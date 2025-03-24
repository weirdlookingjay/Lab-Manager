import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatBytes } from "@/lib/utils";
import { FolderIcon, FileIcon, DownloadIcon, UploadIcon, ChevronLeftIcon, AlertTriangle } from "lucide-react";
import { Computer } from '@/lib/types';

interface FileSystemProps {
  computer: Computer;
}

interface FileSystemEntry {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

interface FileItem {
  name: string;
  path: string;
  isDirectory: boolean;
  size: number | null;
  modifiedTime: string;
}

function formatFileSize(bytes: number): string {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }

  return `${size.toFixed(1)} ${units[unitIndex]}`;
}

export function FileSystemExplorer({ computer }: FileSystemProps) {
  const [localPath, setLocalPath] = useState("/");
  const [remotePath, setRemotePath] = useState("/");
  const [localFiles, setLocalFiles] = useState<FileItem[]>([]);
  const [remoteFiles, setRemoteFiles] = useState<FileItem[]>([]);
  const [selectedLocalFile, setSelectedLocalFile] = useState<string | null>(null);
  const [selectedRemoteFile, setSelectedRemoteFile] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLocalFiles(localPath);
    if (computer.status === 'online') {
      loadRemoteFiles(remotePath);
    }
  }, [localPath, remotePath, computer.status]);

  const loadLocalFiles = async (path: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/files/local?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error("Failed to load local files");
      const files = await response.json();
      setLocalFiles(files);
      setError(null);
    } catch (err) {
      setError("Failed to load local files");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadRemoteFiles = async (path: string) => {
    if (computer.status !== 'online') {
      setRemoteFiles([]);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/computers/${computer.id}/files?path=${encodeURIComponent(path)}`);
      if (!response.ok) throw new Error("Failed to load remote files");
      const files = await response.json();
      setRemoteFiles(files);
      setError(null);
    } catch (err) {
      setError("Failed to load remote files");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLocalNavigate = (path: string) => {
    setLocalPath(path);
    setSelectedLocalFile(null);
  };

  const handleRemoteNavigate = (path: string) => {
    setRemotePath(path);
    setSelectedRemoteFile(null);
  };

  const handleUpload = async () => {
    if (!selectedLocalFile) return;
    if (computer.status !== 'online') {
      setError("Cannot upload files when computer is offline");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/computers/${computer.id}/files/upload`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          localPath: selectedLocalFile,
          remotePath: remotePath
        })
      });
      
      if (!response.ok) throw new Error("Failed to upload file");
      loadRemoteFiles(remotePath);
      setError(null);
    } catch (err) {
      setError("Failed to upload file");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!selectedRemoteFile) return;
    if (computer.status !== 'online') {
      setError("Cannot download files when computer is offline");
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/computers/${computer.id}/files/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          remotePath: selectedRemoteFile,
          localPath: localPath
        })
      });
      
      if (!response.ok) throw new Error("Failed to download file");
      loadLocalFiles(localPath);
      setError(null);
    } catch (err) {
      setError("Failed to download file");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const FileList = ({ 
    files, 
    currentPath, 
    onNavigate, 
    selectedFile, 
    onSelectFile,
    isLocal 
  }: { 
    files: FileItem[]; 
    currentPath: string;
    onNavigate: (path: string) => void;
    selectedFile: string | null;
    onSelectFile: (path: string | null) => void;
    isLocal: boolean;
  }) => (
    <div className="h-[600px] overflow-auto">
      {currentPath && (
        <Button
          variant="ghost"
          className="mb-2"
          onClick={() => {
            const parentPath = currentPath.split('/').slice(0, -1).join('/');
            onNavigate(parentPath);
          }}
        >
          <ChevronLeftIcon className="mr-2 h-4 w-4" />
          Up
        </Button>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>Modified</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {files.map((file) => (
            <TableRow 
              key={file.path}
              className={`cursor-pointer ${selectedFile === file.path ? 'bg-muted' : ''}`}
              onClick={() => {
                if (file.isDirectory) {
                  onNavigate(file.path);
                } else {
                  onSelectFile(file.path === selectedFile ? null : file.path);
                }
              }}
            >
              <TableCell className="flex items-center">
                {file.isDirectory ? (
                  <FolderIcon className="mr-2 h-4 w-4" />
                ) : (
                  <FileIcon className="mr-2 h-4 w-4" />
                )}
                {file.name}
              </TableCell>
              <TableCell>{file.size ? formatFileSize(file.size) : '-'}</TableCell>
              <TableCell>{file.modifiedTime || '-'}</TableCell>
              {!file.isDirectory && (
                <TableCell>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => isLocal ? handleUpload() : handleDownload()}
                    disabled={computer.status !== 'online' || loading}
                  >
                    {isLocal ? <UploadIcon className="h-4 w-4" /> : <DownloadIcon className="h-4 w-4" />}
                  </Button>
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );

  return (
    <div className="grid grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Local Files</CardTitle>
          <div className="text-sm text-muted-foreground">
            Current path: {localPath || '/'}
          </div>
        </CardHeader>
        <CardContent>
          <FileList
            files={localFiles}
            currentPath={localPath}
            onNavigate={handleLocalNavigate}
            selectedFile={selectedLocalFile}
            onSelectFile={setSelectedLocalFile}
            isLocal={true}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Remote Files - {computer.label}</CardTitle>
            <div className="text-sm text-muted-foreground">
              Current path: {remotePath || '/'}
            </div>
          </div>
          {computer.status !== 'online' && (
            <div className="flex items-center text-yellow-600">
              <AlertTriangle className="h-4 w-4 mr-2" />
              <span className="text-sm">Computer Offline</span>
            </div>
          )}
        </CardHeader>
        <CardContent>
          {computer.status === 'online' ? (
            <FileList
              files={remoteFiles}
              currentPath={remotePath}
              onNavigate={handleRemoteNavigate}
              selectedFile={selectedRemoteFile}
              onSelectFile={setSelectedRemoteFile}
              isLocal={false}
            />
          ) : (
            <div className="text-center p-4 text-muted-foreground">
              <p>File system operations are disabled while the computer is offline.</p>
              <p className="text-sm mt-2">The computer will be considered online when it reports metrics or is seen within the last 30 minutes.</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="col-span-2 flex justify-center space-x-4">
        <Button
          onClick={handleUpload}
          disabled={!selectedLocalFile || !selectedLocalFile.length || computer.status !== 'online' || loading}
        >
          <UploadIcon className="mr-2 h-4 w-4" />
          Upload to Remote
        </Button>
        <Button
          onClick={handleDownload}
          disabled={!selectedRemoteFile || !selectedRemoteFile.length || computer.status !== 'online' || loading}
        >
          <DownloadIcon className="mr-2 h-4 w-4" />
          Download to Local
        </Button>
      </div>

      {error && (
        <div className="col-span-2 bg-destructive/10 border-l-4 border-destructive p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-destructive" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
