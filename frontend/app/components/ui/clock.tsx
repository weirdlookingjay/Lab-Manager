'use client';

import * as React from 'react';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { cn } from '@/lib/utils';

interface ClockProps {
  value: Date;
  onChange: (date: Date) => void;
  className?: string;
}

export function Clock({ value, onChange, className }: ClockProps) {
  const hours = value.getHours();
  const minutes = value.getMinutes();

  const handleHourChange = (hour: string) => {
    const newDate = new Date(value);
    newDate.setHours(parseInt(hour));
    onChange(newDate);
  };

  const handleMinuteChange = (minute: string) => {
    const newDate = new Date(value);
    newDate.setMinutes(parseInt(minute));
    onChange(newDate);
  };

  return (
    <div className={cn('flex items-end gap-2', className)}>
      <div className="grid gap-1.5">
        <Label>Hour</Label>
        <Select value={hours.toString()} onValueChange={handleHourChange}>
          <SelectTrigger className="w-[70px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Array.from({ length: 24 }, (_, i) => (
              <SelectItem key={i} value={i.toString()}>
                {i.toString().padStart(2, '0')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="grid gap-1.5">
        <Label>Minute</Label>
        <Select value={minutes.toString()} onValueChange={handleMinuteChange}>
          <SelectTrigger className="w-[70px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Array.from({ length: 60 }, (_, i) => (
              <SelectItem key={i} value={i.toString()}>
                {i.toString().padStart(2, '0')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
