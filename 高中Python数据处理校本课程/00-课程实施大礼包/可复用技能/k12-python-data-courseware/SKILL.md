---
name: k12-python-data-courseware
description: Create or extend a high-school Python and data-processing school-based course, including curriculum blueprints, 5×45-minute unit resources, offline code, formative autograders, data-quality graders, capstone tasks, pilot-teaching scripts, anonymous quizzes, class-level analysis, and school-report presentations with speaker scripts. Use when designing, piloting, evaluating, or iterating K12 Python data-literacy courseware.
---

# K12 Python Data Courseware

Create classroom-ready high-school Python and data-processing courseware, then validate it through a narrow, evidence-based pilot. Read [references/courseware-blueprints.md](references/courseware-blueprints.md) for curriculum and unit design. Read [references/pilot-validation.md](references/pilot-validation.md) when preparing a pilot, capstone task, quiz, pilot report, speaker script, or post-pilot decision. Read [references/advanced-data-units.md](references/advanced-data-units.md) when designing U4—U6 CSV/data-quality units, chart-expression units, micro-projects, constrained validation, or a school-level course presentation.

## Workflow

1. **Inspect before expanding.** Identify the blueprint, learner group, course hours, completed units, offline constraints, and data-safety boundary. Choose one implementation risk; do not expand several units at once.
2. **Align the unit.** Define observable objectives, a driving problem, a runnable product, a knowledge representation, a reflection, and formative checks. Organize learning as problem → data → program → result → explanation and boundary.
3. **Create core and capstone resources.** Write the teacher guide and student worksheet first. Add starter/reference Python code, rubrics, debugging support, and a small end-of-unit capstone. The capstone must use a precise low-risk data scenario, require a runnable product, include ordinary/boundary/combined tests, and end with an evidence-and-boundary statement.
4. **For list/dictionary cleaning units, preserve provenance.** Separate a single-value cleaning function from batch transformation. Keep original records unchanged. Return valid records and an issue log that retains record ID, raw value, and reason. Require valid count, issue count, total, average, and the rule denominator in any summary.
5. **For CSV units, build the standard-library path first.** Use `csv.DictReader` or an equivalent field-based reader before optional `pandas`. Teach path checks, field names, string-to-number conversion, missing values, duplicate keys, filters, group summaries, and data dictionaries. Never overwrite the raw file; write cleaned outputs separately.
6. **Add formative automation only when appropriate.** Use local function-level autograding for narrow skills. For a data-quality project, test single-value cleaning, batch routing, issue-log fields, raw-data preservation, summary schema and one approved input-change response. Report dimension-level diagnostics, not only a score. State that the runner is not a security sandbox, use it only for trusted classroom code, and never turn its result into a personal ranking.
7. **Prepare the pilot.** For a 5×45-minute unit, write a minute-accurate teacher script with key prompts, student actions, checks, and adjustment rules. For chart units, prepare code and prebuilt-chart paths that share one chart contract. For micro-projects, freeze a small scope, assign roles, use staged checkpoints and require one evidence-based P0 revision. Add an environment preflight that verifies local resources, input files, reference code, and analysis scripts.
8. **Measure without labeling students.** Create an 8—12 item anonymous formative quiz. Cover program behavior, boundaries, tracing, debugging, data structure, CSV/data-quality reasoning, and responsibility. Never collect identity or sensitive data; never create rankings or high-risk decisions.
9. **Analyze at class level.** Use `scripts/analyze_anonymous_quiz.py` with a config copied from `templates/anonymous_quiz_config_template.json`. Combine question-level results with observations and product completion; select only one P0 resource improvement.
10. **Communicate the decision.** Use a 10-page structure for a pilot review: current assets and gap, course purpose, reason for a narrow pilot, scope, lesson flow, teacher readiness, evaluation, anonymous evidence, and a single next decision. When the outline exists, write a matching page-by-page speaker script that explains the rationale rather than reading slide text.
11. **Validate and deliver.** Run Python examples, preflights, autograders, and analysis scripts on empty templates or authorized data. Verify lesson-minute arithmetic, resource paths, privacy statements, absence of individual-score outputs, schema expectations, and outline/script page alignment.

## Non-negotiable safeguards

- Use only teaching-simulation, public, authorized, or de-identified data.
- Do not collect student names, IDs, grades, health, precise location, family information, or other sensitive data for classroom analytics.
- Do not infer student ability, conduct, health, or future outcomes from a small capstone dataset or a quiz.
- State that local Python autograders and data-quality graders are not security sandboxes; run only trusted classroom code in controlled environments.
- Treat lower quiz accuracy as evidence to examine task design, explanation, time, and resource scaffolds—not as a reason to label students.
- Keep raw data immutable and document every cleaning rule, exclusion, issue reason, and denominator.
- After a first pilot, make one focused P0 change before developing further units.

## Reference resources

- [references/courseware-blueprints.md](references/courseware-blueprints.md): 30-hour map, unit requirements, autograder constraints, and general quality checks.
- [references/pilot-validation.md](references/pilot-validation.md): pilot scope, minute scripts, capstones, anonymous quizzes, evidence interpretation, 10-page report structure, and speaker scripts.
- [references/advanced-data-units.md](references/advanced-data-units.md): U4 CSV/data-quality rules, U5 chart contract and dual path, U6 six-limit micro-project, controlled validator boundary, and school-presentation story.
- `scripts/analyze_anonymous_quiz.py`: configurable class-level multiple-choice summary; does not output individual scores.
- `templates/anonymous_quiz_config_template.json`: required configuration shape for the analysis script.
