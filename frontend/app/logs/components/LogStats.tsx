'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface LogStatsProps {
  summary: {
    total_logs: number;
    total_errors: number;
    total_warnings: number;
    error_rate: number;
    warning_rate: number;
    trend_data: any[];
    top_categories: { category: string; total: number }[];
  };
}

export function LogStats({ summary }: LogStatsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{summary.total_logs}</div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-red-600">
            {summary.error_rate.toFixed(2)}%
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Warning Rate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-yellow-600">
            {summary.warning_rate.toFixed(2)}%
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Top Category</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {summary.top_categories[0]?.category || 'N/A'}
          </div>
        </CardContent>
      </Card>
      
      <Card className="col-span-full">
        <CardHeader>
          <CardTitle>Log Trend</CardTitle>
        </CardHeader>
        <CardContent className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={summary.trend_data}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="start_time" 
                tickFormatter={(time) => new Date(time).toLocaleDateString()}
              />
              <YAxis />
              <Tooltip 
                labelFormatter={(label) => new Date(label).toLocaleString()}
                formatter={(value: number) => [value, 'Count']}
              />
              <Line type="monotone" dataKey="total" stroke="#3b82f6" name="Total" />
              <Line type="monotone" dataKey="errors" stroke="#ef4444" name="Errors" />
              <Line type="monotone" dataKey="warnings" stroke="#f59e0b" name="Warnings" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
