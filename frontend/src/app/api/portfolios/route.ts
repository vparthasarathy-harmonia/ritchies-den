import { S3Client, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { NextResponse } from "next/server";

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function GET() {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const Prefix = "";
  const result = await s3.send(
    new ListObjectsV2Command({
      Bucket,
      Prefix,
      Delimiter: "/",
    })
  );

  const folders = (result.CommonPrefixes || []).map((p) =>
    p.Prefix?.replace(Prefix, "").replace(/\/$/, "")
  );

  return NextResponse.json(folders);
}
