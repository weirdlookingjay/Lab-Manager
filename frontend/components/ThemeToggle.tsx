'use client';

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Palette, Sun, Moon } from "lucide-react";
import { useTheme } from "@/hooks/useTheme";

const themes = [
  { 
    name: 'blue', 
    label: 'Blue Theme',
    color: 'rgb(59 130 246)',
    textColor: 'white'
  },
  { 
    name: 'purple', 
    label: 'Purple Theme',
    color: 'rgb(147 51 234)',
    textColor: 'white'
  },
  { 
    name: 'green', 
    label: 'Green Theme',
    color: 'rgb(34 197 94)',
    textColor: 'white'
  }
] as const;

export function ThemeToggle() {
  const { theme, mode, setTheme, setMode } = useTheme();
  const currentTheme = themes.find(t => t.name === theme) ?? themes[2]; // Default to green

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button 
          variant="outline"
          size="default"
          className="flex items-center gap-2 min-w-[120px]"
          style={{
            backgroundColor: currentTheme.color,
            color: currentTheme.textColor,
            borderColor: 'transparent'
          }}
        >
          <Palette className="h-4 w-4" />
          {currentTheme.label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {themes.map((t) => (
          <DropdownMenuItem
            key={t.name}
            onClick={() => setTheme(t.name)}
            className="flex items-center gap-2"
          >
            <div
              className="h-4 w-4 rounded-full"
              style={{ backgroundColor: t.color }}
            />
            {t.label}
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onClick={() => setMode('light')}
          className="flex items-center gap-2"
        >
          <Sun className="h-4 w-4" />
          Light Mode
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setMode('dark')}
          className="flex items-center gap-2"
        >
          <Moon className="h-4 w-4" />
          Dark Mode
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
