'use client';

import { Terminal } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import Link from 'next/link';

interface ToolsSectionProps {
  computer: any;
}

export default function ToolsSection({ computer }: ToolsSectionProps) {
  const { theme, mode } = useTheme();

  return (
    <div className="space-y-4">
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow`}>
        <div className={`px-4 py-3 border-b border-${mode === 'dark' ? 'gray-700' : 'gray-200'}`}>
          <h2 className="text-sm font-medium">Remote Commands</h2>
        </div>
        <div className="p-4">
          <Link 
            href={`/computers/${computer.id}/terminal`}
            className={`flex items-center gap-2 px-3 py-2 text-sm rounded-md hover:bg-${theme}-50 dark:hover:bg-${theme}-900/20 text-gray-700 dark:text-gray-300`}
          >
            <Terminal className="h-4 w-4" />
            <span>Command Prompt</span>
          </Link>
        </div>
      </div>
    </div>
  );
}
