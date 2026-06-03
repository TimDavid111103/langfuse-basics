from app.eval.events import (
    EventBus,
    ExperimentCompleted,
    ExperimentStarted,
    QuestionEvaluated,
    RunCompleted,
    RunStarted,
    reset_event_bus,
)


class TestEventBus:
    def setup_method(self) -> None:
        reset_event_bus()

    def test_subscribe_and_emit(self) -> None:
        bus = EventBus()
        received: list[ExperimentStarted] = []

        bus.subscribe(ExperimentStarted, received.append)
        event = ExperimentStarted(
            experiment_id=1,
            experiment_name="test",
            questionnaire_id=2,
            source_material_id=3,
            num_runs=2,
        )
        bus.emit(event)

        assert received == [event]

    def test_handlers_only_receive_matching_type(self) -> None:
        bus = EventBus()
        started: list[ExperimentStarted] = []
        completed: list[ExperimentCompleted] = []

        bus.subscribe(ExperimentStarted, started.append)
        bus.subscribe(ExperimentCompleted, completed.append)

        bus.emit(ExperimentStarted(1, "test", 2, 3, 1))
        bus.emit(
            ExperimentCompleted(
                experiment_id=1,
                overall_winner="rag",
                overall_no_rag_score=28.0,
                overall_rag_score=32.0,
                num_runs=1,
            )
        )

        assert len(started) == 1
        assert len(completed) == 1

    def test_multiple_handlers_for_same_type(self) -> None:
        bus = EventBus()
        calls: list[str] = []

        bus.subscribe(RunStarted, lambda _: calls.append("a"))
        bus.subscribe(RunStarted, lambda _: calls.append("b"))
        bus.emit(RunStarted(experiment_id=1, run_index=0))

        assert calls == ["a", "b"]

    def test_clear_removes_handlers(self) -> None:
        bus = EventBus()
        received: list[QuestionEvaluated] = []
        bus.subscribe(QuestionEvaluated, received.append)
        bus.clear()
        bus.emit(
            QuestionEvaluated(
                experiment_id=1,
                run_index=0,
                question_index=0,
                winner="tie",
                no_rag_total=30.0,
                rag_total=30.0,
            )
        )

        assert received == []

    def test_run_completed_event_fields(self) -> None:
        event = RunCompleted(
            experiment_id=5,
            run_index=2,
            winner="no_rag",
            no_rag_avg=33.5,
            rag_avg=31.0,
        )

        assert event.experiment_id == 5
        assert event.run_index == 2
        assert event.winner == "no_rag"
