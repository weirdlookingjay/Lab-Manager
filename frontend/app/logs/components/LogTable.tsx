'use client';

import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { format } from 'date-fns';

interface Log {
  timestamp: string;
  message: string;
  level: string;
  category?: string;
  event?: string;
}

interface LogTableProps {
  logs: Log[];
  title: string;
}

export function LogTable({ logs, title }: LogTableProps) {
  const getLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'ERROR':
        return 'bg-red-500';
      case 'WARNING':
        return 'bg-yellow-500';
      case 'INFO':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm">
      <div className="p-6">
        <h3 className="text-lg font-semibold">{title}</h3>
        <ScrollArea className="h-[400px] w-full">
          <div className="space-y-4">
            {logs.map((log, index) => (
              <div
                key={index}
                className="flex flex-col space-y-2 rounded-lg border p-4 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Badge className={getLevelColor(log.level)}>
                      {log.level}
                    </Badge>
                    {log.category && (
                      <Badge variant="outline">{log.category}</Badge>
                    )}
                    {log.event && (
                      <Badge variant="outline">{log.event}</Badge>
                    )}
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {format(new Date(log.timestamp), 'PPpp')}
                  </span>
                </div>
                <p className="text-sm">{log.message}</p>
              </div>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
