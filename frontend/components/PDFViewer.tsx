"use client";

import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';


interface PDFViewerProps {
  pdfId: string;
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  highlightRegions?: Array<{
    x0: number;
    y0: number;
    x1: number;
    y1: number;
  }>;
}

export const PDFViewer: React.FC<PDFViewerProps> = ({
  pdfId,
  currentPage,
  totalPages,
  onPageChange,
  highlightRegions,
}) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  // Build image URL with highlight parameters
  const getPageImageUrl = () => {
    const baseUrl = `/api/qa/page-image?pdf_id=${pdfId}&page_num=${currentPage}`;
    if (highlightRegions && highlightRegions.length > 0) {
      return `${baseUrl}&highlight_regions=${encodeURIComponent(JSON.stringify(highlightRegions))}`;
    }
    return baseUrl;
  };

  const handlePageChange = async (newPage: number) => {
    if (newPage < 1 || newPage > totalPages) return;
    setLoading(true);
    try {
      await onPageChange(newPage);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to change page",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-4xl mx-auto p-4">
      <div className="relative min-h-[600px] bg-muted rounded-lg overflow-hidden">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : (
          <img
            src={getPageImageUrl()}
            alt={`Page ${currentPage}`}
            className="w-full h-auto"
            onError={() => {
              toast({
                title: "Error",
                description: "Failed to load page image",
                variant: "destructive",
              });
            }}
          />
        )}
      </div>
      
      <div className="flex items-center justify-between mt-4">
        <Button
          variant="outline"
          onClick={() => handlePageChange(currentPage - 1)}
          disabled={currentPage <= 1 || loading}
        >
          Previous
        </Button>
        
        <div className="flex items-center gap-2">
          <Input
            type="number"
            min={1}
            max={totalPages}
            value={currentPage}
            onChange={(e) => handlePageChange(parseInt(e.target.value))}
            className="w-20 text-center"
          />
          <span className="text-sm text-muted-foreground">
            of {totalPages}
          </span>
        </div>
        
        <Button
          variant="outline"
          onClick={() => handlePageChange(currentPage + 1)}
          disabled={currentPage >= totalPages || loading}
        >
          Next
        </Button>
      </div>
    </Card>
  );
};
