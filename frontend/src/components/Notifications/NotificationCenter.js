import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Badge,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  CircularProgress,
  Alert,
  Menu,
  MenuItem,
  FormControl,
  InputLabel,
  Select
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Delete as DeleteIcon,
  MarkEmailRead as MarkReadIcon,
  FilterList as FilterIcon,
  Chat as ChatIcon,
  Web as WebIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { notifications as notificationService } from '../../services/api';

const NotificationCenter = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [filterCategory, setFilterCategory] = useState('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  // const [testDialogOpen, setTestDialogOpen] = useState(false);

  // دریافت اعلان‌ها
  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        skip: 0,
        limit: 50,
        unreadOnly: showUnreadOnly
      };

      if (filterCategory !== 'all') {
        params.category = filterCategory;
      }

      const data = await notificationService.getNotifications(
        params.skip,
        params.limit,
        params.unreadOnly,
        params.category
      );

      setNotifications(data);
    } catch (err) {
      setError('خطا در دریافت اعلان‌ها');
      console.error('Error fetching notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  // دریافت تعداد اعلان‌های نخوانده
  const fetchUnreadCount = async () => {
    try {
      const data = await notificationService.getUnreadCount(
        filterCategory !== 'all' ? filterCategory : null
      );
      setUnreadCount(data.unread_count);
    } catch (err) {
      console.error('Error fetching unread count:', err);
    }
  };

  // علامت‌گذاری به عنوان خوانده شده
  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationService.markAsRead(notificationId);
      await fetchNotifications();
      await fetchUnreadCount();
    } catch (err) {
      setError('خطا در علامت‌گذاری اعلان');
      console.error('Error marking notification as read:', err);
    }
  };

  // علامت‌گذاری همه به عنوان خوانده شده
  const handleMarkAllAsRead = async () => {
    try {
      await notificationService.markAllAsRead(
        filterCategory !== 'all' ? filterCategory : null
      );
      await fetchNotifications();
      await fetchUnreadCount();
    } catch (err) {
      setError('خطا در علامت‌گذاری همه اعلان‌ها');
      console.error('Error marking all notifications as read:', err);
    }
  };

  // حذف اعلان
  const handleDeleteNotification = async (notificationId) => {
    try {
      await notificationService.deleteNotification(notificationId);
      await fetchNotifications();
      await fetchUnreadCount();
    } catch (err) {
      setError('خطا در حذف اعلان');
      console.error('Error deleting notification:', err);
    }
  };

  // ایجاد اعلان تست - مخفی شده است
  // const handleCreateTestNotification = async () => {
  //   try {
  //     await notificationService.createTestNotification();
  //     setTestDialogOpen(false);
  //     await fetchNotifications();
  //     await fetchUnreadCount();
  //   } catch (err) {
  //     setError('خطا در ایجاد اعلان تست');
  //     console.error('Error creating test notification:', err);
  //   }
  // };

  // دریافت آیکون بر اساس نوع اعلان
  const getNotificationIcon = (type) => {
    switch (type) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  // دریافت آیکون بر اساس دسته‌بندی
  const getCategoryIcon = (category) => {
    switch (category) {
      case 'conversation':
        return <ChatIcon />;
      case 'website':
        return <WebIcon />;
      case 'security':
        return <SecurityIcon />;
      case 'system':
        return <SettingsIcon />;
      default:
        return <InfoIcon />;
    }
  };

  // فرمت کردن تاریخ
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));

    if (diffInHours < 1) {
      return 'کمتر از یک ساعت پیش';
    } else if (diffInHours < 24) {
      return `${diffInHours} ساعت پیش`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      return `${diffInDays} روز پیش`;
    }
  };

  useEffect(() => {
    fetchNotifications();
    fetchUnreadCount();
  }, [filterCategory, showUnreadOnly]);

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          مرکز اعلان‌ها
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <Badge badgeContent={unreadCount} color="error">
            <NotificationsIcon />
          </Badge>

          <Button
            variant="outlined"
            startIcon={<FilterIcon />}
            onClick={(e) => setAnchorEl(e.currentTarget)}
          >
            فیلتر
          </Button>

          {/* دکمه ایجاد اعلان تست مخفی شده است */}
          {/* <Button
            variant="contained"
            onClick={() => setTestDialogOpen(true)}
          >
            ایجاد اعلان تست
          </Button> */}
        </Box>
      </Box>

      {/* فیلتر منو */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem>
          <FormControl fullWidth size="small">
            <InputLabel>دسته‌بندی</InputLabel>
            <Select
              value={filterCategory}
              onChange={(e) => setFilterCategory(e.target.value)}
              label="دسته‌بندی"
            >
              <MenuItem value="all">همه</MenuItem>
              <MenuItem value="conversation">چت‌ها</MenuItem>
              <MenuItem value="website">وب‌سایت‌ها</MenuItem>
              <MenuItem value="security">امنیت</MenuItem>
              <MenuItem value="system">سیستم</MenuItem>
            </Select>
          </FormControl>
        </MenuItem>
        <MenuItem>
          <Button
            variant={showUnreadOnly ? "contained" : "outlined"}
            onClick={() => setShowUnreadOnly(!showUnreadOnly)}
            fullWidth
          >
            فقط نخوانده‌ها
          </Button>
        </MenuItem>
      </Menu>

      {/* دکمه‌های عملیات */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<MarkReadIcon />}
          onClick={handleMarkAllAsRead}
          disabled={notifications.length === 0}
        >
          علامت‌گذاری همه به عنوان خوانده شده
        </Button>
      </Box>

      {/* نمایش خطا */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* لیست اعلان‌ها */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : notifications.length === 0 ? (
        <Box sx={{ textAlign: 'center', p: 4 }}>
          <NotificationsIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary">
            اعلانی وجود ندارد
          </Typography>
        </Box>
      ) : (
        <List>
          {notifications.map((notification) => (
            <React.Fragment key={notification.id}>
              <ListItem
                sx={{
                  backgroundColor: notification.is_read ? 'transparent' : 'action.hover',
                  borderRadius: 1,
                  mb: 1
                }}
              >
                <ListItemIcon>
                  {getNotificationIcon(notification.type)}
                </ListItemIcon>

                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1" component="span">
                        {notification.title}
                      </Typography>
                      {!notification.is_read && (
                        <Chip
                          label="جدید"
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                      <Chip
                        icon={getCategoryIcon(notification.category)}
                        label={notification.category}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(notification.created_at)}
                      </Typography>
                    </Box>
                  }
                />

                <Box sx={{ display: 'flex', gap: 1 }}>
                  {!notification.is_read && (
                    <IconButton
                      size="small"
                      onClick={() => handleMarkAsRead(notification.id)}
                      title="علامت‌گذاری به عنوان خوانده شده"
                    >
                      <MarkReadIcon />
                    </IconButton>
                  )}
                  <IconButton
                    size="small"
                    onClick={() => handleDeleteNotification(notification.id)}
                    title="حذف اعلان"
                  >
                    <DeleteIcon />
                  </IconButton>
                </Box>
              </ListItem>
              <Divider />
            </React.Fragment>
          ))}
        </List>
      )}

      {/* دیالوگ ایجاد اعلان تست مخفی شده است */}
      {/* <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)}>
        <DialogTitle>ایجاد اعلان تست</DialogTitle>
        <DialogContent>
          <Typography>
            آیا می‌خواهید یک اعلان تست ایجاد کنید؟
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>
            انصراف
          </Button>
          <Button onClick={handleCreateTestNotification} variant="contained">
            ایجاد
          </Button>
        </DialogActions>
      </Dialog> */}
    </Box>
  );
};

export default NotificationCenter;
