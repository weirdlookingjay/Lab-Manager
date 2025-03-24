export type NotificationType = 'info' | 'warning' | 'error' | 'success';
export type NotificationPriority = 'low' | 'medium' | 'high' | 'critical';

export interface Notification {
    id: number;
    title: string;
    message: string;
    type: NotificationType;
    priority: NotificationPriority;
    is_read: boolean;
    created_at: string;
    updated_at: string;
}
