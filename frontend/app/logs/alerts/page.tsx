'use client';

import { useEffect, useState } from 'react';
import { fetchWithAuth } from '@/app/utils/api';
import { useToast } from '@/hooks/use-toast';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, Bell, Check } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { format } from 'date-fns';

interface LogAlert {
  id: number;
  pattern_name: string;
  triggered_at: string;
  details: any;
  acknowledged: boolean;
  acknowledged_by_username?: string;
  acknowledged_at?: string;
  matched_logs: Array<{
    timestamp: string;
    message: string;
    level: string;
    category?: string;
    event?: string;
  }>;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<LogAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<LogAlert | null>(null);
  const { toast } = useToast();

  const fetchAlerts = async () => {
    try {
      const data = await fetchWithAuth('/api/log-alerts/');
      setAlerts(data);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch log alerts',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    // Poll for new alerts every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await fetchWithAuth(`/api/log-alerts/${alertId}/acknowledge/`, {
        method: 'POST',
      });
      fetchAlerts();
      toast({
        title: 'Success',
        description: 'Alert acknowledged',
      });
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
      toast({
        title: 'Error',
        description: 'Failed to acknowledge alert',
        variant: 'destructive',
      });
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
        <h1 className="text-3xl font-bold">Log Alerts</h1>
      </div>

      <div className="grid gap-4">
        {alerts.map((alert) => (
          <Card key={alert.id} className="p-6">
            <div className="flex justify-between items-start">
              <div className="flex items-start space-x-4">
                <div className={`p-2 rounded-full ${alert.acknowledged ? 'bg-green-100' : 'bg-yellow-100'}`}>
                  {alert.acknowledged ? (
                    <Check className="h-5 w-5 text-green-600" />
                  ) : (
                    <Bell className="h-5 w-5 text-yellow-600" />
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-semibold">{alert.pattern_name}</h3>
                  <p className="text-sm text-muted-foreground mt-1">
                    Triggered at {format(new Date(alert.triggered_at), 'PPpp')}
                  </p>
                  {alert.acknowledged && (
                    <p className="text-sm text-muted-foreground">
                      Acknowledged by {alert.acknowledged_by_username} at{' '}
                      {format(new Date(alert.acknowledged_at!), 'PPpp')}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex space-x-2">
                <Dialog>
                  <DialogTrigger asChild>
                    <Button variant="outline" onClick={() => setSelectedAlert(alert)}>
                      View Details
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-w-2xl">
                    <DialogHeader>
                      <DialogTitle>Alert Details</DialogTitle>
                    </DialogHeader>
                    <ScrollArea className="h-[400px]">
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium">Pattern</h4>
                          <p>{alert.pattern_name}</p>
                        </div>
                        <div>
                          <h4 className="font-medium">Details</h4>
                          <pre className="bg-muted p-2 rounded-md text-sm mt-1">
                            {JSON.stringify(alert.details, null, 2)}
                          </pre>
                        </div>
                        <div>
                          <h4 className="font-medium">Matched Logs</h4>
                          <div className="space-y-2 mt-2">
                            {alert.matched_logs.map((log, index) => (
                              <div
                                key={index}
                                className="bg-muted p-3 rounded-md text-sm space-y-1"
                              >
                                <div className="flex items-center space-x-2">
                                  <Badge>{log.level}</Badge>
                                  {log.category && <Badge variant="outline">{log.category}</Badge>}
                                  {log.event && <Badge variant="outline">{log.event}</Badge>}
                                  <span className="text-muted-foreground">
                                    {format(new Date(log.timestamp), 'PPpp')}
                                  </span>
                                </div>
                                <p>{log.message}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </ScrollArea>
                  </DialogContent>
                </Dialog>
                {!alert.acknowledged && (
                  <Button onClick={() => handleAcknowledge(alert.id)}>
                    Acknowledge
                  </Button>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
