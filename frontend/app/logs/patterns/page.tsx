'use client';

import { useEffect, useState } from 'react';
import { fetchWithAuth } from '@/app/utils/api';
import { useToast } from '@/hooks/use-toast';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Loader2, Plus } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';

interface LogPattern {
  id: number;
  name: string;
  description: string;
  pattern_type: 'SEQUENCE' | 'THRESHOLD' | 'CORRELATION';
  conditions: any;
  alert_threshold: number;
  cooldown_minutes: number;
  enabled: boolean;
  created_at: string;
  last_triggered?: string;
}

export default function PatternsPage() {
  const [patterns, setPatterns] = useState<LogPattern[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const { toast } = useToast();

  const fetchPatterns = async () => {
    try {
      const data = await fetchWithAuth('/api/log-patterns/');
      setPatterns(data);
    } catch (error) {
      console.error('Failed to fetch patterns:', error);
      toast({
        title: 'Error',
        description: 'Failed to fetch log patterns',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatterns();
  }, []);

  const handleToggleEnabled = async (pattern: LogPattern) => {
    try {
      await fetchWithAuth(`/api/log-patterns/${pattern.id}/toggle_enabled/`, {
        method: 'POST',
      });
      fetchPatterns();
    } catch (error) {
      console.error('Failed to toggle pattern:', error);
      toast({
        title: 'Error',
        description: 'Failed to toggle pattern status',
        variant: 'destructive',
      });
    }
  };

  const handleCreatePattern = async (formData: FormData) => {
    try {
      const data = {
        name: formData.get('name'),
        description: formData.get('description'),
        pattern_type: formData.get('pattern_type'),
        conditions: JSON.parse(formData.get('conditions') as string),
        alert_threshold: parseInt(formData.get('alert_threshold') as string),
        cooldown_minutes: parseInt(formData.get('cooldown_minutes') as string),
        enabled: true,
      };

      await fetchWithAuth('/api/log-patterns/', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      setDialogOpen(false);
      fetchPatterns();
      toast({
        title: 'Success',
        description: 'Pattern created successfully',
      });
    } catch (error) {
      console.error('Failed to create pattern:', error);
      toast({
        title: 'Error',
        description: 'Failed to create pattern',
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
        <h1 className="text-3xl font-bold">Log Patterns</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              Create Pattern
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Log Pattern</DialogTitle>
            </DialogHeader>
            <form action={handleCreatePattern} className="space-y-4">
              <div className="space-y-2">
                <label>Name</label>
                <Input name="name" required />
              </div>
              <div className="space-y-2">
                <label>Description</label>
                <Textarea name="description" required />
              </div>
              <div className="space-y-2">
                <label>Pattern Type</label>
                <Select name="pattern_type" required>
                  <SelectTrigger>
                    <SelectValue placeholder="Select pattern type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="SEQUENCE">Event Sequence</SelectItem>
                    <SelectItem value="THRESHOLD">Threshold Based</SelectItem>
                    <SelectItem value="CORRELATION">Event Correlation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label>Conditions (JSON)</label>
                <Textarea name="conditions" required />
              </div>
              <div className="space-y-2">
                <label>Alert Threshold</label>
                <Input type="number" name="alert_threshold" defaultValue="1" required />
              </div>
              <div className="space-y-2">
                <label>Cooldown Minutes</label>
                <Input type="number" name="cooldown_minutes" defaultValue="60" required />
              </div>
              <Button type="submit">Create Pattern</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-4">
        {patterns.map((pattern) => (
          <Card key={pattern.id} className="p-6">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{pattern.name}</h3>
                <p className="text-sm text-muted-foreground mt-1">{pattern.description}</p>
              </div>
              <Switch
                checked={pattern.enabled}
                onCheckedChange={() => handleToggleEnabled(pattern)}
              />
            </div>
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium">Type</label>
                <p className="text-sm">{pattern.pattern_type}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Alert Threshold</label>
                <p className="text-sm">{pattern.alert_threshold}</p>
              </div>
              <div>
                <label className="text-sm font-medium">Cooldown</label>
                <p className="text-sm">{pattern.cooldown_minutes} minutes</p>
              </div>
              <div>
                <label className="text-sm font-medium">Last Triggered</label>
                <p className="text-sm">
                  {pattern.last_triggered
                    ? new Date(pattern.last_triggered).toLocaleString()
                    : 'Never'}
                </p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
