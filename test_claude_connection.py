# test_claude_connection.py

from rag.llm_client_claude import invoke_claude

test_prompt = "Say hello and tell me what year it is."

try:
    print("🧠 Sending test prompt to Claude...")
    response = invoke_claude(test_prompt)
    print("✅ Response from Claude:\n", response.strip())
except Exception as e:
    print("❌ Claude connection failed:", e)
