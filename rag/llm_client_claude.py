# ritchies-den/rag/llm_client.py

import os
import json
import boto3
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.local")

bedrock_runtime = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.getenv("BEDROCK_REGION"),
    aws_access_key_id=os.getenv("BEDROCK_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("BEDROCK_SECRET_ACCESS_KEY")
)

MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"

def invoke_claude(prompt: str, temperature: float = 0.0, max_tokens: int = 1000) -> str:
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}]
    }

    response = bedrock_runtime.invoke_model(
        modelId=MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    response_body = json.loads(response["body"].read())
    return response_body["content"][0]["text"]
