import asyncio
import json
from datetime import datetime

from langfuse import Langfuse, get_client, observe
from openai import OpenAI

from app.config import settings

# Langfuse reads credentials from os.environ by default, which pydantic-settings
# does not populate. Initialize the singleton explicitly so @observe and get_client()
# use the correct keys from our settings.
Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_base_url,
)
from app.models.experiment import Experiment, ExperimentResult, ExperimentStatus
from app.services.dataset.versioning import get_version_questions
from app.services.evaluation.judge import aggregate_results, evaluate_rubrics
from app.services.retrieval.retriever import retrieve_chunks
from app.services.rubric_generation.no_rag import generate_rubric_no_rag
from app.services.rubric_generation.rag import generate_rubric_rag

TOP_K_RETRIEVAL = 5


@observe(name="experiment_pipeline")
async def run_experiment_pipeline(experiment_id: int, num_runs: int) -> None:
    """Execute the full RAG-vs-no-RAG pipeline for an experiment.

    For each run:
    1. Retrieve source-material chunks once per question (deterministic).
    2. Generate a rubric under the no-RAG condition (model knowledge only).
    3. Generate a rubric under the RAG condition (grounded in retrieved chunks).
    4. Ask the judge model to score both rubrics against the reference passages.
    5. Persist per-question results to the database.
    """
    from app.database import AsyncSessionLocal
    from sqlmodel import select

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

        try:
            questions = await get_version_questions(
                experiment.questionnaire_id,
                experiment.questionnaire_version,
                session,
            )

            # Retrieval is deterministic so we do it once and reuse across runs.
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
                # Both conditions run concurrently within a run; runs are sequential
                # so that each run represents an independent stochastic sample.
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

                all_runs.append(run_results)

            summary = aggregate_results(experiment_id, all_runs)
            get_client().update_current_span(
                output={
                    "overall_winner": summary.overall_winner,
                    "no_rag_score": round(summary.overall_no_rag_score, 2),
                    "rag_score": round(summary.overall_rag_score, 2),
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
