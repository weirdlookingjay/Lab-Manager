"use client";

import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader2 } from 'lucide-react';
import { fetchWithAuth } from '@/app/utils/api';

interface PdfPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  pdfUrl: string;
  fileName: string;
}

export function PdfPreviewModal({ isOpen, onClose, pdfUrl, fileName }: PdfPreviewModalProps) {
  const [loading, setLoading] = useState(true);
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    async function loadPdf() {
      if (!isOpen || !pdfUrl) return;
      
      try {
        setLoading(true);
        setError(null);
        
        // Use fetchWithAuth directly with the full URL
        const response = await fetchWithAuth(pdfUrl);
        
        if (!response.ok) {
          throw new Error('Failed to load PDF');
        }
        
        const blob = await response.blob();
        if (!mounted) return;
        
        const objectUrl = URL.createObjectURL(blob);
        setBlobUrl(objectUrl);
        setLoading(false);
      } catch (err) {
        console.error('Error loading PDF:', err);
        if (!mounted) return;
        setError('Failed to load PDF. Please try again.');
        setLoading(false);
      }
    }

    loadPdf();
    
    return () => {
      mounted = false;
      if (blobUrl) {
        URL.revokeObjectURL(blobUrl);
        setBlobUrl(null);
      }
    };
  }, [isOpen, pdfUrl]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[80vh]">
        <DialogHeader>
          <DialogTitle>{fileName}</DialogTitle>
        </DialogHeader>
        <div className="flex-1 w-full h-full min-h-[60vh] relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          )}
          {error && (
            <div className="absolute inset-0 flex items-center justify-center text-red-500">
              {error}
            </div>
          )}
          {!loading && !error && blobUrl && (
            <object
              data={blobUrl}
              type="application/pdf"
              className="w-full h-full"
            >
              <p>Unable to display PDF. <a href={pdfUrl} target="_blank" rel="noopener noreferrer">Download</a> instead.</p>
            </object>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
