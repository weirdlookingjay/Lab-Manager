'use client';

import { useEffect, useState } from 'react';
import { fetchWithAuth } from '@/app/utils/api';
import { useToast } from '@/hooks/use-toast';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { format } from 'date-fns';
import { Slider } from '@/components/ui/slider';

interface Log {
  timestamp: string;
  message: string;
  level: string;
  category?: string;
  event?: string;
}

interface LogCorrelation {
  id: number;
  correlation_id: string;
  correlation_type: string;
  confidence_score: number;
  created_at: string;
  primary_log: Log;
  related_logs: Log[];
}

export default function CorrelationsPage() {
  const [correlations, setCorrelations] = useState<LogCorrelation[]>([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    correlation_type: 'ALL',
    min_confidence: 0.5,
  });
  const { toast } = useToast();

  const fetchCorrelations = async () => {
    try {
      const params = new URLSearchParams();
      if (filters.correlation_type && filters.correlation_type !== 'ALL') {
        params.append('correlation_type', filters.correlation_type);
      }
      params.append('min_confidence', filters.min_confidence.toString());

      const data = await fetchWithAuth(`/api/log-correlations/?${params.toString()}`);
      setCorrelations(data);
    } catch (error) {
      console.error('Failed to fetch correlations:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch log correlations',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCorrelations();
  }, [filters]);

  const getCorrelationTypeLabel = (type: string) => {
    switch (type) {
      case 'AUTH_FILE_ACCESS':
        return 'Authentication → File Access';
      case 'SCAN_LIFECYCLE':
        return 'Scan Lifecycle';
      default:
        return type;
    }
  };

  if (loading) {
    return (
      <div className="flex h-[200px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Log Correlations</h1>
      </div>

      <Card className="p-6">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm font-medium">Correlation Type</label>
            <Select
              value={filters.correlation_type}
              onValueChange={(value) =>
                setFilters((prev) => ({ ...prev, correlation_type: value }))
              }
            >
              <SelectTrigger>
                <SelectValue placeholder="All types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All types</SelectItem>
                <SelectItem value="AUTH_FILE_ACCESS">Authentication → File Access</SelectItem>
                <SelectItem value="SCAN_LIFECYCLE">Scan Lifecycle</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Minimum Confidence: {(filters.min_confidence * 100).toFixed(0)}%
            </label>
            <Slider
              value={[filters.min_confidence]}
              onValueChange={([value]) =>
                setFilters((prev) => ({ ...prev, min_confidence: value }))
              }
              min={0}
              max={1}
              step={0.1}
            />
          </div>
        </div>
      </Card>

      <div className="grid gap-4">
        {correlations.map((correlation) => (
          <Card key={correlation.id} className="p-6">
            <div className="space-y-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-lg font-semibold">
                    {getCorrelationTypeLabel(correlation.correlation_type)}
                  </h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Detected at {format(new Date(correlation.created_at), 'PPpp')}
                  </p>
                </div>
                <Badge
                  className={
                    correlation.confidence_score >= 0.8
                      ? 'bg-green-100 text-green-800'
                      : correlation.confidence_score >= 0.5
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }
                >
                  {(correlation.confidence_score * 100).toFixed(0)}% confidence
                </Badge>
              </div>

              <div className="space-y-2">
                <div className="bg-muted p-3 rounded-md">
                  <div className="text-sm font-medium mb-2">Primary Event</div>
                  <div className="flex items-center space-x-2">
                    <Badge>{correlation.primary_log.level}</Badge>
                    {correlation.primary_log.category && (
                      <Badge variant="outline">{correlation.primary_log.category}</Badge>
                    )}
                    {correlation.primary_log.event && (
                      <Badge variant="outline">{correlation.primary_log.event}</Badge>
                    )}
                    <span className="text-sm text-muted-foreground">
                      {format(new Date(correlation.primary_log.timestamp), 'PPpp')}
                    </span>
                  </div>
                  <p className="text-sm mt-1">{correlation.primary_log.message}</p>
                </div>

                <div className="pl-4 border-l-2 border-muted space-y-2">
                  <div className="text-sm font-medium">Related Events</div>
                  {correlation.related_logs.map((log, index) => (
                    <div key={index} className="bg-muted p-3 rounded-md">
                      <div className="flex items-center space-x-2">
                        <Badge>{log.level}</Badge>
                        {log.category && <Badge variant="outline">{log.category}</Badge>}
                        {log.event && <Badge variant="outline">{log.event}</Badge>}
                        <span className="text-sm text-muted-foreground">
                          {format(new Date(log.timestamp), 'PPpp')}
                        </span>
                      </div>
                      <p className="text-sm mt-1">{log.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
