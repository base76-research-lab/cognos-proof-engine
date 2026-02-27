from __future__ import annotations

from ops.integrations.langchain.tool import CognosVerifyTool


if __name__ == "__main__":
    tool = CognosVerifyTool()
    output = tool._run(
        prompt="Give a short explanation of GDPR lawful bases.",
        draft_answer="GDPR has only one lawful basis: consent.",
    )
    print(output)
