"""Basic example of using CognOS SDK."""

from cognos import CognosClient


def main():
    """Basic chat example."""
    # Create client (assumes CognOS running on localhost:8788)
    client = CognosClient()

    # Check if gateway is healthy
    health = client.healthz()
    print(f"Gateway status: {health['status']}")

    # Simple chat request
    print("\n🔵 Calling LLM through CognOS...")
    response = client.chat(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "What is 2+2?"}],
        mode="monitor",
    )

    # Check response
    print(f"\n✅ Response received")
    print(f"   Content: {response.choices[0].message['content']}")
    print(f"   Decision: {response.cognos.decision}")
    print(f"   Risk: {response.cognos.risk}")
    print(f"   Trace ID: {response.cognos.trace_id}")

    # Retrieve full trace
    print(f"\n📋 Retrieving trace record...")
    trace = client.get_trace(response.cognos.trace_id)
    print(f"   Model: {trace['model']}")
    print(f"   Policy: {trace['policy']}")
    print(f"   Trust Score: {trace['trust_score']}")

    # Generate compliance report
    print(f"\n📊 Creating compliance report...")
    report = client.create_trust_report(
        trace_ids=[response.cognos.trace_id],
        regime="EU_AI_ACT",
    )
    print(f"   Report ID: {report['report_id']}")
    print(f"   Found: {report['summary']['found_count']} trace(s)")
    print(f"   Decisions: {report['summary']['decision_breakdown']}")

    # Cleanup
    client.close()
    print("\n✨ Done!")


if __name__ == "__main__":
    main()
