"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { fetchWithAuth } from "../utils/api";
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

interface Computer {
  id: number;
  label: string;
  ip: string;
  last_seen: string;
  logged_in_user: string | null;
}

export default function ComputersPage() {
  const [computers, setComputers] = useState<Computer[]>([]);
  const [loading, setLoading] = useState(true);
  // const [retryCount, setRetryCount] = useState(0);
  const [retryCount] = useState(0);
  const { toast } = useToast();

  useEffect(() => {
    loadComputers();

    // Start with 30 second polling, increase up to 2 minutes on errors
    const pollInterval = Math.min(30000 * Math.pow(1.5, retryCount), 120000);
    const interval = setInterval(loadComputers, pollInterval);

    return () => clearInterval(interval);
  }, [retryCount]);

  const loadComputers = async () => {
    try {
      // const response = await fetchWithAuth("/api/computers/");
      // if (!response.ok) {
      //   if (response.status === 429) {  // Too Many Requests
      //     setRetryCount(prev => prev + 1);
      //     throw new Error("Rate limit exceeded, reducing polling frequency");
      //   }
      //   const data = await response.json();

      //   // Add detailed logging
      //   console.log('Raw API response:', JSON.stringify(data, null, 2));

      //   throw new Error("Failed to fetch computers");
      // }
      // const data = await response.json();
      // console.log('Fetched computers:', data);
      // data.forEach((computer: Computer) => {
      //   console.log(`Computer ${computer.label}:`, {
      //     logged_in_user: computer.logged_in_user,
      //     last_seen: computer.last_seen,
      //     ip: computer.ip
      //   });
      // });
      //setComputers(data);
      // Reset retry count on success
      //setRetryCount(0);
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

      console.log('Fetching from:', `${API_BASE_URL}/api/computers/`);
      const response = await fetchWithAuth("/api/computers/");

      if (!response.ok) {
        // ...existing error handling...
      }
      const data = await response.json();

      // Add detailed logging
      console.log('Raw API response:', JSON.stringify(data, null, 2));
      data.forEach((computer: Computer) => {
        console.log('Computer details:', {
          id: computer.id,
          label: computer.label,
          logged_in_user: computer.logged_in_user,
          raw_user: computer.logged_in_user === null ? 'null' : computer.logged_in_user
        });
      });

      setComputers(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load computers";
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const formatLastSeen = (date: string) => {
    try {
      return formatDistanceToNow(new Date(date), { addSuffix: true });
    } catch {
      return "Unknown";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6">
      <Card>
        <CardHeader>
          <CardTitle>Computers</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Computer Label</TableHead>
                <TableHead>IP Address</TableHead>
                <TableHead>Last Seen</TableHead>
                <TableHead>Logged in User</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {computers.map((computer) => (
                <TableRow key={computer.id}>
                  <TableCell>
                    <Link
                      href={`/computers/${computer.id}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      {computer.label}
                    </Link>
                  </TableCell>
                  <TableCell>{computer.ip}</TableCell>
                  <TableCell>{computer.last_seen ? formatLastSeen(computer.last_seen) : 'Never'}</TableCell>
                  <TableCell>{computer.logged_in_user || 'Not logged in'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
