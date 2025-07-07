import {
  S3Client,
  CopyObjectCommand,
  DeleteObjectCommand,
} from '@aws-sdk/client-s3';
import { NextRequest, NextResponse } from 'next/server';

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

export async function POST(req: NextRequest) {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const { oldKey, newKey } = await req.json();

  if (!oldKey || !newKey || oldKey === newKey) {
    return NextResponse.json({ error: 'Invalid keys' }, { status: 400 });
  }

  try {
    await s3.send(
      new CopyObjectCommand({
        Bucket,
        CopySource: `${Bucket}/${oldKey}`,
        Key: newKey,
      })
    );

    await s3.send(
      new DeleteObjectCommand({
        Bucket,
        Key: oldKey,
      })
    );

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Rename error:', error);
    return NextResponse.json({ error: 'Rename failed' }, { status: 500 });
  }
}
