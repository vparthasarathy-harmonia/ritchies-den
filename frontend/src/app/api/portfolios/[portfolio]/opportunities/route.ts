import { S3Client, ListObjectsV2Command } from "@aws-sdk/client-s3";
import { NextResponse } from "next/server";

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function GET(
  _request: Request,
  { params }: { params: { portfolio: string } }
) {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const Prefix = `${params.portfolio}/opportunities/`; // e.g. NatSec_DoD/opportunities/

  try {
    const result = await s3.send(
      new ListObjectsV2Command({
        Bucket,
        Prefix,
        Delimiter: "/", // This ensures we get only top-level folders under the prefix
      })
    );

    const folders = (result.CommonPrefixes || []).map((p) =>
      p.Prefix?.replace(Prefix, "").replace(/\/$/, "")
    );

    console.log("Opportunities found:", folders);

    return NextResponse.json(folders);
  } catch (error) {
    console.error("S3 List Error:", error);
    return NextResponse.json({ error: "Failed to list opportunities" }, { status: 500 });
  }
}
