import { Computer } from "@/lib/types";
import { ToolsNavigation } from "@/components/computers/ToolsNavigation";

interface ComputerDetailsProps {
  computer: Computer;
}

export function ComputerDetails({ computer }: ComputerDetailsProps) {
  // Get metrics data
  const cpuInfo = computer.metrics?.cpu || {};
  const systemInfo = computer.metrics?.system || {};

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-3 py-2 bg-[#4AB8DA] text-white">
        <h1 className="text-xs font-medium">{computer.label}</h1>
        <div className="flex items-center gap-1">
          <div className={`h-1.5 w-1.5 rounded-full ${computer.status === 'online' ? 'bg-green-400' : 'bg-red-400'}`} />
          <span className="text-[11px]">{computer.status === 'online' ? 'Online' : 'Offline'}</span>
        </div>
      </div>

      <ToolsNavigation computerId={computer.id} />

      <div className="flex-1 p-4 bg-gray-50">
        <div className="bg-white rounded shadow">
          <div className="p-4">
            <h2 className="text-xs font-medium mb-4">SYSTEM INFORMATION</h2>
            <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-xs">
              <div>
                <div className="text-gray-500">IP ADDRESS</div>
                <div>{computer.ip_address || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">MANUFACTURER</div>
                <div>{cpuInfo.manufacturer || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">CPU MODEL</div>
                <div>{computer.cpu_model || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">OPERATING SYSTEM</div>
                <div>{computer.os_version || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">DEVICE CLASS</div>
                <div>{computer.device_class || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">LOGGED IN USER</div>
                <div>{computer.logged_in_user || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">UPTIME</div>
                <div>{systemInfo.uptime || 'Not Available'}</div>
              </div>
              <div>
                <div className="text-gray-500">MEMORY</div>
                <div>
                  {computer.memory_total ? 
                    `${computer.memory_gb} (${computer.memory_percent}%)` : 
                    'Not Available'
                  }
                </div>
              </div>
              <div>
                <div className="text-gray-500">DISK</div>
                <div>
                  {computer.total_disk ? 
                    `${computer.disk_gb} (${computer.disk_percent}%)` : 
                    'Not Available'
                  }
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="bg-white rounded shadow p-4">
            <h2 className="text-xs font-medium mb-4">MEMORY UTILIZATION BY TOP 5 PROCESSES</h2>
            <div className="h-64 flex items-center justify-center text-gray-500 text-xs">
              Memory chart coming soon
            </div>
          </div>
          <div className="bg-white rounded shadow p-4">
            <h2 className="text-xs font-medium mb-4">RUNNING PROCESSES</h2>
            <div className="h-64 flex items-center justify-center text-gray-500 text-xs">
              Process list coming soon
            </div>
          </div>
        </div>

        <div className="mt-4 bg-white rounded shadow p-4">
          <h2 className="text-xs font-medium mb-4">System Metrics</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span>CPU Usage</span>
                <span>{computer.cpu_percent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${computer.cpu_percent}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span>Memory Usage</span>
                <span>{computer.memory_percent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${computer.memory_percent}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-[11px] mb-1">
                <span>Disk Usage</span>
                <span>{computer.disk_percent}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full" 
                  style={{ width: `${computer.disk_percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
