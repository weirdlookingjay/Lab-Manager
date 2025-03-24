import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import axios from 'axios';

const NotificationCenter = () => {
    const [notifications, setNotifications] = useState([]);
    const [socket, setSocket] = useState(null);

    useEffect(() => {
        // Fetch existing notifications
        fetchNotifications();
        
        // Set up WebSocket connection
        const ws = new WebSocket(`ws://${window.location.host}/ws/notifications/`);
        
        ws.onopen = () => {
            console.log('WebSocket Connected');
        };

        ws.onmessage = (event) => {
            const notification = JSON.parse(event.data);
            handleNewNotification(notification);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        setSocket(ws);

        return () => {
            if (ws) {
                ws.close();
            }
        };
    }, []);

    const fetchNotifications = async () => {
        try {
            const response = await axios.get('/api/notifications/');
            setNotifications(response.data);
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    };

    const handleNewNotification = (notification) => {
        // Add to notifications list
        setNotifications(prev => [notification, ...prev]);
        
        // Show toast notification
        toast[notification.type || 'info'](notification.message, {
            position: "top-right",
            autoClose: 5000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
        });
    };

    const markAsRead = async (notificationId) => {
        try {
            await axios.post(`/api/notifications/${notificationId}/mark_read/`);
            setNotifications(prev =>
                prev.map(notif =>
                    notif.id === notificationId
                        ? { ...notif, is_read: true }
                        : notif
                )
            );
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    };

    const markAllAsRead = async () => {
        try {
            await axios.post('/api/notifications/mark_all_read/');
            setNotifications(prev =>
                prev.map(notif => ({ ...notif, is_read: true }))
            );
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    };

    return (
        <div className="notification-center">
            <div className="notification-header">
                <h2>Notifications</h2>
                {notifications.some(n => !n.is_read) && (
                    <button onClick={markAllAsRead}>Mark all as read</button>
                )}
            </div>
            <div className="notification-list">
                {notifications.length === 0 ? (
                    <p>No notifications</p>
                ) : (
                    notifications.map(notification => (
                        <div
                            key={notification.id}
                            className={`notification-item ${notification.type} ${notification.is_read ? 'read' : 'unread'}`}
                            onClick={() => !notification.is_read && markAsRead(notification.id)}
                        >
                            <div className="notification-title">{notification.title}</div>
                            <div className="notification-message">{notification.message}</div>
                            <div className="notification-meta">
                                <span className="notification-priority">{notification.priority}</span>
                                <span className="notification-time">
                                    {new Date(notification.created_at).toLocaleString()}
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default NotificationCenter;
