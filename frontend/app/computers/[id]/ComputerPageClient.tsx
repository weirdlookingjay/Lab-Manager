'use client';

import { ArrowLeft } from "lucide-react";
import Link from 'next/link';
import SystemOverview from "@/components/computers/SystemOverview";
import SystemInformation from "@/components/computers/SystemInformation";
import { ProcessesSection } from "@/components/computers/ProcessesSection";
import ToolsSection from "@/components/computers/ToolsSection";
import { useTheme } from "@/hooks/useTheme";
import { useState } from 'react';

interface ComputerPageClientProps {
  computer: any;
}

export default function ComputerPageClient({ computer }: ComputerPageClientProps) {
  const { theme, mode } = useTheme();
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'tools', label: 'Tools' },
    { id: 'monitoring', label: 'Monitoring' },
    { id: 'asset', label: 'Asset' },
    { id: 'notes', label: 'Notes' },
    { id: 'settings', label: 'Settings' },
    { id: 'remote', label: 'Remote Control Settings' },
    { id: 'reports', label: 'Reports' }
  ];

  return (
    <div className={`flex flex-col h-full ${mode === 'dark' ? 'dark' : ''}`}>
      <div className={`flex items-center gap-3 px-3 py-2 bg-${theme}-600 text-white dark:bg-${theme}-900`}>
        <Link href="/computers" className="hover:opacity-80 transition-opacity">
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <h1 className="text-xs font-medium">{computer.hostname}</h1>
        <div className="flex items-center gap-1">
          <div className={`h-1.5 w-1.5 rounded-full ${computer.status === 'online' ? 'bg-emerald-400' : 'bg-red-400'} animate-pulse`} />
          <span className="text-[11px] opacity-90">{computer.status === 'online' ? 'Online' : 'Offline'}</span>
        </div>
        <div className="text-[11px] opacity-80">
          Last seen: {computer.last_seen}
        </div>
        <div className="text-[11px] opacity-80">
          Last metrics: {computer.last_metrics_update}
        </div>
      </div>

      <SystemOverview computer={computer} />

      <nav className={`border-b border-${mode === 'dark' ? 'gray-700' : 'gray-200'} bg-white dark:bg-gray-800`}>
        <div className="flex overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 text-[11px] font-medium border-b-2 whitespace-nowrap ${
                activeTab === tab.id
                  ? `text-${theme}-600 dark:text-${theme}-400 border-${theme}-600 dark:border-${theme}-400`
                  : 'text-gray-500 dark:text-gray-400 border-transparent hover:text-gray-700 dark:hover:text-gray-300'
              } -mb-px`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </nav>

      <div className="flex-1 bg-white dark:bg-gray-900">
        <div className="p-4 space-y-4">
          {activeTab === 'overview' && (
            <>
              <SystemInformation computer={computer} />
              <ProcessesSection computer={computer} />
            </>
          )}
          {activeTab === 'tools' && (
            <ToolsSection computer={computer} />
          )}
          {activeTab === 'monitoring' && (
            <div>Monitoring content</div>
          )}
          {activeTab === 'asset' && (
            <div>Asset content</div>
          )}
          {activeTab === 'notes' && (
            <div>Notes content</div>
          )}
          {activeTab === 'settings' && (
            <div>Settings content</div>
          )}
          {activeTab === 'remote' && (
            <div>Remote Control Settings content</div>
          )}
          {activeTab === 'reports' && (
            <div>Reports content</div>
          )}
        </div>
      </div>
    </div>
  );
}
