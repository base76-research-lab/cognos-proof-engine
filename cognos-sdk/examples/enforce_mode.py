"""Using enforce mode with policy decisions."""

from cognos import CognosClient


def main():
    """Enforce mode example with policy decisions."""
    client = CognosClient()

    print("Testing enforce mode with different risk thresholds...\n")

    for target_risk in [0.05, 0.15, 0.50]:
        print(f"--- Target Risk: {target_risk} ---")

        response = client.chat(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Generate medical diagnosis"}],
            mode="enforce",
            target_risk=target_risk,
        )

        decision = response.cognos.decision
        risk = response.cognos.risk

        print(f"Decision: {decision}")
        print(f"Risk: {risk:.3f}")

        if decision == "PASS":
            print("→ ✅ Safe to proceed")
        elif decision == "REFINE":
            print("→ ⚠️ Should be refined/reviewed")
        elif decision == "ESCALATE":
            print("→ ⚠️ High risk, escalate to human")
        elif decision == "BLOCK":
            print("→ ❌ Blocked")

        print()

    client.close()


if __name__ == "__main__":
    main()
