'use client';

import { useState, useEffect } from 'react';
import { Calendar } from '@/components/ui/calendar';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { format } from 'date-fns';
import { CalendarIcon, Clock as ClockIcon, Loader2, Mail, X } from 'lucide-react';
import { getComputers, deleteScanSchedule, type Computer, type ScanSchedule } from '@/app/utils/api';
import { toast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

interface ScheduleSettingsProps {
  open: boolean;
  onClose: () => void;
  schedule?: ScanSchedule;
  onSubmit: (schedule: ScanSchedule) => Promise<void>;
  computers: Computer[];
  selectedComputers: string[];
  onComputerSelectionChange: (computers: string[]) => void;
  selected_days?: number[];
  setSelectedDays: (days: number[]) => void;
  monthlyDate?: string;
  setMonthlyDate: (date: string | undefined) => void;
  scheduleType: 'daily' | 'weekly' | 'monthly';
  setScheduleType: (type: 'daily' | 'weekly' | 'monthly') => void;
  scheduleTime: string;
  setScheduleTime: (time: string) => void;
  scheduleEnabled: boolean;
  setScheduleEnabled: (enabled: boolean) => void;
  email_notification: boolean;
  setEmailNotification: (enabled: boolean) => void;
  email_addresses: string[];
  setEmailAddresses: (emails: string[]) => void;
  mutateSchedule: () => void;
}

export function ScheduleSettings({
  open,
  onClose,
  schedule,
  onSubmit,
  computers,
  selectedComputers,
  onComputerSelectionChange,
  selected_days,
  setSelectedDays,
  monthlyDate,
  setMonthlyDate,
  scheduleType,
  setScheduleType,
  scheduleTime,
  setScheduleTime,
  scheduleEnabled,
  setScheduleEnabled,
  email_notification,
  setEmailNotification,
  email_addresses,
  setEmailAddresses,
  mutateSchedule
}: ScheduleSettingsProps) {
  const [newEmail, setNewEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    const loadComputers = async () => {
      try {
        const data = await getComputers();
        computers = data;
      } catch (error) {
        console.error('Error loading computers:', error);
      } finally {
        setLoading(false);
      }
    };

    loadComputers();
  }, []);

  useEffect(() => {
    if (schedule && open) { 
      console.log('Initializing selected computers from schedule:', schedule);
      const computerIds = schedule.computer_ids || 
        (schedule.computers?.map(c => c.id.toString()) || []);
      console.log('Setting selected computers to:', computerIds);
      onComputerSelectionChange(computerIds.map(id => id.toString()));

      setScheduleTime(schedule.time || '');
      setScheduleType(schedule.type || 'daily');
      setSelectedDays(schedule.selected_days || []);
      setMonthlyDate(schedule.monthly_date);
      setScheduleEnabled(schedule.enabled || false);
      setEmailNotification(schedule.email_notification || false);
      setEmailAddresses(schedule.email_addresses || []);
    } else if (!open) { 
      onComputerSelectionChange([]);
    }
  }, [schedule, open]);

  const handleEmailAdd = () => {
    if (newEmail && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newEmail)) {
      setEmailAddresses([...email_addresses, newEmail]);
      setNewEmail('');
    }
  };

  const handleEmailRemove = (email: string) => {
    setEmailAddresses(email_addresses.filter(e => e !== email));
  };

  const handleComputerToggle = (computerId: string) => {
    console.log('Toggling computer:', computerId);
    console.log('Current selected computers:', selectedComputers);
    
    const currentSelected = selectedComputers || [];
    const newSelected = currentSelected.includes(computerId)
      ? currentSelected.filter(id => id !== computerId)
      : [...currentSelected, computerId];
    
    console.log('New selected computers:', newSelected);
    onComputerSelectionChange(newSelected);
  };

  const weekDays = [
    { value: 0, label: 'Sunday' },
    { value: 1, label: 'Monday' },
    { value: 2, label: 'Tuesday' },
    { value: 3, label: 'Wednesday' },
    { value: 4, label: 'Thursday' },
    { value: 5, label: 'Friday' },
    { value: 6, label: 'Saturday' }
  ];

  const handleDelete = async () => {
    if (!schedule?.id) return;
    
    try {
      setLoading(true);
      await deleteScanSchedule(schedule.id);
      toast({
        title: 'Success',
        description: 'Schedule deleted successfully',
      });
      // Reset computer selection after deleting
      onComputerSelectionChange([]);
      mutateSchedule();
      onClose();
      setShowDeleteConfirm(false);
    } catch (error) {
      console.error('Error deleting schedule:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete schedule',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteConfirm(true);
  };

  const handleDeleteCancel = () => {
    setShowDeleteConfirm(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const scheduleData: ScanSchedule = {
        type: scheduleType,
        time: scheduleTime,
        enabled: scheduleEnabled,
        email_notification: email_notification,
        email_addresses: email_addresses,
        selected_days: scheduleType === 'weekly' ? selected_days || [] : [],
        monthly_date: scheduleType === 'monthly' ? monthlyDate : undefined,
        computer_ids: selectedComputers.map(id => parseInt(id, 10))
      };

      if (schedule?.id) {
        scheduleData.id = schedule.id;
      }

      await onSubmit(scheduleData);
      
      if (!schedule) { 
        onComputerSelectionChange([]);
        setSelectedDays([]);
        setMonthlyDate(undefined);
        setScheduleTime('09:00');
        setEmailNotification(false);
        setEmailAddresses([]);
      }
      
      onClose();
    } catch (error) {
      console.error('Error saving schedule:', error);
      toast({
        title: 'Error',
        description: 'Failed to save schedule',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const showDeleteButton = !!schedule?.id;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{schedule ? 'Edit Schedule' : 'Create New Schedule'}</DialogTitle>
          <DialogDescription>Configure your scan schedule settings</DialogDescription>
        </DialogHeader>
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-medium mb-2">Schedule Type</h2>
            <RadioGroup
              value={scheduleType}
              onValueChange={(value: 'daily' | 'weekly' | 'monthly') => setScheduleType(value)}
              className="flex gap-4"
            >
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="daily" id="daily" />
                <Label htmlFor="daily">Daily</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="weekly" id="weekly" />
                <Label htmlFor="weekly">Weekly</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="monthly" id="monthly" />
                <Label htmlFor="monthly">Monthly</Label>
              </div>
            </RadioGroup>
          </div>

          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Switch
                id="scheduleEnabled"
                checked={scheduleEnabled}
                onCheckedChange={setScheduleEnabled}
              />
              <Label htmlFor="scheduleEnabled">Enable Schedule</Label>
            </div>
          </div>

          <div>
            <h2 className="text-lg font-medium mb-2">Time</h2>
            <Input
              type="time"
              value={scheduleTime || ''}
              onChange={(e) => setScheduleTime(e.target.value)}
            />
          </div>

          <div>
            <h2 className="text-lg font-medium mb-2">Select Computers</h2>
            <div className="grid grid-cols-3 gap-2">
              {computers.map((computer) => {
                const isSelected = selectedComputers?.includes(computer.id.toString());
                console.log('Computer:', computer.id, 'Selected:', isSelected);
                return (
                  <div key={computer.id} className="flex items-center space-x-2">
                    <Checkbox
                      id={`computer-${computer.id}`}
                      checked={isSelected}
                      onCheckedChange={() => handleComputerToggle(computer.id.toString())}
                    />
                    <Label 
                      htmlFor={`computer-${computer.id}`}
                      className={cn(computer.status === 'online' ? 'text-green-600' : 'text-gray-500')}
                    >
                      {computer.name} ({computer.label})
                    </Label>
                  </div>
                );
              })}
            </div>
          </div>

          {scheduleType === 'weekly' && (
            <div>
              <h2 className="text-lg font-medium mb-2">Days of Week</h2>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {weekDays.map((day) => (
                  <div key={day.value} className="flex items-center space-x-2">
                    <Checkbox
                      id={`day-${day.value}`}
                      checked={selected_days?.includes(day.value) ?? false}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedDays([...(selected_days ?? []), day.value]);
                        } else {
                          setSelectedDays((selected_days ?? []).filter(d => d !== day.value));
                        }
                      }}
                    />
                    <Label htmlFor={`day-${day.value}`}>{day.label}</Label>
                  </div>
                ))}
              </div>
            </div>
          )}

          {scheduleType === 'monthly' && (
            <div>
              <h2 className="text-lg font-medium mb-2">Day of Month</h2>
              <div className="flex gap-2">
                <Input
                  type="number"
                  min="1"
                  max="31"
                  value={monthlyDate || ''}
                  onChange={(e) => {
                    const day = parseInt(e.target.value);
                    if (day >= 1 && day <= 31) {
                      setMonthlyDate(day.toString());
                    } else {
                      setMonthlyDate(undefined);
                    }
                  }}
                />
              </div>
            </div>
          )}

          <div>
            <div className="flex items-center space-x-2 mb-4">
              <Switch
                id="emailNotification"
                checked={email_notification}
                onCheckedChange={setEmailNotification}
              />
              <Label htmlFor="emailNotification">Email Notifications</Label>
            </div>

            {email_notification && (
              <div className="space-y-4">
                <h2 className="text-lg font-medium">Email Addresses</h2>
                <div className="flex gap-2">
                  <Input
                    id="email"
                    type="email"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="Enter email address"
                  />
                  <Button variant="default" onClick={handleEmailAdd}>Add</Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {email_addresses.map((email) => (
                    <Badge key={email} variant="secondary" className="flex items-center gap-1">
                      {email}
                      <button
                        onClick={() => handleEmailRemove(email)}
                        className="ml-1 hover:bg-destructive/20 rounded-full p-1"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-between mt-4">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <div className="flex gap-2">
              {showDeleteButton && (
                <Button 
                  variant="destructive" 
                  onClick={() => setShowDeleteConfirm(true)}
                  disabled={loading}
                >
                  Delete Schedule
                </Button>
              )}
              <Button onClick={handleSubmit}>Save Changes</Button>
            </div>
          </div>
        </div>
      </DialogContent>
      
      {/* Delete Confirmation Modal */}
      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Schedule</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this scan schedule? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={loading}>Cancel</AlertDialogCancel>
            <AlertDialogAction 
              onClick={handleDelete}
              disabled={loading}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Deleting...
                </>
              ) : (
                'Delete'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </Dialog>
  );
}
