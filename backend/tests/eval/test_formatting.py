from app.eval.formatting import format_chunks_for_rubric, format_passages_for_judge, format_rubric
from app.schemas.retrieval import RetrievedChunk
from app.schemas.rubric import GeneratedRubric, RubricCriterion


def _sample_chunk(**overrides: object) -> RetrievedChunk:
    defaults = {
        "chunk_id": 1,
        "source_material_id": 1,
        "chunk_index": 0,
        "page_number": 5,
        "section_title": "Bernoulli's Equation",
        "text": "Fluid speed increases as pressure decreases.",
        "context": "This section introduces Bernoulli's principle.",
        "cosine_distance": 0.12,
    }
    defaults.update(overrides)
    return RetrievedChunk(**defaults)  # type: ignore[arg-type]


def _sample_rubric() -> GeneratedRubric:
    return GeneratedRubric(
        question_index=0,
        question_text="State Bernoulli's equation.",
        criteria=[
            RubricCriterion(
                criterion_name="States equation",
                description="Student writes Bernoulli's equation correctly.",
                point_value=5,
                example_correct_response="P + ½ρv² + ρgh = constant",
                example_incorrect_response="F = ma",
                physics_concepts_required=["Bernoulli's equation"],
            )
        ],
        total_points=5,
        condition="rag",
        model_id="gpt-4o-mini",
        prompt_tokens=100,
        completion_tokens=50,
    )


class TestFormatRubric:
    def test_includes_criterion_details(self) -> None:
        text = format_rubric(_sample_rubric())

        assert "States equation (5 pts)" in text
        assert "P + ½ρv² + ρgh = constant" in text
        assert "F = ma" in text


class TestFormatChunksForRubric:
    def test_includes_passage_header_and_page(self) -> None:
        text = format_chunks_for_rubric([_sample_chunk()])

        assert "[Passage 1 — Bernoulli's Equation, p.5]" in text
        assert "Context: This section introduces Bernoulli's principle." in text
        assert "Fluid speed increases" in text

    def test_multiple_chunks(self) -> None:
        chunks = [
            _sample_chunk(chunk_index=0),
            _sample_chunk(chunk_index=1, section_title="Torricelli's Rule", page_number=6),
        ]
        text = format_chunks_for_rubric(chunks)

        assert "[Passage 1" in text
        assert "[Passage 2 — Torricelli's Rule, p.6]" in text


class TestFormatPassagesForJudge:
    def test_judge_style_differs_from_rubric_style(self) -> None:
        chunk = _sample_chunk()
        rubric_fmt = format_chunks_for_rubric([chunk])
        judge_fmt = format_passages_for_judge([chunk])

        assert "[Passage 1" in rubric_fmt
        assert "[1 — Bernoulli's Equation]" in judge_fmt
        assert "p.5" not in judge_fmt

    def test_empty_context_omitted(self) -> None:
        chunk = _sample_chunk(context=None)
        text = format_passages_for_judge([chunk])

        assert "Context:" not in text
        assert "Fluid speed increases" in text
