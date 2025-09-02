import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { notifications as notificationService, auth } from '../services/api';

const NotificationContext = createContext();

export const useNotifications = () => {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
};

export const NotificationProvider = ({ children }) => {
    const { user } = useAuth();
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [notificationSettings, setNotificationSettings] = useState({
        emailNotifications: true,
        pushNotifications: true,
        smsNotifications: false,
        notifyOnNewConversation: true,
        notifyOnWebsiteUpdate: true
    });

    // پاک کردن state وقتی کاربر تغییر می‌کند
    useEffect(() => {
        if (!user) {

            setNotifications([]);
            setUnreadCount(0);
            setError(null);
        } else {
            // وقتی کاربر login می‌کند، state را پاک کن

            setNotifications([]);
            setUnreadCount(0);
            setError(null);
        }
    }, [user]); // هر تغییر در user object

    // دریافت اعلان‌ها
    const fetchNotifications = async (skip = 0, limit = 50, unreadOnly = false, category = null) => {
        if (!user) return;

        try {
            setLoading(true);
            setError(null);

            const data = await notificationService.getNotifications(skip, limit, unreadOnly, category);
            setNotifications(data);
        } catch (err) {
            setError('خطا در دریافت اعلان‌ها');
            console.error('Error fetching notifications:', err);
        } finally {
            setLoading(false);
        }
    };

    // دریافت تعداد اعلان‌های نخوانده
    const fetchUnreadCount = async (category = null) => {
        if (!user) return;

        try {
            const data = await notificationService.getUnreadCount(category);
            setUnreadCount(data.unread_count);
        } catch (err) {
            console.error('Error fetching unread count:', err);
        }
    };

    // علامت‌گذاری به عنوان خوانده شده
    const markAsRead = async (notificationId) => {
        if (!user) return;

        try {

            await notificationService.markAsRead(notificationId);
            // به‌روزرسانی state محلی
            setNotifications(prev =>
                prev.map(notification =>
                    notification.id === notificationId
                        ? { ...notification, is_read: true }
                        : notification
                )
            );
            await fetchUnreadCount();
        } catch (err) {
            setError('خطا در علامت‌گذاری اعلان');
            console.error('Error marking notification as read:', err);
        }
    };

    // علامت‌گذاری همه به عنوان خوانده شده
    const markAllAsRead = async (category = null) => {
        if (!user) return;

        try {
            await notificationService.markAllAsRead(category);
            // به‌روزرسانی state محلی
            setNotifications(prev =>
                prev.map(notification => ({ ...notification, is_read: true }))
            );
            setUnreadCount(0);
        } catch (err) {
            setError('خطا در علامت‌گذاری اعلان‌ها');
            console.error('Error marking all notifications as read:', err);
        }
    };

    // حذف اعلان
    const deleteNotification = async (notificationId) => {
        if (!user) return;

        try {
            await notificationService.deleteNotification(notificationId);
            // حذف از state محلی
            setNotifications(prev => prev.filter(notification => notification.id !== notificationId));
            await fetchUnreadCount();
        } catch (err) {
            setError('خطا در حذف اعلان');
            console.error('Error deleting notification:', err);
        }
    };

    // ایجاد اعلان تست
    const createTestNotification = async () => {
        if (!user) return;

        try {
            await notificationService.createTestNotification();
            await fetchNotifications();
            await fetchUnreadCount();
        } catch (err) {
            setError('خطا در ایجاد اعلان تست');
            console.error('Error creating test notification:', err);
        }
    };

    // دریافت تنظیمات اعلان‌های کاربر
    const fetchNotificationSettings = async () => {
        if (!user) return;

        try {
            const userSettings = await auth.getUserSettings();
            if (userSettings.notifications) {
                setNotificationSettings({
                    emailNotifications: userSettings.notifications.emailNotifications ?? true,
                    pushNotifications: userSettings.notifications.pushNotifications ?? true,
                    smsNotifications: userSettings.notifications.smsNotifications ?? false,
                    notifyOnNewConversation: userSettings.notifications.notifyOnNewConversation ?? true,
                    notifyOnWebsiteUpdate: userSettings.notifications.notifyOnWebsiteUpdate ?? true
                });
            }
        } catch (err) {
            console.error('Error fetching notification settings:', err);
        }
    };

    // به‌روزرسانی خودکار فقط یک بار وقتی کاربر login می‌کند
    useEffect(() => {
        if (!user?.id) return;

        // فقط یک بار درخواست ارسال کن
        fetchNotifications();
        fetchUnreadCount();
        fetchNotificationSettings();
    }, [user?.id]); // فقط وقتی user.id تغییر می‌کند

    const value = {
        notifications,
        unreadCount,
        loading,
        error,
        notificationSettings,
        fetchNotifications,
        fetchUnreadCount,
        fetchNotificationSettings,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        createTestNotification,
        clearError: () => setError(null),
        currentUserId: user?.id
    };

    return (
        <NotificationContext.Provider value={value}>
            {children}
        </NotificationContext.Provider>
    );
};
