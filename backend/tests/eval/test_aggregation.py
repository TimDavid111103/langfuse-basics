import pytest

from app.eval.aggregation import aggregate_results, run_winner


class TestRunWinner:
    def test_rag_wins(self) -> None:
        assert run_winner(30.0, 35.0) == "rag"

    def test_no_rag_wins(self) -> None:
        assert run_winner(35.0, 30.0) == "no_rag"

    def test_tie(self) -> None:
        assert run_winner(32.0, 32.0) == "tie"


class TestAggregateResults:
    def test_overall_winner_and_scores(self, sample_runs: list) -> None:
        summary = aggregate_results(experiment_id=1, runs=sample_runs)

        assert summary.experiment_id == 1
        assert summary.num_runs == 2
        assert summary.overall_winner == "rag"
        assert summary.overall_no_rag_score == pytest.approx(27.0)
        assert summary.overall_rag_score == pytest.approx(31.0)

    def test_run_summaries(self, sample_runs: list) -> None:
        summary = aggregate_results(experiment_id=1, runs=sample_runs)

        assert len(summary.runs) == 2
        assert all(run.winner == "rag" for run in summary.runs)
        assert summary.runs[0].no_rag_avg == pytest.approx(27.0)
        assert summary.runs[0].rag_avg == pytest.approx(31.0)

    def test_dimension_averages(self, sample_runs: list) -> None:
        summary = aggregate_results(experiment_id=1, runs=sample_runs)

        for dim in ("concept_coverage", "factual_accuracy", "specificity", "subject_matter_depth"):
            assert dim in summary.dimension_averages
            assert summary.dimension_averages[dim]["no_rag"] == pytest.approx(6.75)
            assert summary.dimension_averages[dim]["rag"] == pytest.approx(7.75)

    def test_judge_summary_mentions_runs(self, sample_runs: list) -> None:
        summary = aggregate_results(experiment_id=1, runs=sample_runs)

        assert "2 run(s)" in summary.judge_summary
        assert "RAG: 2" in summary.judge_summary

    def test_single_run(self) -> None:
        from tests.conftest import make_question_result

        runs = [[make_question_result(no_rag_total=20.0, rag_total=20.0, winner="tie")]]
        summary = aggregate_results(experiment_id=42, runs=runs)

        assert summary.num_runs == 1
        assert summary.overall_winner == "tie"
        assert "Tie: 1" in summary.judge_summary
