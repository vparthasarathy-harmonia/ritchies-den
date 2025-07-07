import {
  S3Client,
  ListObjectsV2Command,
  DeleteObjectsCommand,
} from '@aws-sdk/client-s3';
import { NextRequest, NextResponse } from 'next/server';

const s3 = new S3Client({
  region: process.env.AWS_REGION,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// === GET: List files/folders ===
export async function GET(req: Request) {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const { searchParams } = new URL(req.url);
  const prefix = searchParams.get('prefix') || '';

  try {
    const result = await s3.send(
      new ListObjectsV2Command({
        Bucket,
        Prefix: prefix,
        Delimiter: '/',
      })
    );

    const folders = (result.CommonPrefixes || []).map((p) =>
      p.Prefix?.replace(prefix, '').replace(/\/$/, '')
    );

    const files = (result.Contents || [])
      .filter((item) => item.Key !== prefix)
      .map((item) => ({
        name: item.Key!.replace(prefix, ''),
        size: item.Size,
        lastModified: item.LastModified,
        key: item.Key,
      }));

    return NextResponse.json({ folders, files });
  } catch (error) {
    console.error('Browse error:', error);
    return NextResponse.json({ error: 'Failed to browse S3' }, { status: 500 });
  }
}

// === DELETE: Multi-delete support ===
export async function DELETE(req: NextRequest) {
  const Bucket = process.env.S3_BUCKET_NAME!;
  const { keys } = await req.json();

  if (!Array.isArray(keys) || keys.length === 0) {
    return NextResponse.json({ error: 'No keys provided' }, { status: 400 });
  }

  try {
    const result = await s3.send(
      new DeleteObjectsCommand({
        Bucket,
        Delete: {
          Objects: keys.map((Key: string) => ({ Key })),
          Quiet: false,
        },
      })
    );

    return NextResponse.json({ deleted: result.Deleted });
  } catch (error) {
    console.error('Delete error:', error);
    return NextResponse.json({ error: 'Failed to delete objects' }, { status: 500 });
  }
}
