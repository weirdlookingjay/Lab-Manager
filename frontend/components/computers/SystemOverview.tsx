import React from 'react';
import { Computer } from '@/lib/types';
import {
  BsMemory, BsWindows,
  BsPerson, BsClock, BsGlobe, BsCalendar3, BsBuilding, BsBox
} from 'react-icons/bs';
import { useTheme } from '@/hooks/useTheme';
import { useMetricsPolling } from '@/hooks/useMetricsPolling';

interface SystemOverviewProps {
  computer: Computer;
}

const formatOsVersion = (osVersion: string | null): string => {
  if (!osVersion) return 'Not Available';
  
  // Match "Windows-" followed by version number
  const match = osVersion.match(/^Windows-(\d+)/);
  if (match) {
    return `Windows-${match[1]}`;
  }
  
  return osVersion;
};

export default function SystemOverview({ computer }: SystemOverviewProps) {
  const { theme } = useTheme();
  const { metrics } = useMetricsPolling(computer.id, 5000); // Poll every 5 seconds

  // Merge real-time metrics with computer data
  const cpuUsage = metrics?.metrics?.cpu?.percent ?? metrics?.cpu_percent ?? computer.metrics?.cpu?.percent ?? computer.cpu_percent ?? 0;
  const cpuSpeed = metrics?.metrics?.cpu?.speed ?? metrics?.cpu_speed ?? computer.metrics?.cpu?.speed ?? computer.cpu_speed ?? 3.30;
  const memoryPercent = metrics?.memory_percent ?? computer.memory_percent ?? 0;
  const memoryGB = metrics?.memory_gb ?? computer.memory_gb ?? '0';
  
  // Usage stats section
  const usageStats = [
    {
      label: 'CPU USAGE',
      value: `${cpuUsage}%`,
      subValue: `${cpuSpeed} GHz`,
      width: cpuUsage,
      color: `var(--${theme}-600)`
    },
    {
      label: 'MEMORY USAGE',
      value: `${memoryPercent}%`,
      subValue: `${memoryGB} GB`,
      width: memoryPercent,
      color: `var(--${theme}-600)`
    }
  ];

  const leftColumn = [
    {
      label: 'LAST DISCOVERY',
      value: computer.last_metrics_update || 'Not Available',
      icon: <BsCalendar3 size={14} className={`text-${theme}-100`} />
    },
    {
      label: 'MANUFACTURER',
      value: (metrics?.metrics?.cpu?.manufacturer ?? metrics?.cpu?.manufacturer ?? computer.metrics?.cpu?.manufacturer) || 'Not Available',
      icon: <BsBuilding size={14} className={`text-${theme}-100`} />
    },
    {
      label: 'MEMORY',
      value: `${memoryGB} GB (${memoryPercent}% Used)`,
      icon: <BsMemory size={14} className={`text-${theme}-100`} />
    },
    {
      label: 'OPERATING SYSTEM',
      value: formatOsVersion(computer.os_version),
      icon: <BsWindows size={14} className={`text-${theme}-100`} />
    }
  ];

  const rightColumn = [
    {
      icon: <BsClock size={14} className={`text-${theme}-100`} />,
      label: 'UPTIME',
      value: computer.uptime || 'Not Available'
    },
    {
      label: 'DEVICE CLASS',
      value: computer.device_class || 'Not Available',
      icon: <BsBox size={14} className={`text-${theme}-100`} />
    },
    {
      label: 'NETWORKING',
      value: `${computer.label || 'Unknown'} (${computer.ip_address || 'No IP'})`,
      icon: <BsGlobe size={14} className={`text-${theme}-100`} />
    },
    {
      label: 'LOGGED IN USER',
      value: computer.logged_in_user || 'Not Available',
      icon: <BsPerson size={14} className={`text-${theme}-100`} />
    }
  ];

  return (
    <div className="bg-white p-4">
      <div className="grid grid-cols-12 gap-4">
        {/* Left Column */}
        <div className="col-span-5 space-y-1">
          {leftColumn.map((item, index) => (
            <div key={index} className="flex">
              <div className={`flex items-center gap-2 bg-${theme}-600 text-white px-3 py-1 w-40`}>
                {item.icon}
                <span className="text-xs whitespace-nowrap">{item.label}</span>
              </div>
              <div className={`flex-1 bg-gray-50 dark:bg-gray-800 px-2 py-1 text-gray-900 dark:text-gray-100 min-w-[100px]`}>
                <span className="text-xs">{item.value}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Right Column */}
        <div className="col-span-4 space-y-1">
          {rightColumn.map((item, index) => (
            <div key={index} className="flex">
              <div className={`flex items-center gap-2 bg-${theme}-600 text-white px-3 py-1 w-40`}>
                {item.icon}
                <span className="text-xs whitespace-nowrap">{item.label}</span>
              </div>
              <div className={`flex-1 bg-gray-50 dark:bg-gray-800 px-2 py-1 text-gray-900 dark:text-gray-100 min-w-[100px]`}>
                <span className="text-xs">{item.value}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Usage Stats Section */}
        <div className="col-span-3 space-y-6">
          {usageStats.map((stat, index) => (
            <div key={index}>
              <div className="flex justify-between mb-1">
                <div className={`text-xs text-${theme}-600 dark:text-${theme}-400 uppercase font-medium`}>{stat.label}</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-medium" style={{ color: stat.color }}>{stat.value}</span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{stat.subValue}</span>
                </div>
              </div>

              <div className="w-full bg-gray-100 dark:bg-gray-800 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full transition-all duration-300 bg-${theme}-600 dark:bg-${theme}-500`}
                  style={{ width: `${stat.width}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
