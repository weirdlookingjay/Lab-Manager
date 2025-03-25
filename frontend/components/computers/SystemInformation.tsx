import React from 'react';
import { Computer } from '@/types/computer';
import { 
  BsClock, BsCalendar3, BsBuilding, 
  BsMemory, BsBox, BsGlobe,
  BsCpu, BsWindows, BsLaptop
} from 'react-icons/bs';

interface SystemInformationProps {
  computer: Computer;
}

export default function SystemInformation({ computer }: SystemInformationProps) {
  const metrics = [
    {
      label: 'LAST DISCOVERY',
      value: computer.last_metrics_update || 'Never',
      icon: <BsCalendar3 className="text-blue-600" size={16} />
    },
    {
      label: 'IP ADDRESS',
      value: computer.ip_address || 'Not Available',
      icon: <BsGlobe className="text-blue-600" size={16} />
    },
    {
      label: 'MANUFACTURER',
      value: computer.metrics?.metrics?.cpu?.manufacturer || 'Not Available',
      icon: <BsBuilding className="text-blue-600" size={16} />
    },
    {
      label: 'MEMORY',
      value: computer.memory_gb || '0 GB',
      icon: <BsMemory className="text-blue-600" size={16} />
    },
    {
      label: 'OPERATING SYSTEM',
      value: computer.metrics?.metrics?.system?.os_version || 'Not Available',
      icon: <BsWindows className="text-blue-600" size={16} />
    },
    {
      label: 'CPU USAGE',
      value: `${computer.metrics?.metrics?.cpu?.percent?.toFixed(1) || '0'}%`,
      icon: <BsCpu className="text-blue-600" size={16} />
    },
    {
      label: 'UPTIME',
      value: computer.metrics?.metrics?.system?.uptime || 'Not Available',
      icon: <BsClock className="text-blue-600" size={16} />
    }
  ];

  const rightMetrics = [
    {
      label: 'SYSTEM NAME',
      value: computer.hostname || 'Not Available',
      icon: <BsLaptop className="text-blue-600" size={16} />
    },
    {
      label: 'CLASS',
      value: computer.metrics?.metrics?.system?.device_class || 'Not Available',
      icon: <BsBox className="text-blue-600" size={16} />
    },
    {
      label: 'ARCHITECTURE',
      value: computer.metrics?.metrics?.cpu?.architecture || 'Not Available',
      icon: <BsCpu className="text-blue-600" size={16} />
    },
    {
      label: 'MODEL',
      value: computer.metrics?.metrics?.cpu?.model || 'Not Available',
      icon: <BsCpu className="text-blue-600" size={16} />
    },
    {
      label: 'DISK',
      value: `${computer.disk_gb || '0'} / ${computer.total_disk ? (computer.total_disk / (1024 * 1024 * 1024)).toFixed(1) : '0'} GB`,
      icon: <BsMemory className="text-blue-600" size={16} />
    },
    {
      label: 'CPU',
      value: computer.metrics?.metrics?.cpu?.model || 'Not Available',
      icon: <BsCpu className="text-blue-600" size={16} />
    },
    {
      label: 'AGENT STATUS',
      value: computer.status || 'offline',
      icon: <div className={`h-4 w-4 rounded-full ${computer.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
    }
  ];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4">System Information</h2>
      <div className="grid grid-cols-12 gap-8">
        <div className="col-span-6">
          <div className="space-y-4">
            {metrics.map((metric, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className="mt-0.5">{metric.icon}</div>
                <div>
                  <div className="text-xs text-gray-500 font-medium">{metric.label}</div>
                  <div className="text-sm text-gray-900">{metric.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="col-span-6">
          <div className="space-y-4">
            {rightMetrics.map((metric, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className="mt-0.5">{metric.icon}</div>
                <div>
                  <div className="text-xs text-gray-500 font-medium">{metric.label}</div>
                  <div className="text-sm text-gray-900">{metric.value}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
