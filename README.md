# SPARC: Scenario Planning and Reasoning for Automated C Unit Test Generation

Automated unit test generation for C remains a formidable challenge due to the semantic gap between high-level program intent and the rigid syntactic constraints of pointer arithmetic and manual memory management. While Large Language Models (LLMs) exhibit strong generative capabilities, direct intent-to-code synthesis frequently suffers from the *leap-to-code* failure mode, where models prematurely emit code without grounding in program structure, constraints, and semantics, producing non-compilable tests, hallucinated function signatures, low branch coverage, and semantically irrelevant assertions.

SPARC is a neuro-symbolic, scenario-based framework comprising four stages: (1) Control Flow Graph (CFG) analysis, (2) an Operation Map that grounds LLM reasoning in validated utility helpers, (3) path-targeted test synthesis, and (4) an iterative, self-correction validation loop using compiler and runtime feedback to surface C-specific failures such as memory ownership violations, address truncation, and allocator misuse.

Evaluated on 59 C subjects, SPARC outperforms a vanilla DeepSeek prompting baseline by **31.36% in line coverage**, **26.01% in branch coverage**, and **20.78% in mutation score**, while matching or exceeding KLEE on complex subjects. The framework retains 94.3% of tests through iterative repair and produces tests with significantly higher developer-rated readability and maintainability.

## Repository Structure

| Folder | Description |
|---|---|
| [`sparc-c-test-generator/`](sparc-c-test-generator/README.md) | Main tool — setup instructions, pipeline scripts, and all source code. See its README for installation and usage. |
| [`subjects/`](subjects/) | C source files used as test subjects (algorithm implementations from TheAlgorithms/C). |
| [`survey/`](survey/README.md) | Link to the user feedback survey. |
