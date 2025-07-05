import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { NextRequest, NextResponse } from "next/server";

const s3 = new S3Client({ region: "us-east-1" });

const BUCKET = process.env.S3_BUCKET || process.env.NEXT_PUBLIC_S3_BUCKET;

export async function POST(req: NextRequest) {
  try {
    const { folderName } = await req.json();

    if (!folderName || typeof folderName !== "string") {
      return NextResponse.json(
        { message: "Invalid or missing folder name." },
        { status: 400 }
      );
    }

    const folderKey = folderName.endsWith("/") ? folderName : `${folderName}/`;

    await s3.send(
      new PutObjectCommand({
        Bucket: BUCKET,
        Key: folderKey,
        Body: "",
      })
    );

    return NextResponse.json(
      { message: "Folder created successfully", folder: folderKey },
      { status: 200 }
    );
  } catch (err: any) {
    console.error("Folder creation error:", err);
    return NextResponse.json(
      { message: "Internal Server Error", error: err.message },
      { status: 500 }
    );
  }
}
