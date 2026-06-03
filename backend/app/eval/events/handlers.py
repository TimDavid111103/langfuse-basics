"""Default event handlers for pipeline observability."""

import logging

from app.eval.events.bus import EventBus
from app.eval.events.types import (
    ExperimentCompleted,
    ExperimentFailed,
    ExperimentStarted,
    QuestionEvaluated,
    RunCompleted,
    RunStarted,
)

logger = logging.getLogger(__name__)


def log_experiment_started(event: ExperimentStarted) -> None:
    logger.info(
        "Experiment started: id=%s name=%r runs=%s",
        event.experiment_id,
        event.experiment_name,
        event.num_runs,
    )


def log_run_started(event: RunStarted) -> None:
    logger.info("Run started: experiment=%s run=%s", event.experiment_id, event.run_index)


def log_question_evaluated(event: QuestionEvaluated) -> None:
    logger.debug(
        "Question evaluated: experiment=%s run=%s q=%s winner=%s",
        event.experiment_id,
        event.run_index,
        event.question_index,
        event.winner,
    )


def log_run_completed(event: RunCompleted) -> None:
    logger.info(
        "Run completed: experiment=%s run=%s winner=%s no_rag=%.2f rag=%.2f",
        event.experiment_id,
        event.run_index,
        event.winner,
        event.no_rag_avg,
        event.rag_avg,
    )


def log_experiment_completed(event: ExperimentCompleted) -> None:
    logger.info(
        "Experiment completed: id=%s winner=%s no_rag=%.2f rag=%.2f",
        event.experiment_id,
        event.overall_winner,
        event.overall_no_rag_score,
        event.overall_rag_score,
    )


def log_experiment_failed(event: ExperimentFailed) -> None:
    logger.error("Experiment failed: id=%s error=%s", event.experiment_id, event.error)


def register_default_handlers(bus: EventBus) -> None:
    """Wire logging handlers onto an event bus."""
    bus.subscribe(ExperimentStarted, log_experiment_started)
    bus.subscribe(RunStarted, log_run_started)
    bus.subscribe(QuestionEvaluated, log_question_evaluated)
    bus.subscribe(RunCompleted, log_run_completed)
    bus.subscribe(ExperimentCompleted, log_experiment_completed)
    bus.subscribe(ExperimentFailed, log_experiment_failed)
