'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import { useState } from 'react';

interface LogFiltersProps {
  onFilterChange: (filters: {
    period?: string;
    level?: string;
    category?: string;
    startDate?: Date;
    endDate?: Date;
  }) => void;
}

export function LogFilters({ onFilterChange }: LogFiltersProps) {
  const [startDate, setStartDate] = useState<Date>();
  const [endDate, setEndDate] = useState<Date>();

  return (
    <div className="flex flex-wrap gap-4 mb-6">
      <Select
        onValueChange={(value) =>
          onFilterChange({ period: value })
        }
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select period" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="HOUR">Hourly</SelectItem>
          <SelectItem value="DAY">Daily</SelectItem>
          <SelectItem value="WEEK">Weekly</SelectItem>
          <SelectItem value="MONTH">Monthly</SelectItem>
        </SelectContent>
      </Select>

      <Select
        onValueChange={(value) =>
          onFilterChange({ level: value })
        }
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select level" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="INFO">Info</SelectItem>
          <SelectItem value="WARNING">Warning</SelectItem>
          <SelectItem value="ERROR">Error</SelectItem>
        </SelectContent>
      </Select>

      <Select
        onValueChange={(value) =>
          onFilterChange({ category: value })
        }
      >
        <SelectTrigger className="w-[180px]">
          <SelectValue placeholder="Select category" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="COMPUTER_STATUS">Computer Status</SelectItem>
          <SelectItem value="FILE_SCAN">File Scan</SelectItem>
          <SelectItem value="FILE_ACCESS">File Access</SelectItem>
          <SelectItem value="SYSTEM">System</SelectItem>
          <SelectItem value="AUTH">Authentication</SelectItem>
        </SelectContent>
      </Select>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-[180px] justify-start text-left font-normal">
            <CalendarIcon className="mr-2 h-4 w-4" />
            {startDate ? format(startDate, 'PPP') : 'Start date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0">
          <Calendar
            mode="single"
            selected={startDate}
            onSelect={(date) => {
              setStartDate(date);
              onFilterChange({ startDate: date });
            }}
            initialFocus
          />
        </PopoverContent>
      </Popover>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" className="w-[180px] justify-start text-left font-normal">
            <CalendarIcon className="mr-2 h-4 w-4" />
            {endDate ? format(endDate, 'PPP') : 'End date'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0">
          <Calendar
            mode="single"
            selected={endDate}
            onSelect={(date) => {
              setEndDate(date);
              onFilterChange({ endDate: date });
            }}
            initialFocus
          />
        </PopoverContent>
      </Popover>
    </div>
  );
}
