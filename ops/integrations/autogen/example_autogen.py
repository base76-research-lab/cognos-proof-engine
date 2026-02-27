from __future__ import annotations

import json

from ops.integrations.autogen.tool import cognos_verify


if __name__ == "__main__":
    output = cognos_verify(
        prompt="Summarize lawful basis under GDPR.",
        draft_answer="There is only consent.",
    )
    print(json.dumps(output, indent=2))
