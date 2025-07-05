"use client";

import Image from "next/image";
import React, { useState, useEffect } from "react";
import { ThemeToggle } from "../../components/theme-toggle";
import { Button } from "../../components/ui/button";

export default function Page() {
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [folders, setFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string>("opportunities/test");
  const [newFolderName, setNewFolderName] = useState<string>("");

  useEffect(() => {
    const fetchFolders = async () => {
      const res = await fetch("/api/list-folders");
      const data = await res.json();
      setFolders(data.folders || []);
    };
    fetchFolders();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSelectedFiles(e.target.files);
  };

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
      alert("Please select files first.");
      return;
    }

    for (const file of Array.from(selectedFiles)) {
      try {
        const folder = selectedFolder;

        const res = await fetch("/api/s3-upload-url", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ fileName: file.name, fileType: file.type, folder }),
        });

        const { url } = await res.json();

        const uploadRes = await fetch(url, {
          method: "PUT",
          headers: { "Content-Type": file.type },
          body: file,
        });

        if (!uploadRes.ok) throw new Error(`Failed to upload ${file.name}`);
      } catch (err) {
        console.error("Upload error:", err);
        alert("Upload failed: " + (err as Error).message);
        return;
      }
    }

    alert("All files uploaded successfully!");
    setSelectedFiles(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-slate-100 p-10">
      <div className="max-w-7xl mx-auto rounded-xl shadow-lg bg-white p-6">
        <header className="flex items-center justify-between mb-10 border-b pb-4">
          <div className="flex items-center space-x-4">
            <Image src="/harmonia-logo.png" alt="Harmonia Logo" width={40} height={40} />
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Ritchie's Den</h1>
              <p className="text-sm text-gray-500">AI Solution Architecture Workspace</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Image
              src="/ritchie-avatar.png"
              alt="Ritchie Avatar"
              width={56}
              height={56}
              className="rounded-lg border border-gray-300"
            />
            <ThemeToggle />
          </div>
        </header>

        <div className="grid grid-cols-5 gap-6">
          <aside className="col-span-1 border-r pr-4">
            <h2 className="text-lg font-semibold mb-2 text-gray-700">Folders</h2>

            <div className="mb-4">
  <input
    type="text"
    placeholder="New folder name"
    value={newFolderName}
    onChange={(e) => setNewFolderName(e.target.value)}
    className="w-full px-2 py-1 text-sm border rounded mb-1"
  />
  <button
    onClick={async () => {
      if (!newFolderName) return;
      const res = await fetch("/api/create-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folderName: newFolderName }),
      });
      const data = await res.json();
      if (res.ok) {
        setFolders((prev) => [...prev, newFolderName]);
        setNewFolderName("");
      } else {
        alert(data.message);
      }
    }}
    className="text-sm bg-green-600 text-white rounded px-2 py-1 hover:bg-green-700"
  >
    + Create Folder
  </button>
</div>

            <ul className="space-y-1">
              {folders.map((folder) => (
                <li key={folder}>
                  <button
                    onClick={() => setSelectedFolder(folder)}
                    className={`text-left w-full px-2 py-1 rounded text-sm ${
                      selectedFolder === folder ? "bg-blue-100 text-blue-700" : "hover:bg-gray-100"
                    }`}
                  >
                    {folder.replace(/\/$/, "")}
                  </button>
                </li>
              ))}
            </ul>
          </aside>

          <main className="col-span-4">
            <div className="bg-gray-50 border border-dashed border-gray-300 p-6 rounded-lg">
              <label className="block text-gray-700 font-semibold mb-2">
                Upload Documents to <span className="font-mono">{selectedFolder}</span>
              </label>
              <input
                type="file"
                multiple
                onChange={handleFileChange}
                className="mb-4 block w-full text-sm text-gray-600"
              />

              {selectedFiles && (
                <ul className="list-disc pl-5 space-y-1 mb-4 text-sm text-gray-700">
                  {Array.from(selectedFiles).map((file) => (
                    <li key={file.name}>
                      {file.name} — {(file.size / 1024).toFixed(1)} KB
                    </li>
                  ))}
                </ul>
              )}

              <Button onClick={handleUpload} className="mt-2">
                Upload
              </Button>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
