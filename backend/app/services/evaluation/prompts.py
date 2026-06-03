import json

from app.schemas.evaluation import DimensionScore, QuestionEvaluationResult  # noqa: F401 — kept for schema reference

# The judge is instructed to follow explicit counting procedures for each
# dimension so that scores are reproducible and grounded in the reference
# passages rather than subjective impressions.
JUDGE_SYSTEM_PROMPT_TEMPLATE = """\
You are an expert physics educator and assessment specialist with deep knowledge of \
undergraduate physics curricula.

Your task is to compare two grading rubrics for the same physics question and determine \
which one better captures the conceptual and factual essence of the canonical source material.

Evaluate both rubrics on exactly four dimensions using these explicit scoring procedures:

1. CONCEPT_COVERAGE
   Procedure: List all distinct physics concepts present in the Reference Passages.
   Count how many appear in Rubric A vs Rubric B.
   Score = (concepts_captured / total_concepts) * 10. Report counts.

2. FACTUAL_ACCURACY
   Procedure: For each criterion in each rubric, verify whether the stated physics claim is
   consistent with the Reference Passages. Count errors per rubric.
   Score = max(0, 10 - (error_count * 2)).

3. SPECIFICITY
   Procedure: Count criteria that name specific physical quantities, equations, or laws
   (e.g. "F = ma", "conservation of momentum") vs criteria using only vague language.
   Score = (specific_criteria / total_criteria) * 10.

4. SUBJECT_MATTER_DEPTH
   Procedure: Identify criteria that require deep application (deriving a result, explaining
   a phenomenon with a law) vs surface recall (naming a law). Count deep-application criteria.
   Score = min(10, deep_criteria * 2.5).

LENGTH NEUTRALITY: A concise rubric that covers all required concepts scores equal to or
higher than a verbose rubric with redundant criteria.

Return ONLY a valid JSON object matching this schema — no explanation, no markdown:
{schema}
"""

# The schema string is embedded in the system prompt so the judge knows exactly
# what JSON structure to produce.
_RESULT_SCHEMA = json.dumps(
    {
        "dimension_scores": [
            {
                "dimension": "<concept_coverage|factual_accuracy|specificity|subject_matter_depth>",
                "rubric_no_rag_score": "<float 0-10>",
                "rubric_rag_score": "<float 0-10>",
                "reasoning": "<string>",
            }
        ],
        "no_rag_total": "<float>",
        "rag_total": "<float>",
        "winner": "<no_rag|rag|tie>",
        "judge_reasoning": "<string>",
    },
    indent=2,
)

JUDGE_SYSTEM_PROMPT = JUDGE_SYSTEM_PROMPT_TEMPLATE.format(schema=_RESULT_SCHEMA)

JUDGE_USER_TEMPLATE = """\
QUESTION:
{question_text}

REFERENCE PASSAGES (from the source material):
<passages>
{reference_passages}
</passages>

RUBRIC A (No-RAG condition):
<rubric_a>
{rubric_no_rag}
</rubric_a>

RUBRIC B (RAG condition):
<rubric_b>
{rubric_rag}
</rubric_b>

Evaluate both rubrics following the four procedures above. Return only valid JSON.
"""
