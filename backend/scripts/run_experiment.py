"""
Create and run an experiment.

Usage:
    uv run python scripts/run_experiment.py \\
        --questionnaire "Chapter 8 — Fluids" \\
        --material "Chapter 8 - Fluids" \\
        --name "Fluids eval run 1" \\
        --runs 3

Arguments:
    --questionnaire   Name of the questionnaire (must exist in DB)
    --material        Name of the source material (must be ingested and complete)
    --name            Label for this experiment
    --runs            Number of independent runs (default: 1, max: 20)

Run from the backend/ directory.
"""
import argparse
import asyncio
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

from langfuse import get_client

from app.database import AsyncSessionLocal, create_db_and_tables
from app.models.experiment import Experiment, ExperimentResult, ExperimentStatus
from app.models.questionnaire import Questionnaire
from app.models.source_material import IngestionStatus, SourceMaterial
from app.judging import QuestionEvaluationResult, aggregate_results
from app.services.pipeline import run_experiment_pipeline


async def main(
    questionnaire_name: str,
    material_name: str,
    experiment_name: str,
    num_runs: int,
) -> None:
    """Look up the questionnaire and material, create an experiment, run it, and print results."""
    await create_db_and_tables()

    async with AsyncSessionLocal() as session:
        q_result = await session.exec(
            select(Questionnaire).where(Questionnaire.name == questionnaire_name)
        )
        questionnaire = q_result.first()
        if questionnaire is None:
            print(f"Error: questionnaire '{questionnaire_name}' not found.")
            sys.exit(1)

        m_result = await session.exec(
            select(SourceMaterial).where(SourceMaterial.name == material_name)
        )
        material = m_result.first()
        if material is None:
            print(f"Error: material '{material_name}' not found.")
            sys.exit(1)
        if material.ingestion_status != IngestionStatus.COMPLETE:
            print(f"Error: material '{material_name}' ingestion status is '{material.ingestion_status}' — must be 'complete'.")
            sys.exit(1)

        experiment = Experiment(
            name=experiment_name,
            questionnaire_id=questionnaire.id,
            questionnaire_version=questionnaire.current_version,
            source_material_id=material.id,
            status=ExperimentStatus.CREATED,
        )
        session.add(experiment)
        await session.commit()
        await session.refresh(experiment)

    print(f"experiment     '{experiment_name}'  id={experiment.id}")
    print(f"questionnaire  '{questionnaire_name}'  v{questionnaire.current_version}  ({questionnaire.id})")
    print(f"material       '{material_name}'  ({material.chunk_count} chunks)")
    print(f"runs           {num_runs}")
    print()

    started = datetime.utcnow()
    await run_experiment_pipeline(experiment.id, num_runs)
    elapsed = (datetime.utcnow() - started).total_seconds()

    # Re-open a session to read results; the pipeline closed its own session.
    async with AsyncSessionLocal() as session:
        rows_result = await session.exec(
            select(ExperimentResult)
            .where(ExperimentResult.experiment_id == experiment.id)
            .order_by(ExperimentResult.run_index, ExperimentResult.question_index)
        )
        rows = rows_result.all()

        by_run: dict[int, list[QuestionEvaluationResult]] = defaultdict(list)
        for row in rows:
            by_run[row.run_index].append(
                QuestionEvaluationResult(**json.loads(row.evaluation_json))
            )

        runs = [by_run[i] for i in sorted(by_run.keys())]
        summary = aggregate_results(experiment.id, runs)

    print("=" * 60)
    print(f"RESULTS  (elapsed {elapsed:.0f}s)")
    print("=" * 60)
    print(f"overall winner : {summary.overall_winner.upper()}")
    print(f"no-rag avg     : {summary.overall_no_rag_score:.2f} / 40")
    print(f"rag avg        : {summary.overall_rag_score:.2f} / 40")
    print()

    dims = ["concept_coverage", "factual_accuracy", "specificity", "subject_matter_depth"]
    dim_labels = {
        "concept_coverage": "Concept Coverage",
        "factual_accuracy": "Factual Accuracy",
        "specificity": "Specificity",
        "subject_matter_depth": "Depth",
    }
    print(f"{'dimension':<24}  {'no-rag':>8}  {'rag':>8}")
    print("-" * 44)
    for dim in dims:
        avgs = summary.dimension_averages.get(dim, {})
        print(f"  {dim_labels[dim]:<22}  {avgs.get('no_rag', 0):>8.2f}  {avgs.get('rag', 0):>8.2f}")
    print()

    for run in summary.runs:
        label = f"run {run.run_index + 1}" if num_runs > 1 else "run"
        print(f"{label}  winner={run.winner}  no-rag={run.no_rag_avg:.2f}  rag={run.rag_avg:.2f}")
        for q in run.per_question_results:
            print(f"  Q{q.question_index + 1}  winner={q.winner}  no-rag={q.no_rag_total:.1f}  rag={q.rag_total:.1f}")

    if experiment.langfuse_trace_id:
        print(f"langfuse trace  https://cloud.langfuse.com/trace/{experiment.langfuse_trace_id}")
    get_client().flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create and run a Pensive experiment.")
    parser.add_argument("--questionnaire", required=True, help="Questionnaire name")
    parser.add_argument("--material", required=True, help="Source material name")
    parser.add_argument("--name", required=True, help="Experiment label")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs (default: 1)")
    args = parser.parse_args()

    if not 1 <= args.runs <= 20:
        print("Error: --runs must be between 1 and 20")
        sys.exit(1)

    asyncio.run(main(args.questionnaire, args.material, args.name, args.runs))
