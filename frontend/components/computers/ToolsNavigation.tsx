"use client"

import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useRouter, usePathname } from "next/navigation"
import { 
  MonitorDot, 
  Cpu, 
  Database, 
  Box, 
  Power, 
  Printer, 
  Terminal, 
  FolderOpen 
} from "lucide-react";

interface ToolsNavigationProps {
  computerId: string;
}

export function ToolsNavigation({ computerId }: ToolsNavigationProps) {
  return (
    <div className="flex items-center border-b border-gray-200">
      <nav className="flex px-4">
        <a className="py-2 text-xs font-medium text-gray-900 border-b-2 border-blue-500 -mb-px">Overview</a>
        <a className="py-2 text-xs font-medium text-gray-500">Tools</a>
        <a className="py-2 text-xs font-medium text-gray-500">Monitoring</a>
        <a className="py-2 text-xs font-medium text-gray-500">Asset</a>
        <a className="py-2 text-xs font-medium text-gray-500">Notes</a>
        <a className="py-2 text-xs font-medium text-gray-500">Settings</a>
        <a className="py-2 text-xs font-medium text-gray-500">Remote Control Settings</a>
        <a className="py-2 text-xs font-medium text-gray-500">Reports</a>
      </nav>
    </div>
  );
}
