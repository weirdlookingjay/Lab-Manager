"use client";

import React from 'react';
import { Card } from './ui/card';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';

interface AnswerDisplayProps {
  answer: string | {
    text: string;
    confidence?: number;
    context?: string;
    page_num?: number;
    start_pos?: number;
    end_pos?: number;
    metadata?: {
      font_info?: Record<string, {
        font: string;
        size: number;
        color: string;
      }>;
      [key: string]: any;
    };
  };
  onPageChange?: (page: number) => void;
  onHighlight?: (answer: any) => void;
}

export const AnswerDisplay: React.FC<AnswerDisplayProps> = ({
  answer,
  onPageChange,
  onHighlight,
}) => {
  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(1)}%`;
  };

  const getFontInfo = (fontInfo: Record<string, { font: string }> | undefined) => {
    if (!fontInfo) return null;
    const firstFont = Object.values(fontInfo)[0];
    return firstFont?.font;
  };

  const answerText = typeof answer === 'string' ? answer : answer.text;
  const metadata = typeof answer === 'string' ? null : answer;

  return (
    <Card className="w-full p-4">
      <ScrollArea className="max-h-[400px] pr-4">
        <div className="space-y-4">
          <div className="space-y-2">
            <p className="text-sm text-foreground/80">{answerText}</p>
            {metadata && (
              <div className="flex flex-wrap gap-2 mt-2">
                {metadata.confidence && (
                  <Badge variant="secondary">
                    Confidence: {formatConfidence(metadata.confidence)}
                  </Badge>
                )}
                {metadata.page_num && (
                  <Badge
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => onPageChange?.(metadata.page_num!)}
                  >
                    Page {metadata.page_num}
                  </Badge>
                )}
                {metadata.metadata?.font_info && (
                  <Badge variant="secondary">
                    Font: {getFontInfo(metadata.metadata.font_info)}
                  </Badge>
                )}
                {onHighlight && metadata.page_num && (
                  <Badge
                    variant="outline"
                    className="cursor-pointer"
                    onClick={() => onHighlight?.(metadata)}
                  >
                    Highlight
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
    </Card>
  );
};
