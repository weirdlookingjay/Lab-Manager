import { useState, useEffect } from 'react';
import { CpuMetrics } from '@/lib/types';

interface MetricsResponse {
  cpu_percent?: number;
  memory_percent?: number;
  cpu_speed?: string;
  memory_gb?: string;
  metrics?: {
    cpu?: CpuMetrics;
  };
  cpu?: CpuMetrics;
}

export function useMetricsPolling(computerId: string, token?: string, interval: number = 5000) {
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const url = new URL(`/api/computers/${computerId}/`, baseUrl);
        
        const response = await fetch(url.toString(), {
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Token ${token}` } : {})
          },
          method: 'GET'
        });
        if (!response.ok) throw new Error('Failed to fetch metrics');
        const data = await response.json();
        setMetrics(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch metrics');
      }
    };

    if (computerId) {
      // Initial fetch
      fetchMetrics();

      // Set up polling
      const pollInterval = setInterval(fetchMetrics, interval);

      // Cleanup
      return () => clearInterval(pollInterval);
    }
  }, [computerId, token, interval]);

  return { metrics, error };
}
