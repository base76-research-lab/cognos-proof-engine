from __future__ import annotations

from ops.integrations.crewai.tool import CognosVerify


if __name__ == "__main__":
    tool = CognosVerify()
    print(tool.run(prompt="What is DPIA?", draft_answer="A DPIA is optional in all cases."))
