import React from 'react';
import { Computer } from '@/types/computer';
import { useMetricsPolling } from '@/hooks/useMetricsPolling';
import { FaMemory, FaHdd, FaMicrochip, FaWindows, FaClock, FaDesktop, FaNetworkWired, FaUser } from 'react-icons/fa';

interface SystemOverviewProps {
  computer: Computer;
  token?: string;
}

export default function SystemOverview({ computer, token }: SystemOverviewProps) {
  // Polling for updates but using computer object directly since it has all the data
  useMetricsPolling(computer.id, token);

  // Format Windows version to just show Windows-10 or Windows-11
  const formatWindowsVersion = (version: string | undefined) => {
    if (!version) return 'Not Available';
    const match = version.match(/^(Windows-\d+)/);
    return match ? match[1] : version;
  };

  return (
    <div className="grid grid-cols-3 gap-8 p-4">
      {/* Left Column */}
      <div className="space-y-1">
        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaMicrochip size={12} />
            <span className="text-xs font-medium">CPU</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.metrics?.metrics?.cpu?.percent?.toFixed(1) || '0'}%</span>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaHdd size={12} />
            <span className="text-xs font-medium">DISK</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.disk_percent?.toFixed(1) || '0'}%</span>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaMemory size={12} />
            <span className="text-xs font-medium">MEMORY</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.memory_percent?.toFixed(1) || '0'}%</span>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaWindows size={12} />
            <span className="text-xs font-medium">OS</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{formatWindowsVersion(computer.metrics?.metrics?.system?.os_version)}</span>
          </div>
        </div>
      </div>

      {/* Middle Column */}
      <div className="space-y-1">
        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaClock size={12} />
            <span className="text-xs font-medium">UPTIME</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.metrics?.metrics?.system?.uptime || 'Not Available'}</span>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaDesktop size={12} />
            <span className="text-xs font-medium">DEVICE CLASS</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.metrics?.metrics?.system?.device_class || 'Not Available'}</span>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaNetworkWired size={12} />
            <span className="text-xs font-medium">IP ADDRESS</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.ip_address || 'No IP'}</span>
          </div>
        </div>

        <div className="flex items-center">
          <div className="bg-blue-600 text-white px-3 py-1.5 rounded-sm flex items-center gap-2 min-w-[90px]">
            <FaUser size={12} />
            <span className="text-xs font-medium">LOGGED IN USER</span>
          </div>
          <div className="bg-gray-100 flex-1 px-3 py-1.5 rounded-sm ml-1">
            <span className="text-xs">{computer.metrics?.metrics?.system?.logged_in_user || 'Not Available'}</span>
          </div>
        </div>
      </div>

      {/* Right Column */}
      <div className="space-y-8">
        <div>
          <div className="flex items-center mb-1">
            <div className="flex items-center gap-2">
              <FaMicrochip size={12} className="text-blue-600" />
              <span className="text-xs font-medium">CPU USAGE</span>
            </div>
            <div className="flex-1 text-right">
              <div className="flex items-center gap-3 justify-end">
                <span className="text-xs">{computer.metrics?.metrics?.cpu?.percent?.toFixed(1) || '0'}%</span>
                <span className="text-xs text-gray-500">{computer.metrics?.metrics?.cpu?.speed || '0'} GHz</span>
              </div>
            </div>
          </div>
          <div className="h-1.5 bg-blue-100 rounded-full overflow-hidden w-full">
            <div 
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${computer.metrics?.metrics?.cpu?.percent || 0}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex items-center mb-1">
            <div className="flex items-center gap-2">
              <FaMemory size={12} className="text-blue-600" />
              <span className="text-xs font-medium">MEMORY USAGE</span>
            </div>
            <div className="flex-1 text-right">
              <div className="flex items-center gap-3 justify-end">
                <span className="text-xs">{computer.memory_percent?.toFixed(1) || '0'}%</span>
                <span className="text-xs text-orange-500">{computer.memory_gb || '0'} GB</span>
              </div>
            </div>
          </div>
          <div className="h-1.5 bg-blue-100 rounded-full overflow-hidden w-full">
            <div 
              className="h-full bg-blue-600 transition-all duration-300"
              style={{ width: `${computer.memory_percent || 0}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
