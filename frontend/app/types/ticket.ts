import { User } from './user';

export type TicketPriority = 'low' | 'medium' | 'high' | 'urgent';

export type TicketStatus = 'open' | 'in_progress' | 'pending' | 'resolved' | 'closed';

export interface CustomField {
  id: string;
  name: string;
  type: 'text' | 'number' | 'select' | 'multiselect' | 'date' | 'checkbox';
  options?: string[];
  required: boolean;
  value: any;
  placeholder?: string;
  description?: string;
}

export interface TicketTemplate {
  id: string;
  name: string;
  description: string;
  default_priority: TicketPriority;
  default_assignee?: string;
  custom_fields: Record<string, {
    type: 'text' | 'number' | 'select' | 'multiselect' | 'date' | 'checkbox';
    required: boolean;
    description?: string;
    options?: string[];
    value?: any;
  }>;
  sla_minutes?: number;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  priority: TicketPriority;
  status: TicketStatus;
  created_by: User;
  assigned_to?: User;
  created_at: string;  // ISO 8601 format
  updated_at: string;  // ISO 8601 format
  due_date?: string;  // ISO 8601 format
  custom_fields: { [key: string]: any };
  tags: string[];
  linked_tickets: string[];
  parent_ticket?: string;
  sla_breach_at?: string;  // ISO 8601 format
  template?: string;
  comments: TicketComment[];
  isInternal: boolean;
  attachments?: string[];
  activity_log: TicketActivityLogEntry[];
}

export interface SLAConfig {
  priority: TicketPriority;
  responseMinutes: number;
  resolutionMinutes: number;
}

export interface TicketComment {
  id: string;
  content: string;
  author: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  is_internal: boolean;
  created_at: string;
  updated_at: string;
  ticket: string;
  attachments?: string[];
}

export interface TicketActivityLogEntry {
  id: string;
  action: 'status_change' | 'assignment' | 'priority_change' | 'tag_change' | 'CREATE';
  timestamp: string;  // ISO 8601 format
  user: string;
  old_value?: string;
  new_value: string;
  note?: string;
  details?: {
    old_value?: string;
    new_value: string;
    note?: string;
  };
}

// API response type
export interface RoutingRuleResponse {
  id: string;
  name: string;
  conditions: {
    keywords?: string[];
    priority?: 'low' | 'medium' | 'high' | 'urgent';
    customFields?: Record<string, string>;
    timeRange?: {
      start?: string;
      end?: string;
    };
  };
  actions: {
    setPriority?: 'low' | 'medium' | 'high' | 'urgent';
    setAssignee?: string;
    setStatus?: string;
    setTags?: string[];
  };
  assign_to?: User;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Frontend form type
export interface RoutingRule {
  id: string;
  name: string;
  conditions: {
    priority?: string;
    status?: string;
    tags?: string[];
    assignedTo?: string;
    keywords?: string[];
    customFields?: Record<string, string>;
  };
  actions: {
    setPriority?: 'low' | 'medium' | 'high' | 'urgent';
    setAssignee?: string;
    setStatus?: string;
    setTags?: string[];
  };
  assignTo: User | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Type for creating a new ticket
export interface TicketCreateRequest {
  title: string;
  description: string;
  priority: TicketPriority;
  assigned_to?: string;  // User ID
  custom_fields?: { [key: string]: any };
  template?: string;
}

// Type for updating a ticket
export interface TicketUpdateRequest {
  title?: string;
  description?: string;
  priority?: TicketPriority;
  assigned_to?: string | null;  // User ID or null to unassign
  status?: TicketStatus;
  custom_fields?: { [key: string]: any };
  tags?: string[];
  statusNote?: string;  // Note to add when changing status
}
