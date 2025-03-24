import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Download, Tag, Trash, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { fetchWithAuth } from '@/app/utils/api';

interface BulkActionBarProps {
  selectedDocs: Set<string>;
  onClearSelection: () => void;
  className?: string;
}

export function BulkActionBar({
  selectedDocs,
  onClearSelection,
  className = ''
}: BulkActionBarProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const { toast } = useToast();

  const handleDownload = async () => {
    try {
      setIsDownloading(true);
      // Create a zip file of selected documents
      const response = await fetchWithAuth(`/api/auth/documents/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ paths: Array.from(selectedDocs) }),
      });

      if (!response.ok) throw new Error('Failed to download documents');

      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'documents.zip';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Success",
        description: "Documents downloaded successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to download selected documents",
        variant: "destructive"
      });
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className={`
      fixed bottom-4 left-1/2 -translate-x-1/2 
      flex items-center gap-4 p-4 
      bg-background border border-border rounded-lg shadow-lg 
      animate-in slide-in-from-bottom-4
      ${className}
    `}>
      <span className="text-sm font-medium text-foreground">
        {selectedDocs.size} item{selectedDocs.size !== 1 ? 's' : ''} selected
      </span>
      
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleDownload}
          disabled={isDownloading}
          className="bg-background hover:bg-muted"
        >
          <Download className="h-4 w-4 mr-2" />
          {isDownloading ? 'Downloading...' : 'Download Selected'}
        </Button>
        
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearSelection}
          className="hover:bg-muted"
        >
          <X className="h-4 w-4 mr-2" />
          Clear Selection
        </Button>
      </div>
    </div>
  );
}
