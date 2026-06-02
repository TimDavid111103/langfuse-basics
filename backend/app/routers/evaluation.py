import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.experiment import Experiment, ExperimentResult
from app.schemas.evaluation import ExperimentEvaluationSummary, QuestionEvaluationResult

router = APIRouter()


@router.get("/evaluation/{experiment_id}/summary", response_model=ExperimentEvaluationSummary)
async def get_evaluation_summary(
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
) -> ExperimentEvaluationSummary:
    exp_result = await session.exec(
        select(Experiment).where(Experiment.id == experiment_id)
    )
    experiment = exp_result.first()
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    rows_result = await session.exec(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.run_index, ExperimentResult.question_index)
    )
    rows = rows_result.all()

    if not rows or any(r.evaluation_json is None for r in rows):
        raise HTTPException(
            status_code=404,
            detail="Evaluation not yet complete for this experiment.",
        )

    # Group by run_index, preserving question order within each run
    by_run: dict[int, list[QuestionEvaluationResult]] = defaultdict(list)
    for row in rows:
        by_run[row.run_index].append(
            QuestionEvaluationResult(**json.loads(row.evaluation_json))
        )

    runs = [by_run[i] for i in sorted(by_run.keys())]

    from app.services.evaluation.judge import aggregate_results

    return aggregate_results(experiment_id, runs)
