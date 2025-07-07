import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { NextRequest, NextResponse } from "next/server";

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function POST(
  request: NextRequest,
  { params }: { params: { portfolio: string } }
) {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const { name } = await request.json();

  if (!name || !params.portfolio) {
    return NextResponse.json({ error: "Missing name or portfolio" }, { status: 400 });
  }

  const folderKey = `${params.portfolio}/opportunities/${name}/`; // S3 folder

  try {
    await s3.send(
      new PutObjectCommand({
        Bucket,
        Key: folderKey,
        Body: "", // empty file to create folder
      })
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("S3 Create Folder Error:", error);
    return NextResponse.json({ error: "Failed to create opportunity" }, { status: 500 });
  }
}
