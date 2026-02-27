from openai import OpenAI

# Point OpenAI SDK at CognOS Gateway
client = OpenAI(
    base_url="http://127.0.0.1:8788/v1",
    api_key="your-gateway-key-or-placeholder",
)

response = client.chat.completions.create(
    model="openai:gpt-4.1-mini",
    messages=[{"role": "user", "content": "Explain GDPR lawful basis in 3 bullets."}],
)

print(response.choices[0].message.content)
