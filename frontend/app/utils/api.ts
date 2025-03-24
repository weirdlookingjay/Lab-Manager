"use client"

import Cookies from 'js-cookie';
import useSWR, { mutate } from 'swr';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Global fetcher for SWR
export const globalFetcher = async (url: string) => {
  // Check cache first
  const cacheKey: string = `fetch_cache_${url}`;
  const cachedData = localStorage.getItem(cacheKey);
  
  if (cachedData) {
    // Return cached data immediately
    return JSON.parse(cachedData);
  }

  const response = await fetchWithAuth(url);
  if (!response.ok) {
    const error = new Error('An error occurred while fetching the data.');
    // Add extra info to the error object
    (error as any).info = await response.json();
    (error as any).status = response.status;
    throw error;
  }
  
  const data = await response.json();
  
  // Cache the successful response
  localStorage.setItem(cacheKey, JSON.stringify(data));
  
  return data;
};

// Global SWR configuration
export const swrConfig = {
  refreshInterval: 30000, // Default 30s refresh
  dedupingInterval: 10000, // Increase deduping window
  errorRetryCount: 3, // Limit retry attempts
  focusThrottleInterval: 5000, // Throttle focus events
  loadingTimeout: 4000, // Show loading state after 4s
  revalidateOnFocus: false, // Don't revalidate on focus
  shouldRetryOnError: false, // Don't retry on error
  revalidateIfStale: false, // Don't automatically revalidate stale data
  revalidateOnReconnect: false, // Don't revalidate on reconnect
  keepPreviousData: true, // Keep showing previous data while fetching
  isPaused: () => false, // Never pause revalidation
};

// Specific endpoint configurations
export const endpointConfigs = {
  scanStatus: {
    refreshInterval: 15000, // More frequent for scan status
    revalidateOnFocus: true,
    revalidateIfStale: true,
  },
  computers: {
    refreshInterval: 30000,
    revalidateOnFocus: false,
    revalidateIfStale: false,
    dedupingInterval: 10000,
    keepPreviousData: true,
    fallback: [],
    // Use localStorage to cache computer data
    onSuccess: (data: any) => {
      localStorage.setItem('computers_cache', JSON.stringify(data));
    }
  },
  schedules: {
    refreshInterval: 30000,
    revalidateOnFocus: true,
    revalidateIfStale: true,
    dedupingInterval: 5000,
    keepPreviousData: true,
    fallback: [],
    // Use localStorage to cache schedule data
    onSuccess: (data: any) => {
      localStorage.setItem('schedules_cache', JSON.stringify(data));
    }
  },
  notifications: {
    refreshInterval: 60000, // Less frequent for notifications
    revalidateOnFocus: true,
    revalidateIfStale: true,
  }
};

export async function fetchWithAuth<T>(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = Cookies.get('token');
  const user = Cookies.get('user');
  
  console.log('Debug - Token:', token ? 'exists' : 'missing');
  console.log('Debug - User:', user ? 'exists' : 'missing');
  
  // If no token or user, reject with auth error
  if (!token || !user) {
    console.log('No token or user found');
    return Promise.reject({
      type: 'AuthError',
      message: 'No authentication credentials'
    });
  }

  const url = `${API_BASE_URL}${endpoint}`;
  console.log('Debug - Making API request to:', url);
  
  const headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': `Token ${token}`,
    ...options.headers,
  };

  console.log('Debug - Request headers:', {
    'Content-Type': headers['Content-Type'],
    'Accept': headers['Accept'],
    'Authorization': headers['Authorization'] ? 'Token exists' : 'Token missing',
  });

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  console.log('Debug - Response status:', response.status);
  console.log('Debug - Response headers:', Object.fromEntries(response.headers.entries()));

  // Handle 401 by clearing auth state and rejecting with auth error
  if (response.status === 401) {
    console.error('Unauthorized - clearing auth state');
    Cookies.remove('token');
    Cookies.remove('user');
    return Promise.reject({
      type: 'AuthError',
      message: 'Authentication failed'
    });
  }

  return response;
}

export async function login(username: string, password: string) {
  const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || data.message || data.detail || 'Login failed');
  }

  const data = await response.json();
  
  // Validate response data
  if (!data.token || !data.user) {
    throw new Error('Invalid response from server: missing token or user data');
  }

  return {
    token: data.token,
    user: data.user
  };
}

// API root
export async function getApiRoot() {
  return fetchWithAuth('/api/');
}

