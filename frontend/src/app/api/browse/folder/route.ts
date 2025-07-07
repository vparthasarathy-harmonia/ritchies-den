import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { NextRequest, NextResponse } from "next/server";

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function POST(req: NextRequest) {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const { prefix, name } = await req.json();

  if (!prefix || !name) {
    return NextResponse.json({ error: "Missing prefix or name" }, { status: 400 });
  }

  const Key = `${prefix}${name}/`; // S3 folder key

  try {
    await s3.send(
      new PutObjectCommand({
        Bucket,
        Key,
        Body: "",
      })
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Create folder error:", error);
    return NextResponse.json({ error: "Failed to create folder" }, { status: 500 });
  }
}
