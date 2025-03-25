import { useState, useEffect, useCallback } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { formatBytes } from "@/lib/utils";
import { FolderIcon, FileIcon, ChevronLeftIcon } from "lucide-react";
import { Computer } from '@/types/computer';

interface FileSystemProps {
    computer: Computer;
}

interface FileSystemEntry {
    name: string;
    type: 'file' | 'directory';
    size?: number;
    modified?: string;
    path: string;
}

export function FileSystemExplorer({ computer }: FileSystemProps) {
    const [currentPath, setCurrentPath] = useState('/');
    const [entries, setEntries] = useState<FileSystemEntry[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadRemoteFiles = useCallback(async (path: string) => {
        if (!computer.is_online) {
            setError('Computer is offline');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch(`/api/computers/${computer.id}/files?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error('Failed to load directory contents');
            }
            const data = await response.json();
            setEntries(data.entries);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'An error occurred');
        } finally {
            setIsLoading(false);
        }
    }, [computer.id, computer.is_online]);

    useEffect(() => {
        loadRemoteFiles(currentPath);
    }, [currentPath, loadRemoteFiles]);

    const navigateUp = () => {
        const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
        setCurrentPath(parentPath);
    };

    const navigateTo = (entry: FileSystemEntry) => {
        if (entry.type === 'directory') {
            setCurrentPath(entry.path);
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center space-x-2">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={navigateUp}
                    disabled={currentPath === '/'}
                >
                    <ChevronLeftIcon className="h-4 w-4" />
                </Button>
                <Input
                    value={currentPath}
                    readOnly
                    className="font-mono text-sm"
                />
            </div>

            {error && (
                <div className="p-4 text-sm text-red-500 bg-red-50 rounded-md">
                    {error}
                </div>
            )}

            {isLoading ? (
                <div className="p-4 text-sm text-gray-500">Loading...</div>
            ) : (
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Name</TableHead>
                            <TableHead>Size</TableHead>
                            <TableHead>Modified</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {entries.map((entry) => (
                            <TableRow
                                key={entry.path}
                                className="cursor-pointer hover:bg-gray-50"
                                onClick={() => navigateTo(entry)}
                            >
                                <TableCell className="flex items-center space-x-2">
                                    {entry.type === 'directory' ? (
                                        <FolderIcon className="h-4 w-4 text-blue-500" />
                                    ) : (
                                        <FileIcon className="h-4 w-4 text-gray-500" />
                                    )}
                                    <span>{entry.name}</span>
                                </TableCell>
                                <TableCell>
                                    {entry.size !== undefined ? formatBytes(entry.size) : '-'}
                                </TableCell>
                                <TableCell>{entry.modified || '-'}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            )}
        </div>
    );
}
