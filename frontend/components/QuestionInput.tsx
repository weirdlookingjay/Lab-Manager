"use client"

import React, { useState } from 'react';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Loader2, Send } from 'lucide-react';

interface QuestionInputProps {
  onSubmit: (question: string) => Promise<void>;
  isLoading?: boolean;
}

export const QuestionInput: React.FC<QuestionInputProps> = ({
  onSubmit,
  isLoading = false,
}) => {
  const [question, setQuestion] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isLoading) return;

    try {
      await onSubmit(question.trim());
      setQuestion('');
    } catch (error) {
      console.error('Error submitting question:', error);
    }
  };

  return (
    <Card className="w-full p-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <Textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about the PDF..."
          className="min-h-[100px] resize-none"
          disabled={isLoading}
        />
        
        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={!question.trim() || isLoading}
            className="w-24"
          >
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </form>
    </Card>
  );
};
