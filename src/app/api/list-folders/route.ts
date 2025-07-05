import { S3Client, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { NextRequest, NextResponse } from "next/server";

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function GET(req: NextRequest) {
  const bucket = process.env.S3_BUCKET!;
  const prefix = ""; // top-level

  try {
    const command = new ListObjectsV2Command({
      Bucket: bucket,
      Delimiter: "/",
      Prefix: prefix,
    });

    const response = await s3.send(command);
    const folders = (response.CommonPrefixes || []).map((p) => p.Prefix);

    return NextResponse.json({ folders });
  } catch (err) {
    console.error("Error listing folders:", err);
    return NextResponse.json({ error: "Failed to list folders" }, { status: 500 });
  }
}
