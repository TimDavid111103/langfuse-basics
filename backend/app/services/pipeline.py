import asyncio
import json
from datetime import datetime

from langfuse import Langfuse, get_client, observe
from openai import OpenAI

from app.config import settings

Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_base_url,
)
from app.judging.aggregation import aggregate_results, run_winner
from app.judging.events import (
    EventBus,
    ExperimentCompleted,
    ExperimentFailed,
    ExperimentStarted,
    QuestionEvaluated,
    RunCompleted,
    RunStarted,
    get_event_bus,
)
from app.judging.judge import evaluate_rubrics
from app.models.experiment import Experiment, ExperimentResult, ExperimentStatus
from app.services.dataset.versioning import get_version_questions
from app.services.retrieval.retriever import retrieve_chunks
from app.services.rubric_generation.no_rag import generate_rubric_no_rag
from app.services.rubric_generation.rag import generate_rubric_rag

TOP_K_RETRIEVAL = 5


@observe(name="experiment_pipeline")
async def run_experiment_pipeline(
    experiment_id: int,
    num_runs: int,
    *,
    event_bus: EventBus | None = None,
) -> None:
    """Execute the full RAG-vs-no-RAG pipeline for an experiment."""
    from app.database import AsyncSessionLocal
    from sqlmodel import select

    bus = event_bus or get_event_bus()
    client = OpenAI(api_key=settings.openai_api_key)

    async with AsyncSessionLocal() as session:
        exp_result = await session.exec(
            select(Experiment).where(Experiment.id == experiment_id)
        )
        experiment = exp_result.one()

        experiment.status = ExperimentStatus.RUNNING
        experiment.langfuse_trace_id = get_client().get_current_trace_id()
        get_client().update_current_span(
            metadata={
                "experiment_id": experiment_id,
                "experiment_name": experiment.name,
                "questionnaire_id": experiment.questionnaire_id,
                "source_material_id": experiment.source_material_id,
                "num_runs": num_runs,
            }
        )
        session.add(experiment)
        await session.commit()

        bus.emit(
            ExperimentStarted(
                experiment_id=experiment_id,
                experiment_name=experiment.name,
                questionnaire_id=experiment.questionnaire_id,
                source_material_id=experiment.source_material_id,
                num_runs=num_runs,
            )
        )

        try:
            questions = await get_version_questions(
                experiment.questionnaire_id,
                experiment.questionnaire_version,
                session,
            )

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

            all_runs: list[list] = []
            for run_idx in range(num_runs):
                bus.emit(RunStarted(experiment_id=experiment_id, run_index=run_idx))

                rubrics_no_rag = await asyncio.gather(
                    *[asyncio.to_thread(generate_rubric_no_rag, q, client) for q in questions]
                )
                rubrics_rag = await asyncio.gather(
                    *[
                        asyncio.to_thread(generate_rubric_rag, q, chunks, client)
                        for q, chunks in zip(questions, retrieved_per_question, strict=True)
                    ]
                )
                run_results = await asyncio.gather(
                    *[
                        asyncio.to_thread(evaluate_rubrics, q, no_rag, rag, chunks, client, run_idx)
                        for q, no_rag, rag, chunks in zip(
                            questions, rubrics_no_rag, rubrics_rag, retrieved_per_question, strict=True
                        )
                    ]
                )
                run_results = list(run_results)

                for q, no_rag, rag, chunks, result in zip(
                    questions, rubrics_no_rag, rubrics_rag, retrieved_per_question, run_results, strict=True
                ):
                    bus.emit(
                        QuestionEvaluated(
                            experiment_id=experiment_id,
                            run_index=run_idx,
                            question_index=q.index,
                            winner=result.winner,
                            no_rag_total=result.no_rag_total,
                            rag_total=result.rag_total,
                        )
                    )
                    session.add(ExperimentResult(
                        experiment_id=experiment_id,
                        run_index=run_idx,
                        question_index=q.index,
                        question_text=q.text,
                        rubric_no_rag=json.dumps([c.model_dump() for c in no_rag.criteria]),
                        rubric_rag=json.dumps([c.model_dump() for c in rag.criteria]),
                        retrieved_chunks_json=json.dumps([c.model_dump() for c in chunks]),
                        evaluation_json=result.model_dump_json(),
                        winner=result.winner,
                    ))

                no_rag_avg = sum(r.no_rag_total for r in run_results) / len(run_results)
                rag_avg = sum(r.rag_total for r in run_results) / len(run_results)
                bus.emit(
                    RunCompleted(
                        experiment_id=experiment_id,
                        run_index=run_idx,
                        winner=run_winner(no_rag_avg, rag_avg),
                        no_rag_avg=no_rag_avg,
                        rag_avg=rag_avg,
                    )
                )
                all_runs.append(run_results)

            summary = aggregate_results(experiment_id, all_runs)
            get_client().update_current_span(
                output={
                    "overall_winner": summary.overall_winner,
                    "no_rag_score": round(summary.overall_no_rag_score, 2),
                    "rag_score": round(summary.overall_rag_score, 2),
                }
            )

            bus.emit(
                ExperimentCompleted(
                    experiment_id=experiment_id,
                    overall_winner=summary.overall_winner,
                    overall_no_rag_score=summary.overall_no_rag_score,
                    overall_rag_score=summary.overall_rag_score,
                    num_runs=num_runs,
                )
            )

            experiment.status = ExperimentStatus.COMPLETE
            experiment.completed_at = datetime.utcnow()
            session.add(experiment)
            await session.commit()

        except Exception as exc:
            bus.emit(ExperimentFailed(experiment_id=experiment_id, error=str(exc)))
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
