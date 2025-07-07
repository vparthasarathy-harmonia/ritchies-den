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
  const contentType = req.headers.get("content-type") || "";
  const formData = await req.formData();

  const prefix = formData.get("prefix") as string;
  const file = formData.get("file") as File;

  if (!prefix || !file || !(file instanceof File)) {
    return NextResponse.json({ error: "Missing prefix or file" }, { status: 400 });
  }

  const arrayBuffer = await file.arrayBuffer();

  try {
    await s3.send(
      new PutObjectCommand({
        Bucket: process.env.S3_BUCKET_NAME!,
        Key: `${prefix}${file.name}`,
        Body: Buffer.from(arrayBuffer),
        ContentType: file.type,
      })
    );

    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Upload failed:", err);
    return NextResponse.json({ error: "Upload failed" }, { status: 500 });
  }
}
