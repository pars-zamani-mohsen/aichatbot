import React, { useState, useEffect } from 'react';
import {
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Typography,
  Box,
  Divider,
  Button,
  CircularProgress
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Chat as ChatIcon,
  Web as WebIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { notifications as notificationService } from '../../services/api';

const NotificationBell = () => {
  const [unreadCount, setUnreadCount] = useState(0);
  const [recentNotifications, setRecentNotifications] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [loading, setLoading] = useState(false);

  // دریافت تعداد اعلان‌های نخوانده
  const fetchUnreadCount = async () => {
    try {
      const data = await notificationService.getUnreadCount();
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error('Error fetching unread count:', err);
    }
  };

  // دریافت اعلان‌های اخیر
  const fetchRecentNotifications = async () => {
    try {
      setLoading(true);
      const data = await notificationService.getNotifications(0, 5, true);
      setRecentNotifications(data);
    } catch (err) {
      console.error('Error fetching recent notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  // علامت‌گذاری به عنوان خوانده شده
  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationService.markAsRead(notificationId);
      await fetchUnreadCount();
      await fetchRecentNotifications();
    } catch (err) {
      console.error('Error marking notification as read:', err);
    }
  };

  // دریافت آیکون بر اساس نوع اعلان
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return <SuccessIcon color="success" fontSize="small" />;
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />;
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />;
      default:
        return <InfoIcon color="info" fontSize="small" />;
    }
  };

  // دریافت آیکون بر اساس دسته‌بندی
  const getCategoryIcon = (category) => {
    switch (category) {
      case 'conversation':
        return <ChatIcon fontSize="small" />;
      case 'website':
        return <WebIcon fontSize="small" />;
      case 'security':
        return <SecurityIcon fontSize="small" />;
      case 'system':
        return <SettingsIcon fontSize="small" />;
      default:
        return <InfoIcon fontSize="small" />;
    }
  };

  // فرمت کردن تاریخ
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));

    if (diffInMinutes < 1) {
      return 'همین الان';
    } else if (diffInMinutes < 60) {
      return `${diffInMinutes} دقیقه پیش`;
    } else {
      const diffInHours = Math.floor(diffInMinutes / 60);
      return `${diffInHours} ساعت پیش`;
    }
  };

  // کوتاه کردن متن
  const truncateText = (text, maxLength = 50) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  useEffect(() => {
    fetchUnreadCount();
    fetchRecentNotifications();

    // به‌روزرسانی هر 30 ثانیه
    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
    fetchRecentNotifications();
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <>
      <IconButton
        color="inherit"
        onClick={handleClick}
        sx={{ ml: 1 }}
      >
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 350,
            maxHeight: 400
          }
        }}
      >
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6" component="div">
            اعلان‌ها
          </Typography>
          {unreadCount > 0 && (
            <Typography variant="body2" color="text.secondary">
              {unreadCount} اعلان نخوانده
            </Typography>
          )}
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress size={24} />
          </Box>
        ) : recentNotifications.length === 0 ? (
          <Box sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              اعلان جدیدی وجود ندارد
            </Typography>
          </Box>
        ) : (
          <>
            {recentNotifications.map((notification) => (
              <MenuItem
                key={notification.id}
                sx={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  p: 2,
                  minHeight: 'auto'
                }}
                onClick={() => handleMarkAsRead(notification.id)}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', width: '100%', mb: 1 }}>
                  {getNotificationIcon(notification.type)}
                  <Typography
                    variant="subtitle2"
                    sx={{ ml: 1, flexGrow: 1, fontWeight: notification.is_read ? 'normal' : 'bold' }}
                  >
                    {notification.title}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    {getCategoryIcon(notification.category)}
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(notification.created_at)}
                    </Typography>
                  </Box>
                </Box>

                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ width: '100%' }}
                >
                  {truncateText(notification.message)}
                </Typography>
              </MenuItem>
            ))}

            <Divider />

            <Box sx={{ p: 1 }}>
              <Button
                fullWidth
                variant="text"
                size="small"
                onClick={() => {
                  handleClose();
                  // Navigate to notification center
                  window.location.href = '/notifications';
                }}
              >
                مشاهده همه اعلان‌ها
              </Button>
            </Box>
          </>
        )}
      </Menu>
    </>
  );
};

export default NotificationBell;
