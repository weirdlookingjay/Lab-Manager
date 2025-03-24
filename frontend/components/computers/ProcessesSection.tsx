"use client";

import { Computer, Process, MemoryUtilization } from "@/lib/types";
import { useEffect, useRef } from "react";
import { Chart } from "chart.js/auto";

interface ProcessesSectionProps {
  computer: Computer;
}

export function ProcessesSection({ computer }: ProcessesSectionProps) {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const chartInstance = useRef<Chart | null>(null);

  useEffect(() => {
    if (!chartRef.current || !computer?.memory_utilization_history?.length) return;

    // Destroy existing chart
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current?.getContext('2d');
    if (!ctx) return;

    const memoryData = computer.memory_utilization_history.map((point: MemoryUtilization) => ({
      timestamp: point.timestamp,
      values: point.values || [0, 0, 0, 0, 0]
    }));

    chartInstance.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: memoryData.map(point => point.timestamp),
        datasets: memoryData[0].values?.map((_, i) => ({
          label: `Process ${i + 1}`,
          data: memoryData.map(point => point.values?.[i] || 0),
          backgroundColor: i === 0 ? '#60A5FA' : '#F59E0B',
          stack: 'stack',
          barPercentage: 0.9,
          categoryPercentage: 0.9,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: {
            stacked: true,
            grid: {
              display: false,
            },
            ticks: {
              font: {
                size: 10,
              },
              maxRotation: 0,
            },
          },
          y: {
            stacked: true,
            grid: {
              color: '#E5E7EB',
            },
            ticks: {
              font: {
                size: 10,
              },
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [computer?.memory_utilization_history]);

  const processes = computer?.running_processes || [];

  return (
    <div className="grid grid-cols-2 gap-4">
      <div className="bg-white rounded shadow">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-medium">MEMORY UTILIZATION BY TOP 5 PROCESSES</h2>
            <button className="text-xs text-blue-500">▼</button>
          </div>
          <div className="h-64">
            <canvas ref={chartRef} />
          </div>
        </div>
      </div>

      <div className="bg-white rounded shadow">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs font-medium">RUNNING PROCESSES</h2>
            <button className="text-xs text-blue-500">▼</button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 font-medium">Name ▼</th>
                  <th className="text-left py-2 font-medium">Platform ▼</th>
                  <th className="text-left py-2 font-medium">Process ID ▼</th>
                  <th className="text-left py-2 font-medium">CPU ▼</th>
                  <th className="text-left py-2 font-medium">Memory (private working set) ▼</th>
                  <th className="text-left py-2 font-medium">Memory (physical) ▼</th>
                  <th className="text-left py-2 font-medium">Memory (paged) ▼</th>
                </tr>
              </thead>
              <tbody>
                {processes.map((process, index) => (
                  <tr key={index} className="border-b last:border-0">
                    <td className="py-2">{process?.name || 'Unknown'}</td>
                    <td className="py-2">{process?.platform || 'Unknown'}</td>
                    <td className="py-2">{process?.process_id || 'Unknown'}</td>
                    <td className="py-2">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-green-500 rounded-full" 
                            style={{ width: `${process?.cpu || 0}%` }}
                          />
                        </div>
                        <span>{process?.cpu || 0}%</span>
                      </div>
                    </td>
                    <td className="py-2">{process?.memory_private_working_set || '0'}</td>
                    <td className="py-2">{process?.memory_physical || '0'}</td>
                    <td className="py-2">{process?.memory_paged || '0'}</td>
                  </tr>
                ))}
                {processes.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-4 text-center text-gray-500">
                      No processes running
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
