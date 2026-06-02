import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from langfuse import get_client, observe
from openai import OpenAI
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.config import settings
from app.database import get_session
from app.models.experiment import Experiment, ExperimentResult, ExperimentStatus
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentRead,
    ExperimentResultRead,
    ExperimentRunResponse,
)
from app.services.dataset.versioning import get_version_questions
from app.services.evaluation.judge import aggregate_results, evaluate_rubrics
from app.services.retrieval.retriever import retrieve_chunks
from app.services.rubric_generation.no_rag import generate_rubric_no_rag
from app.services.rubric_generation.rag import generate_rubric_rag

router = APIRouter()

TOP_K_RETRIEVAL = 5


@observe(name="experiment_run")
async def _run_experiment_pipeline(experiment_id: int, num_runs: int) -> None:
    from app.database import AsyncSessionLocal

    client = OpenAI(api_key=settings.openai_api_key)

    async with AsyncSessionLocal() as session:
        exp_result = await session.exec(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = exp_result.one()
        lf = get_client()
        experiment.status = ExperimentStatus.RUNNING
        experiment.langfuse_trace_id = lf.get_current_trace_id()
        session.add(experiment)
        await session.commit()

        try:
            questions = await get_version_questions(
                experiment.questionnaire_id,
                experiment.questionnaire_version,
                session,
            )

            lf.update_current_span(
                metadata={
                    "experiment_id": experiment_id,
                    "questionnaire_id": experiment.questionnaire_id,
                    "source_material_id": experiment.source_material_id,
                    "question_count": len(questions),
                    "num_runs": num_runs,
                },
            )

            # Retrieve chunks once — deterministic, no need to repeat per run
            retrieved_per_question = await asyncio.gather(
                *[
                    retrieve_chunks(
                        query=q.text,
                        source_material_id=experiment.source_material_id,
                        top_k=TOP_K_RETRIEVAL,
                        session=session,
                    )
                    for q in questions
                ]
            )

            # Each run generates fresh rubrics (stochastic) and a fresh judge call
            all_runs: list[list] = []
            for run_idx in range(num_runs):
                rubrics_no_rag = [generate_rubric_no_rag(q, client) for q in questions]
                rubrics_rag = [
                    generate_rubric_rag(q, chunks, client)
                    for q, chunks in zip(questions, retrieved_per_question, strict=True)
                ]

                run_results = []
                for q, no_rag, rag, chunks in zip(
                    questions, rubrics_no_rag, rubrics_rag, retrieved_per_question, strict=True
                ):
                    result = evaluate_rubrics(q, no_rag, rag, chunks, client, run_idx)
                    run_results.append(result)

                    db_result = ExperimentResult(
                        experiment_id=experiment_id,
                        run_index=run_idx,
                        question_index=q.index,
                        question_text=q.text,
                        rubric_no_rag=json.dumps([c.model_dump() for c in no_rag.criteria]),
                        rubric_rag=json.dumps([c.model_dump() for c in rag.criteria]),
                        retrieved_chunks_json=json.dumps([c.model_dump() for c in chunks]),
                        evaluation_json=result.model_dump_json(),
                        winner=result.winner,
                    )
                    session.add(db_result)

                all_runs.append(run_results)

            summary = aggregate_results(experiment_id, all_runs)

            lf.set_current_trace_io(
                output={
                    "overall_winner": summary.overall_winner,
                    "no_rag_score": summary.overall_no_rag_score,
                    "rag_score": summary.overall_rag_score,
                    "num_runs": num_runs,
                }
            )

            experiment.status = ExperimentStatus.COMPLETE
            experiment.completed_at = datetime.utcnow()
            session.add(experiment)
            await session.commit()

        except Exception as exc:
            await session.rollback()
            async with AsyncSessionLocal() as err_session:
                err_result = await err_session.exec(
                    select(Experiment).where(Experiment.id == experiment_id)
                )
                exp = err_result.one()
                exp.status = ExperimentStatus.FAILED
                exp.error_message = str(exc)
                err_session.add(exp)
                await err_session.commit()
            raise


@router.post("/experiments", response_model=ExperimentRead, status_code=201)
async def create_experiment(
    payload: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
) -> ExperimentRead:
    experiment = Experiment(
        name=payload.name,
        questionnaire_id=payload.questionnaire_id,
        questionnaire_version=payload.questionnaire_version,
        source_material_id=payload.source_material_id,
        status=ExperimentStatus.CREATED,
    )
    session.add(experiment)
    await session.commit()
    await session.refresh(experiment)
    return ExperimentRead(
        id=experiment.id,
        name=experiment.name,
        questionnaire_id=experiment.questionnaire_id,
        questionnaire_version=experiment.questionnaire_version,
        source_material_id=experiment.source_material_id,
        status=experiment.status,
        langfuse_trace_id=experiment.langfuse_trace_id,
        error_message=experiment.error_message,
        created_at=experiment.created_at,
        completed_at=experiment.completed_at,
    )


@router.get("/experiments", response_model=list[ExperimentRead])
async def list_experiments(
    session: AsyncSession = Depends(get_session),
) -> list[ExperimentRead]:
    result = await session.exec(select(Experiment))
    return [
        ExperimentRead(
            id=e.id,
            name=e.name,
            questionnaire_id=e.questionnaire_id,
            questionnaire_version=e.questionnaire_version,
            source_material_id=e.source_material_id,
            status=e.status,
            langfuse_trace_id=e.langfuse_trace_id,
            error_message=e.error_message,
            created_at=e.created_at,
            completed_at=e.completed_at,
        )
        for e in result.all()
    ]


@router.get("/experiments/{experiment_id}", response_model=ExperimentRead)
async def get_experiment(
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
) -> ExperimentRead:
    result = await session.exec(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    e = result.first()
    if e is None:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return ExperimentRead(
        id=e.id,
        name=e.name,
        questionnaire_id=e.questionnaire_id,
        questionnaire_version=e.questionnaire_version,
        source_material_id=e.source_material_id,
        status=e.status,
        langfuse_trace_id=e.langfuse_trace_id,
        error_message=e.error_message,
        created_at=e.created_at,
        completed_at=e.completed_at,
    )


@router.post("/experiments/{experiment_id}/run", response_model=ExperimentRunResponse)
async def run_experiment(
    experiment_id: int,
    background_tasks: BackgroundTasks,
    num_runs: int = Query(default=1, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
) -> ExperimentRunResponse:
    result = await session.exec(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    e = result.first()
    if e is None:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    if e.status == ExperimentStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Experiment is already running.")

    background_tasks.add_task(_run_experiment_pipeline, experiment_id, num_runs)

    return ExperimentRunResponse(
        experiment_id=experiment_id,
        status=ExperimentStatus.RUNNING,
        message=f"Experiment started with {num_runs} run(s). Poll GET /experiments/{{id}} for status.",
    )


@router.get("/experiments/{experiment_id}/results", response_model=list[ExperimentResultRead])
async def get_experiment_results(
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
) -> list[ExperimentResultRead]:
    result = await session.exec(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.run_index, ExperimentResult.question_index)
    )
    rows = result.all()
    return [
        ExperimentResultRead(
            id=r.id,
            experiment_id=r.experiment_id,
            run_index=r.run_index,
            question_index=r.question_index,
            question_text=r.question_text,
            rubric_no_rag=r.rubric_no_rag,
            rubric_rag=r.rubric_rag,
            retrieved_chunks_json=r.retrieved_chunks_json,
            evaluation_json=r.evaluation_json,
            winner=r.winner,
            created_at=r.created_at,
        )
        for r in rows
    ]
