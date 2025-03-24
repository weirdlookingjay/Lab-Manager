import { NextResponse } from 'next/server';
import { headers } from 'next/headers';
import { subMinutes } from 'date-fns';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ProcessData {
  name?: string;
  platform?: string;
  process_id?: string;
  cpu?: number;
  memory_private_working_set?: string;
  memory_physical?: string;
  memory_paged?: string;
}

async function getTokenFromCookie(): Promise<string | undefined> {
  const headersList = await headers();
  const cookieHeader = headersList.get('cookie') || '';
  return cookieHeader.split(';')
    .find((c: string) => c.trim().startsWith('token='))
    ?.split('=')[1];
}

export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const token = await getTokenFromCookie();

    if (!token) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const response = await fetch(`${API_BASE_URL}/api/computers/${params.id}/`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      cache: 'no-store'
    });

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Not Found', { status: 404 });
      }
      if (response.status === 401) {
        return new NextResponse('Unauthorized', { status: 401 });
      }
      throw new Error('Failed to fetch computer');
    }

    const data = await response.json();
    const thirtyMinutesAgo = subMinutes(new Date(), 30);

    // Status is determined by backend:
    // Online: last_metrics_update or last_seen within 30 minutes
    // Offline: no metrics update AND no last_seen in last 30 minutes
    const lastMetricsDate = data.last_metrics_update ? new Date(data.last_metrics_update) : null;
    const lastSeenDate = data.last_seen ? new Date(data.last_seen) : null;

    const isOnline = (lastMetricsDate && lastMetricsDate > thirtyMinutesAgo) || 
                     (lastSeenDate && lastSeenDate > thirtyMinutesAgo);

    return NextResponse.json({
      id: data.id,
      hostname: data.hostname || 'Unknown',
      label: data.label || data.hostname || 'Unknown',
      ip_address: data.ip_address || 'Unknown',
      status: data.status || (isOnline ? 'online' : 'offline'),
      last_seen: data.last_seen || null,
      last_metrics_update: data.last_metrics_update || null,
      manufacturer: data.manufacturer || 'Unknown',
      model: data.model || 'Unknown',
      os: data.os || 'Unknown',
      os_version: data.os_version || 'Unknown',
      
      // System Overview
      cpu: {
        model: data.cpu_model || 'Unknown',
        speed: data.cpu_speed || 'Unknown',
        cores: data.cpu_cores || 0,
        threads: data.cpu_threads || 0
      },
      disk: {
        size: data.disk_size || '0',
        free: data.disk_free || '0',
        used: data.disk_used || '0'
      },
      memory: {
        total: data.memory_total || '0',
        available: data.memory_available || '0',
        used: data.memory_used || '0'
      },
      system_uptime: data.system_uptime || 'Not Available',
      device_class: data.device_class || 'Unknown',
      logged_in_user: data.logged_in_user || 'No User',

      // System Information
      last_discovery: data.last_discovery || data.last_seen || null,
      last_system_warranty_discovery: data.last_system_warranty_discovery || data.last_seen || null,
      class: data.class || 'Client',
      serial_number: data.serial_number || '',
      serial_number_service_tag: data.serial_number_service_tag || data.serial_number || '',
      warranty_status: data.warranty_status || 'Unknown',
      device_time_zone: data.device_time_zone || '(UTC-05:00) Eastern Time (US & Canada)',
      os_architecture: data.os_architecture || '64-bit',
      license_key: data.license_key || '',
      agent_status: data.agent_status || '',
      last_boot_up: data.last_boot_up || data.last_seen || null,

      // Processes
      running_processes: (data.running_processes || []).map((process: ProcessData) => ({
        name: process.name || 'Unknown',
        platform: process.platform || 'Unknown',
        process_id: process.process_id || 'Unknown',
        cpu: process.cpu || 0,
        memory_private_working_set: process.memory_private_working_set || '0',
        memory_physical: process.memory_physical || '0',
        memory_paged: process.memory_paged || '0'
      })),

      memory_utilization: data.memory_utilization || [
        {
          timestamp: new Date().toISOString(),
          values: [0, 0, 0, 0, 0]
        }
      ]
    });
  } catch (error) {
    console.error('Error fetching computer:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}

export async function PUT(
  request: Request,
  { params }: { params: { id: string } }
) {
  try {
    const token = await getTokenFromCookie();

    if (!token) {
      return new NextResponse('Unauthorized', { status: 401 });
    }

    const body = await request.json();
    const response = await fetch(`${API_BASE_URL}/api/computers/${params.id}/`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${token}`
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      if (response.status === 404) {
        return new NextResponse('Not Found', { status: 404 });
      }
      if (response.status === 401) {
        return new NextResponse('Unauthorized', { status: 401 });
      }
      throw new Error('Failed to update computer');
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error updating computer:', error);
    return new NextResponse('Internal Server Error', { status: 500 });
  }
}