// Tag API functions
export async function getTags() {
  return fetchWithAuth('/api/tags/');
}

export async function createTag(name: string, color: string = '#3B82F6') {
  return fetchWithAuth('/api/tags/', {
    method: 'POST',
    body: JSON.stringify({ name, color }),
  });
}

export async function deleteTag(id: number) {
  return fetchWithAuth(`/api/tags/${id}/`, {
    method: 'DELETE',
  });
}

export async function addTagToDocument(tagId: number, documentPath: string, computer: string) {
  return fetchWithAuth('/api/tags/add_to_document/', {
    method: 'POST',
    body: JSON.stringify({ tag_id: tagId, document_path: documentPath, computer }),
  });
}

export async function removeTagFromDocument(tagId: number, documentPath: string, computer: string) {
  return fetchWithAuth('/api/tags/remove_from_document/', {
    method: 'POST',
    body: JSON.stringify({ tag_id: tagId, document_path: documentPath, computer }),
  });
}

// Types
export interface Tag {
  id: number;
  name: string;
  color: string;
}

export interface ApiTag {
  id: number;
  name: string;
  color?: string;
}

export interface Computer {
  id: number;
  name: string;
  label: string;
  ip: string;
  status: string;
  last_seen: string;
}

export interface ScanFolder {
  name: string;
  path: string;
  pdf_count: number;
  total_size: number;
}

export interface ApiDocument {
  id: string;
  name: string;
  path: string;
  size: number;
  created: string;
  tags: ApiTag[];
}

export interface DocumentsResponse {
  documents: ApiDocument[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_items: number;
    per_page: number;
  };
}

export interface ScanStatus {
  total: number;
  online: number;
  offline: number;
  enabled: number;
  disabled: number;
  processed_pdfs: number;
  renamed_pdfs: number;
  computers_scanned: number;
  total_computers: number;
  start_time: string | undefined;
  estimated_completion: string | undefined;
  per_computer_progress: Record<string, number>;
  failed_computers: Array<{ computer: string; error: string }>;
  retry_attempts: Record<string, number>;
  scan_in_progress: boolean;
  status: 'idle' | 'running' | 'completed' | 'failed';
  scanning: boolean;
  queue_length: number;
  schedule: {
    type: 'daily' | 'weekly' | 'monthly';
    time: string;
    selectedDays: number[] | undefined;
    monthlyDate: string | undefined;
    emailNotification: boolean;
    emailAddresses: string[];
  };
}

export interface ScanSchedule {
  id?: number;
  type: 'daily' | 'weekly' | 'monthly';
  type_display?: string;
  time: string;
  selected_days: number[];
  monthly_date?: string;
  enabled: boolean;
  computer_ids: number[];
  computers?: Computer[];  
  email_notification: boolean;
  email_addresses: string[];
  created_at?: string;  
  updated_at?: string;  
  last_run?: string;   
  next_run?: string;   
}

export async function getScanStatus(): Promise<ScanStatus> {
  try {
    const response = await fetchWithAuth('/api/scan/status/');
    console.log('Debug - Scan status response:', {
      status: response.status,
      ok: response.ok
    });

    if (!response.ok) {
      const errorData = await response.json();
      console.error('Error response from scan status:', errorData);
      throw new Error(errorData.detail || 'Failed to fetch scan status');
    }

    const data = await response.json();
    console.log('Debug - Scan status data:', data);
    return {
      ...data,
      scanning: data.scan_in_progress,
      status: data.scan_in_progress ? 'running' : 'idle',
      failed_computers: data.failed_computers || [],
      retry_attempts: data.retry_attempts || {},
      per_computer_progress: data.per_computer_progress || {}
    };
  } catch (error) {
    console.error('Error in getScanStatus:', error);
    throw error;
  }
};

export async function startScan(computers: string[]): Promise<void> {
  const response = await fetchWithAuth('/api/scan/start/', {
    method: 'POST',
    body: JSON.stringify({ computers })
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'Failed to start scan');
  }
}

export async function stopScan(): Promise<void> {
  const response = await fetchWithAuth('/api/scan/stop/', {
    method: 'POST'
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'Failed to stop scan');
  }
}

export async function getFolders(): Promise<{ name: string; path: string; pdf_count: number; total_size: number }[]> {
  const response = await fetchWithAuth('/api/scan/folders/');

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'Failed to get folders');
  }

  return response.json();
};

