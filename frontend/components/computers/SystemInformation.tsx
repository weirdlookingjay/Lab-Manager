import React from 'react';
import { Computer, Metrics } from '@/lib/types';
import {
  BsCalendar3, 
  BsBuilding, BsGearFill,
  BsCheckCircleFill, BsWindows, BsHddNetwork, BsPc,
  BsBox, BsCpu, BsMemory, BsClock
} from 'react-icons/bs';
import { useTheme } from '@/hooks/useTheme';

const formatOsVersion = (osVersion: string | null): string => {
  if (!osVersion) return 'Not Available';
  
  // Match "Windows-" followed by version number
  const match = osVersion.match(/^Windows-(\d+)/);
  if (match) {
    return `Windows-${match[1]}`;
  }
  
  return osVersion;
};

interface SystemInformationProps {
  computer: Computer;
}

export default function SystemInformation({ computer }: SystemInformationProps) {
  const { theme, mode } = useTheme();

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZoneName: 'short'
    });
  };

  const bytesToGB = (bytes?: number): string => {
    if (!bytes) return '0';
    return (bytes / (1024 * 1024 * 1024)).toFixed(1);
  };

  const formatMemory = (total?: number, free?: number) => {
    if (!total) return 'Not Available';
    const used = total - (free || 0);
    return `${bytesToGB(used)} GB / ${bytesToGB(total)} GB`;
  };

  const leftColumn = [
    {
      label: 'LAST DISCOVERY',
      value: formatDate(computer.last_metrics_update),
      icon: <BsCalendar3 size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'IP ADDRESS',
      value: computer.ip_address || 'Not Available',
      icon: <BsHddNetwork size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'MANUFACTURER',
      value: computer.metrics?.metrics?.cpu?.manufacturer || 'Not Available',
      icon: <BsBuilding size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'MEMORY',
      value: formatMemory(computer.memory_total, computer.memory_free),
      icon: <BsMemory size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'OPERATING SYSTEM',
      value: formatOsVersion(computer.os_version),
      icon: <BsWindows size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'CPU USAGE',
      value: computer.cpu_percent !== undefined ? `${computer.cpu_percent}%` : 'Not Available',
      icon: <BsCpu size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'UPTIME',
      value: computer.uptime || 'Not Available',
      icon: <BsClock size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    }
  ];

  const rightColumn = [
    {
      label: 'SYSTEM NAME',
      value: computer.hostname || '',
      icon: <BsPc size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'CLASS',
      value: computer.device_class || 'Not Available',
      icon: <BsBox size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'ARCHITECTURE',
      value: computer.metrics?.metrics?.cpu?.architecture || 'Not Available',
      icon: <BsGearFill size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'MODEL',
      value: computer.metrics?.model || 'Not Available',
      icon: <BsPc size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'DISK',
      value: `${(computer.disk_usage || 0).toFixed(1)} GB / ${computer.disk_gb?.replace(' GB', '') || '0'} GB`,
      icon: <BsHddNetwork size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'CPU',
      value: computer.cpu_model || 'Not Available',
      icon: <BsCpu size={14} className={`text-${theme}-600 dark:text-${theme}-400`} />
    },
    {
      label: 'AGENT STATUS',
      value: computer.status || 'offline',
      icon: <BsCheckCircleFill size={14} className={computer.status === 'online' ? "text-green-500" : "text-red-500"} />
    }
  ];

  return (
    <div className={`rounded-lg border border-${mode === 'dark' ? 'gray-700' : 'red-200'} bg-white dark:bg-gray-800 shadow-sm`}>
      <div className={`px-4 py-3 border-b border-${mode === 'dark' ? 'gray-700' : 'gray-200'} bg-gray-50/50 dark:bg-gray-800`}>
        <h2 className="text-sm font-medium text-gray-900 dark:text-white">System Information</h2>
      </div>
      <div className="grid grid-cols-2 gap-6 p-4">
        <div className="space-y-4">
          {leftColumn.map((item, index) => (
            <div key={index} className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-${theme}-50/50 dark:bg-${theme}-900/10 text-${theme}-600 dark:text-${theme}-400`}>
                {item.icon}
              </div>
              <div>
                <div className="text-[11px] font-medium text-gray-500 dark:text-gray-400">{item.label}</div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">{item.value}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="space-y-4">
          {rightColumn.map((item, index) => (
            <div key={index} className="flex items-center gap-3">
              <div className={`p-2 rounded-lg bg-${theme}-50/50 dark:bg-${theme}-900/10 text-${theme}-600 dark:text-${theme}-400`}>
                {item.icon}
              </div>
              <div>
                <div className="text-[11px] font-medium text-gray-500 dark:text-gray-400">{item.label}</div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">{item.value}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
