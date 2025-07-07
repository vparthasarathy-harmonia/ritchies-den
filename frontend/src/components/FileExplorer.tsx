'use client';

import { useEffect, useState, useRef } from 'react';

type FileItem = {
  name: string;
  size: number;
  lastModified: string;
  key: string;
};

export default function FileExplorer({ basePrefix }: { basePrefix: string }) {
  const [path, setPath] = useState<string[]>([]);
  const [folders, setFolders] = useState<string[]>([]);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedKeys, setSelectedKeys] = useState<string[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const currentPrefix = `${basePrefix}${path.join('/')}${path.length ? '/' : ''}`;

  const fetchContents = async () => {
    const res = await fetch(`/api/browse?prefix=${currentPrefix}`);
    const data = await res.json();
    setFolders(data.folders || []);
    setFiles(data.files || []);
    setSelectedKeys([]); // reset selection
  };

  useEffect(() => {
    if (basePrefix) fetchContents();
  }, [basePrefix, path.join('/')]);

  const handleCreateFolder = async () => {
    const name = prompt('Enter new folder name:');
    if (!name) return;

    await fetch('/api/browse/folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prefix: currentPrefix, name }),
    });

    fetchContents();
  };

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('prefix', currentPrefix);

    const res = await fetch('/api/browse/upload', {
      method: 'POST',
      body: formData,
    });

    if (res.ok) {
      fetchContents();
    } else {
      alert('Upload failed');
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files.length) {
      for (const file of e.dataTransfer.files) {
        await handleUpload(file);
      }
    }
  };

  const goBack = () => {
    setPath((prev) => prev.slice(0, -1));
  };

  const toggleSelect = (key: string) => {
    setSelectedKeys((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handleMultiDelete = async () => {
    if (selectedKeys.length === 0) return;

    const confirmed = confirm(
      `Are you sure you want to delete the following items?\n\n${selectedKeys.join(
        '\n'
      )}`
    );

    if (!confirmed) return;

    const res = await fetch('/api/browse', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keys: selectedKeys }),
    });

    if (res.ok) {
      fetchContents();
    } else {
      alert('Delete failed');
    }
  };

  const handleRename = async () => {
    if (selectedKeys.length !== 1) return;

    const oldKey = selectedKeys[0];
    const oldName = oldKey.split('/').filter(Boolean).pop() || '';
    const isFolder = oldKey.endsWith('/');
    const newName = prompt('Enter new name:', oldName);
    if (!newName || newName === oldName) return;

    const newKey =
      oldKey.slice(0, oldKey.lastIndexOf(oldName)) + newName + (isFolder ? '/' : '');

    const res = await fetch('/api/browse/rename', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ oldKey, newKey }),
    });

    if (res.ok) {
      fetchContents();
    } else {
      alert('Rename failed');
    }
  };

  return (
    <div
      className={`bg-white mt-8 rounded-lg p-4 border shadow-sm transition ${
        dragOver ? 'ring-2 ring-blue-400' : ''
      }`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Header: path and controls */}
      <div className="flex items-center justify-between mb-4">
        <div className="text-sm font-semibold text-gray-700 flex flex-wrap items-center gap-1">
          <span className="text-gray-400">Path:</span>
          {(() => {
            const baseParts = basePrefix.replace(/\/$/, '').split('/').filter(Boolean);
            const fullPath = [...baseParts, ...path];
            const dynamicOffset = baseParts.length;

            return fullPath.map((segment, index) => {
              const isDynamic = index >= dynamicOffset;
              const isLast = index === fullPath.length - 1;

              return (
                <span key={index} className="flex items-center gap-1">
                  {isDynamic && !isLast ? (
                    <button
                      onClick={() =>
                        setPath(path.slice(0, index - dynamicOffset + 1))
                      }
                      className="text-blue-600 hover:underline"
                    >
                      {segment}
                    </button>
                  ) : (
                    <span
                      className={
                        isLast ? 'text-gray-900 font-semibold' : 'text-gray-500'
                      }
                    >
                      {segment}
                    </span>
                  )}
                  {index < fullPath.length - 1 && (
                    <span className="text-gray-400">&gt;</span>
                  )}
                </span>
              );
            });
          })()}
        </div>

        <div className="flex gap-2 flex-wrap">
          {path.length > 0 && (
            <button
              onClick={goBack}
              className="text-xs text-blue-600 hover:underline"
            >
              ← Back
            </button>
          )}
          {selectedKeys.length === 1 && (
            <button
              onClick={handleRename}
              className="text-xs text-yellow-700 border border-yellow-500 px-3 py-1 rounded hover:bg-yellow-50"
            >
              ✏️ Rename
            </button>
          )}
          {selectedKeys.length > 0 && (
            <button
              onClick={handleMultiDelete}
              className="text-xs text-red-600 border border-red-500 px-3 py-1 rounded hover:bg-red-50"
            >
              🗑 Delete Selected
            </button>
          )}
          <button
            onClick={handleCreateFolder}
            className="text-xs text-white bg-[#1a18b9] px-3 py-1 rounded hover:bg-[#1414a3]"
          >
            + New Folder
          </button>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-xs text-[#1a18b9] border border-[#1a18b9] px-3 py-1 rounded hover:bg-gray-100"
          >
            Upload
          </button>
          <input
            type="file"
            ref={fileInputRef}
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
              e.target.value = '';
            }}
          />
        </div>
      </div>

      {/* Grid display */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 text-sm">
        {folders.map((folder) => {
          const folderKey = `${currentPrefix}${folder}/`;
          return (
            <div
              key={folder}
              className="px-4 py-3 border rounded bg-white hover:bg-gray-100 flex flex-col items-center justify-center text-center shadow-sm transition relative"
            >
              <input
                type="checkbox"
                className="absolute top-2 left-2"
                checked={selectedKeys.includes(folderKey)}
                onChange={() => toggleSelect(folderKey)}
              />
              <span
                onClick={() => setPath([...path, folder])}
                className="text-2xl cursor-pointer"
              >
                📁
              </span>
              <span className="mt-1 text-sm font-medium text-gray-800">
                {folder}
              </span>
            </div>
          );
        })}

        {files.map((file) => (
          <div
            key={file.key}
            className="px-4 py-3 border rounded bg-white flex flex-col items-center justify-center text-center shadow-sm relative"
          >
            <input
              type="checkbox"
              className="absolute top-2 left-2"
              checked={selectedKeys.includes(file.key)}
              onChange={() => toggleSelect(file.key)}
            />
            <a
              href={`https://${process.env.NEXT_PUBLIC_S3_BUCKET}.s3.${process.env.AWS_REGION}.amazonaws.com/${file.key}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xl hover:underline"
            >
              📄
            </a>
            <span className="mt-1 text-sm font-medium text-gray-700">
              {file.name}
            </span>
          </div>
        ))}

        {folders.length === 0 && files.length === 0 && (
          <div className="col-span-full text-center text-gray-500 italic py-4">
            Empty folder — drag & drop to upload files here.
          </div>
        )}
      </div>
    </div>
  );
}
