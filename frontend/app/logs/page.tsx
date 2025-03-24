'use client';

import { useEffect, useState } from 'react';
import { fetchWithAuth } from '@/app/utils/api';
import { useToast } from '@/hooks/use-toast';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LogTable } from './components/LogTable';
import { LogFilters } from './components/LogFilters';
import { Loader2, AlertTriangle, AlertOctagon, Clock, HourglassIcon, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface Log {
  timestamp: string;
  message: string;
  level: string;
  category?: string;
  event?: string;
}

interface LogSummary {
  total_logs: number;
  error_count: number;
  warning_count: number;
  critical_count: number;
  pending_count: number;
  overdue_count: number;
  activity_data: Array<{
    date: string;
    resolved: number;
    opened: number;
  }>;
  computer_status: {
    up_to_date: number;
    total: number;
  };
}

export default function LogsPage() {
  const [logs, setLogs] = useState<Log[]>([]);
  const [summary, setSummary] = useState<LogSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch logs and summary data
      const [logsData, summaryData] = await Promise.all([
        fetchWithAuth('/api/logs/'),
        fetchWithAuth('/api/logs/summary/')
      ]);

      setLogs(logsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch logs',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && !logs.length) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Top Stats */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <Card className="p-4 flex flex-col items-center">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            <span className="text-sm text-muted-foreground">Warning alerts</span>
          </div>
          <span className="text-2xl font-bold mt-2">{summary?.warning_count || 0}</span>
        </Card>
        <Card className="p-4 flex flex-col items-center">
          <div className="flex items-center space-x-2">
            <AlertOctagon className="h-5 w-5 text-red-500" />
            <span className="text-sm text-muted-foreground">Critical alerts</span>
          </div>
          <span className="text-2xl font-bold mt-2">{summary?.critical_count || 0}</span>
        </Card>
        <Card className="p-4 flex flex-col items-center">
          <div className="flex items-center space-x-2">
            <AlertCircle className="h-5 w-5 text-blue-500" />
            <span className="text-sm text-muted-foreground">Open tickets</span>
          </div>
          <span className="text-2xl font-bold mt-2">{summary?.total_logs || 0}</span>
        </Card>
        <Card className="p-4 flex flex-col items-center">
          <div className="flex items-center space-x-2">
            <HourglassIcon className="h-5 w-5 text-orange-500" />
            <span className="text-sm text-muted-foreground">Pending tickets</span>
          </div>
          <span className="text-2xl font-bold mt-2">{summary?.pending_count || 0}</span>
        </Card>
        <Card className="p-4 flex flex-col items-center">
          <div className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-purple-500" />
            <span className="text-sm text-muted-foreground">Due today</span>
          </div>
          <span className="text-2xl font-bold mt-2">3</span>
        </Card>
        <Card className="p-4 flex flex-col items-center">
          <div className="flex items-center space-x-2">
            <AlertOctagon className="h-5 w-5 text-red-700" />
            <span className="text-sm text-muted-foreground">Overdue</span>
          </div>
          <span className="text-2xl font-bold mt-2">{summary?.overdue_count || 0}</span>
        </Card>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Recent Alerts */}
        <Card className="col-span-1">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
            <div className="space-y-4">
              {logs.slice(0, 3).map((log, index) => (
                <div key={index} className="flex items-start space-x-3">
                  {log.level === 'CRITICAL' ? (
                    <AlertOctagon className="h-5 w-5 text-red-500 mt-1" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-yellow-500 mt-1" />
                  )}
                  <div>
                    <p className="text-sm font-medium">{log.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </Card>

        {/* Ticket Activity */}
        <Card className="col-span-1">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Ticket Activity</h3>
            <div className="h-[200px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={summary?.activity_data || []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="opened" stroke="#8884d8" name="Opened" />
                  <Line type="monotone" dataKey="resolved" stroke="#82ca9d" name="Resolved" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>

        {/* Status Summary */}
        <Card className="col-span-1">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">Computer Status</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm font-medium">Computers</span>
                  <span className="text-sm text-muted-foreground">
                    {summary?.computer_status.up_to_date || 0}/{summary?.computer_status.total || 0}
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500"
                    style={{
                      width: `${((summary?.computer_status.up_to_date || 0) / (summary?.computer_status.total || 1)) * 100}%`
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Log Table */}
      <Card>
        <Tabs defaultValue="real-time" className="p-6">
          <div className="flex justify-between items-center mb-6">
            <TabsList>
              <TabsTrigger value="real-time">Real-time Logs</TabsTrigger>
              <TabsTrigger value="aggregated">Aggregated Logs</TabsTrigger>
            </TabsList>
            <div className="flex space-x-4">
              <Button variant="outline" asChild>
                <Link href="/logs/patterns">Manage Patterns</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/logs/alerts">View Alerts</Link>
              </Button>
              <Button variant="outline" asChild>
                <Link href="/logs/correlations">View Correlations</Link>
              </Button>
            </div>
          </div>

          <LogFilters onFilterChange={() => {}} />

          <TabsContent value="real-time" className="mt-6">
            <LogTable logs={logs} title="Real-time System Logs" />
          </TabsContent>

          <TabsContent value="aggregated" className="mt-6">
            <LogTable logs={logs} title="Aggregated System Logs" />
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
