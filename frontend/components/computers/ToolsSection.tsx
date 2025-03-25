'use client';

import { Terminal } from 'lucide-react';
import { RemoteCommandPrompt } from '@/components/RemoteCommandPrompt';

interface ToolsSectionProps {
  computerId: string;
}

export function ToolsSection({ computerId }: ToolsSectionProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Terminal className="h-4 w-4" />
        <h2 className="text-lg font-semibold">Command Prompt</h2>
      </div>
      <RemoteCommandPrompt computerId={computerId} />
    </div>
  );
}