export async function getScanSchedule(): Promise<ScanSchedule | null> {
  try {
    const response = await fetchWithAuth('/api/scan-schedules/', {
      headers: {
        'Accept': 'application/json',
        'Authorization': `Token ${Cookies.get('token')}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch schedule');
    }

    const data = await response.json();
    return data.schedules?.[0] || data.schedule || null;
  } catch (error) {
    console.error('Error fetching schedule:', error);
    return null;
  }
}

export async function createScanSchedule(schedule: Partial<ScanSchedule>): Promise<ScanSchedule> {
  const response = await fetchWithAuth('/api/scan-schedules/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(schedule),
  });

  if (!response.ok) {
    throw new Error('Failed to create schedule');
  }

  const data = await response.json();
  return data.schedule || data;
}

export async function updateScanSchedule(schedule: Partial<ScanSchedule>): Promise<ScanSchedule> {
  if (!schedule.id) {
    throw new Error('Schedule ID is required for update');
  }

  const response = await fetchWithAuth(`/api/scan-schedules/${schedule.id}/`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify(schedule),
  });

  if (!response.ok) {
    throw new Error('Failed to update schedule');
  }

  const data = await response.json();
  return data.schedule || data;
}

export async function deleteScanSchedule(scheduleId: number): Promise<Response> {
  const response = await fetchWithAuth(`/api/scan-schedules/${scheduleId}/`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to delete scan schedule');
  }

  // Force revalidation of all schedule-related endpoints
  await Promise.all([
    mutate('/api/scan-schedules/'),
    mutate('/api/scan-schedules/current/'),
    mutate((key) => typeof key === 'string' && key.startsWith('/api/scan-schedules'), undefined, { revalidate: true })
  ]);
  
  return response;
}

export async function getCurrentSchedule(): Promise<{ schedule: ScanSchedule }> {
  try {
    const response = await fetchWithAuth('/api/scan-schedules/', {
      headers: {
        'Accept': 'application/json',
        'Authorization': `Token ${Cookies.get('token')}`,
      },
    });
    
    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Failed to get current schedule');
    }

    const data = await response.json();
    // If we get an array, take the first schedule
    const schedule = Array.isArray(data) ? data[0] : (data.schedule || data);
    
    return {
      schedule: {
        ...schedule,
        selected_days: schedule?.selected_days || [],
        email_addresses: schedule?.email_addresses || [],
      }
    };
  } catch (error) {
    console.error('Error in getCurrentSchedule:', error);
    // Return empty schedule instead of throwing
    return {
      schedule: {
        type: 'daily',
        time: '09:00',
        selected_days: [],
        enabled: true,
        computer_ids: [],
        email_notification: false,
        email_addresses: []
      }
    };
  }
}

export async function runScanSchedule(scheduleId: number): Promise<void> {
  const response = await fetchWithAuth(`/api/scan/schedule/${scheduleId}/run/`, {
    method: 'POST'
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.detail || 'Failed to run scan schedule');
  }
}

// Helper function to get cache key for schedule
function getScheduleCacheKey(key: string): string {
  return `schedule_${key}`;
}

// Computer API functions
export const getComputers = async (context?: string): Promise<Computer[]> => {
  const searchParams = new URLSearchParams();
  if (context) searchParams.set('context', context);
  
  console.log('Fetching computers...');
  const response = await fetchWithAuth(`/api/computers/?${searchParams.toString()}`);
  
  if (!response.ok) {
    console.error('Failed to fetch computers:', response.status, response.statusText);
    throw new Error('Failed to fetch computers');
  }
  
  const data = await response.json();
  console.log('Received computers:', data);
  return data;
};

// Document API functions
export const getDocuments = async (params: {
  computer: string | null;
  page?: number;
  per_page?: number;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}): Promise<DocumentsResponse> => {
  const searchParams = new URLSearchParams();
  if (params.computer) searchParams.set('computer', params.computer);
  if (params.page) searchParams.set('page', params.page.toString());
  if (params.per_page) searchParams.set('per_page', params.per_page.toString());
  if (params.search) searchParams.set('search', params.search);
  if (params.sort_by) searchParams.set('sort_by', params.sort_by);
  if (params.sort_order) searchParams.set('sort_order', params.sort_order);

  const response = await fetchWithAuth(`/api/documents/?${searchParams.toString()}`);
  if (!response.ok) {
    console.error('Failed to fetch documents:', response.status, response.statusText);
    throw new Error('Failed to fetch documents');
  }
  const data = await response.json();
  return data;
};
