# CognOS Proof Engine — Manual Research Execution Mode

This mode is for users who want research output plus a concrete execution plan, without agents or automation flows.

## What You Get
- A current project snapshot (TVV + cycle state)
- Prioritized execution items from backlog
- Definition-of-done criteria per item
- Recent completed outcomes
- A simple human execution loop

## Generate Plan
- Write markdown file:
  - `python3 src/research_execution_plan.py`
- Print to terminal:
  - `python3 src/research_execution_plan.py --stdout`
- Include more execution items:
  - `python3 src/research_execution_plan.py --top 5`

Output directory (default):
- `ops/research/`

## Recommended Usage
1. Generate the plan.
2. Execute item #1 in a focused work block.
3. Validate against definition of done.
4. Update backlog/state manually.
5. Regenerate plan and continue.

This keeps the product usable for teams that prefer manual control over autonomous workflows.
