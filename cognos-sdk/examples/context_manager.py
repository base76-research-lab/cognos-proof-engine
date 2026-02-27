"""Using CognOS SDK with context manager (recommended)."""

from cognos import CognosClient


def main():
    """Context manager example."""
    # Using 'with' automatically closes connection
    with CognosClient() as client:
        response = client.chat(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Tell me about AI safety in 2 sentences."}
            ],
            mode="monitor",
            temperature=0.7,
        )

        print(f"Decision: {response.cognos.decision}")
        print(f"Content: {response.choices[0].message['content']}")

        if response.cognos.decision == "PASS":
            print("✅ Response passed trust verification")
        else:
            print(f"⚠️ Risk flagged: {response.cognos.risk}")


if __name__ == "__main__":
    main()
