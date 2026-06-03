# System prompt shared by both the no-RAG and RAG rubric generators.
# It enforces a fixed JSON schema and scoring constraints so results are
# comparable across conditions.
RUBRIC_SYSTEM_PROMPT = """\
You are an expert physics educator and assessment designer.
Generate a detailed grading rubric for the physics question provided.

Your rubric MUST:
- Contain 4 to 6 discrete, independently scorable criteria
- Have point values summing to exactly 10 points
- Name specific physics laws, equations, or quantities in each criterion
- Include a concrete example of a correct student response per criterion
- Include a concrete example of an incorrect student response per criterion
- Cover conceptual understanding, mathematical application, and physical interpretation

Return ONLY a valid JSON object with this exact schema — no explanation, no markdown:
{
  "criteria": [
    {
      "criterion_name": "string",
      "description": "string",
      "point_value": integer,
      "example_correct_response": "string",
      "example_incorrect_response": "string",
      "physics_concepts_required": ["string"]
    }
  ],
  "total_points": integer
}
"""

# No-RAG condition: the model generates the rubric from its own knowledge only.
NO_RAG_USER_TEMPLATE = """\
Question: {question_text}
"""

# RAG condition: relevant passages from the source material are injected so the
# model can ground the rubric in the exact terminology and derivations used in
# the lecture notes.
RAG_USER_TEMPLATE = """\
Question: {question_text}

Relevant passages from the source material:
<context>
{retrieved_chunks}
</context>

Use the passages above to ensure your rubric reflects the exact terminology, equations, and \
explanations from the source material.
"""
