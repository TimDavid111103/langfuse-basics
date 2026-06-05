# Langfuse basics

A learning project where I taught myself **LLM evaluation and observability** — something I hadn't done before — by applying it to a real problem: generating exam **grading rubrics** from lecture notes, and measuring whether grounding the model in the source material (RAG) actually beats relying on its own knowledge (no-RAG).

## What I learned

- **Evals turn "is the output good?" into a number.** Instead of eyeballing model responses, I built an explicit LLM judge that scores both rubrics against the reference passages across four dimensions — concept coverage, factual accuracy, specificity, and subject-matter depth — and declares a winner.

- **Run experiments, not one-offs.** LLM output is noisy, so a single comparison proves nothing. Running each experiment over multiple independent runs and averaging the scores turns "RAG is better" from a vibe into a measurable, repeatable result.

- **Langfuse for tracing and observability.** Every stage of the pipeline is instrumented with the `@observe` decorator, so one experiment shows up as a single trace with nested spans for retrieval, both rubric generators, and the judge. I learned to capture model inputs/outputs and token usage on generation spans, attach experiment metadata to the root trace, set the trace output to the final winner/scores, and flush before the process exits so nothing is lost.

- **RAG vs. no-RAG as a controlled comparison.** The same questions run through two conditions — one writing rubrics from prior knowledge, one grounded in passages retrieved from the chunked-and-embedded PDF — which is what makes the eval a fair, apples-to-apples test of whether retrieval helps.

- **Test the deterministic core, not the model.** The LLM calls aren't reproducible, but the scoring, winner logic, and aggregation around them are pure functions — so those are exactly the parts worth covering with unit tests (ties, single vs. multi-run, dimension averaging).
