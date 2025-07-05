import { NextResponse } from "next/server";
import AnthropicBedrock from "@anthropic-ai/bedrock-sdk";


export async function POST() {
  try {
    const client = new AnthropicBedrock(); // picks up env vars automatically

    const message = await client.messages.create({
      model: "anthropic.claude-3-sonnet-20240229-v1:0",
      max_tokens: 256,
      messages: [
        {
          role: "user",
          content: "Hello Claude 3.5 Sonnet, explain yourself in one sentence.",
        },
      ],
    });

    return NextResponse.json({ response: message });
  } catch (error) {
    console.error("Anthropic Bedrock error:", error);
    return NextResponse.json({ error: "Failed to call Claude via Bedrock SDK" }, { status: 500 });
  }
}

export async function GET() {
  return POST(); // For browser testing
}
