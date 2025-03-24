"use client";

import React, { useState, useCallback } from 'react';
import { PDFViewer } from '@/components/PDFViewer';
import { QuestionInput } from '@/components/QuestionInput';
import { AnswerDisplay } from '@/components/AnswerDisplay';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Upload } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { fetchWithAuth } from '@/app/utils/api';

interface Answer {
  text: string;
  confidence: number;
  context: string;
  page_num: number;
  start_pos: number;
  end_pos: number;
  metadata: {
    font_info?: Record<string, {
      font: string;
      size: number;
      color: string;
    }>;
    [key: string]: any;
  };
}

interface HighlightRegion {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export default function PDFQAPage() {
  const [pdfId, setPdfId] = React.useState<string | null>(null);
  const [currentPage, setCurrentPage] = React.useState(1);
  const [totalPages, setTotalPages] = React.useState(1);
  const [answers, setAnswers] = React.useState<Answer[]>([]);
  const [highlightRegions, setHighlightRegions] = React.useState<HighlightRegion[]>([]);
  const [answer, setAnswer] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  const handleFileUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/qa/process-pdf', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to process PDF');

      const data = await response.json();
      setPdfId(data.pdf_id);
      setTotalPages(data.num_pages);
      setCurrentPage(1);
      setAnswers([]);
      setHighlightRegions([]);

      toast({
        title: "Success",
        description: "PDF uploaded and processed successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to process PDF",
        variant: "destructive",
      });
    }
  };

  const handleAskQuestion = async (question: string) => {
    setIsLoading(true);
    setAnswer('');
    setHighlightRegions([]);

    try {
      const response = await fetchWithAuth('/api/qa/ask/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question,
          pdf_id: pdfId,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get answer');
      }

      const data = await response.json();
      setAnswer(data.answer);
      
      // If the response includes highlight regions, update them
      if (data.highlights) {
        // Convert the highlight format from the API to match PDFViewer's format
        setHighlightRegions(data.highlights.map((h: any) => ({
          x0: h.boundingBox[0],
          y0: h.boundingBox[1],
          x1: h.boundingBox[2],
          y1: h.boundingBox[3],
        })));
      }
    } catch (error) {
      console.error('Error getting answer:', error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to get answer from the AI",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleHighlight = (answer: Answer) => {
    setHighlightRegions([{
      x0: answer.start_pos,
      y0: 0,
      x1: answer.end_pos,
      y1: 100,
    }]);
  };

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8">PDF Question & Answer</h1>
      
      {!pdfId ? (
        <Card className="w-full max-w-xl mx-auto p-8 text-center">
          <input
            type="file"
            ref={fileInputRef}
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFileUpload(file);
            }}
          />
          <Button
            onClick={() => fileInputRef.current?.click()}
            size="lg"
            className="w-64"
          >
            <Upload className="h-5 w-5 mr-2" />
            Upload PDF
          </Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-8">
            <PDFViewer
              pdfId={pdfId}
              currentPage={currentPage}
              totalPages={totalPages}
              onPageChange={setCurrentPage}
              highlightRegions={highlightRegions}
            />
            <div className="flex-1 overflow-y-auto p-4">
              <QuestionInput 
                onSubmit={handleAskQuestion} 
                isLoading={isLoading} 
              />
              {answer && <AnswerDisplay answer={answer} />}
            </div>
          </div>
          <div>
            {answers.map((answer, index) => (
              <div key={index}>
                <AnswerDisplay
                  answer={answer.text}
                  onPageChange={setCurrentPage}
                  onHighlight={() => handleHighlight(answer)}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
