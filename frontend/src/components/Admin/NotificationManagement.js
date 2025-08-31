import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  LinearProgress,
  Avatar,
  Tooltip,
  Pagination,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Delete,
  Visibility,
  Notifications,
  Person,
  CalendarToday,
  Search,
  Refresh,
  Message,
  Info,
  CheckCircle,
  Warning,
  Error,
  Chat,
  Web,
  Security,
  Settings,
  Send,
  MarkEmailRead,
  FilterList
} from '@mui/icons-material';
import { notifications as notificationService } from '../../services/api';

const NotificationManagement = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedNotification, setSelectedNotification] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [userFilter, setUserFilter] = useState('all');
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      setError('');

      const params = {
        skip: (page - 1) * 20,
        limit: 20,
        unreadOnly: showUnreadOnly
      };

      if (searchTerm) {
        params.search = searchTerm;
      }

      if (categoryFilter !== 'all') {
        params.category = categoryFilter;
      }

      if (typeFilter !== 'all') {
        params.type = typeFilter;
      }

      if (userFilter !== 'all') {
        params.userId = userFilter;
      }

      const data = await notificationService.getAdminNotifications(params);
      setNotifications(data.notifications || []);
      setTotalPages(Math.ceil((data.total || 0) / 20));
    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError('خطا در دریافت اعلان‌ها');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [page, searchTerm, categoryFilter, typeFilter, userFilter, showUnreadOnly]);

  const handleSearch = (event) => {
    setSearchTerm(event.target.value);
    setPage(1);
  };

  const handleCategoryFilterChange = (event) => {
    setCategoryFilter(event.target.value);
    setPage(1);
  };

  const handleTypeFilterChange = (event) => {
    setTypeFilter(event.target.value);
    setPage(1);
  };

  const handleUserFilterChange = (event) => {
    setUserFilter(event.target.value);
    setPage(1);
  };

  const handleViewNotification = (notification) => {
    setSelectedNotification(notification);
    setOpenDialog(true);
  };

  const handleDeleteNotification = async (notificationId) => {
    try {
      await notificationService.deleteAdminNotification(notificationId);
      setSuccess('اعلان با موفقیت حذف شد');
      fetchNotifications();
    } catch (err) {
      setError('خطا در حذف اعلان');
      console.error('Error deleting notification:', err);
    }
  };

  const handleMarkAsRead = async (notificationId) => {
    try {
      await notificationService.markAsRead(notificationId);
      fetchNotifications();
    } catch (err) {
      setError('خطا در علامت‌گذاری اعلان');
      console.error('Error marking notification as read:', err);
    }
  };

  const handleSendNotification = async (notificationData) => {
    try {
      await notificationService.sendAdminNotification(notificationData);
      setSuccess('اعلان با موفقیت ارسال شد');
      fetchNotifications();
    } catch (err) {
      setError('خطا در ارسال اعلان');
      console.error('Error sending notification:', err);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fa-IR');
  };

  const formatTime = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleTimeString('fa-IR');
  };

  const getNotificationIcon = (type) => {
    switch (type) {
      case 'info':
        return <Info sx={{ color: 'info.main' }} />;
      case 'success':
        return <CheckCircle sx={{ color: 'success.main' }} />;
      case 'warning':
        return <Warning sx={{ color: 'warning.main' }} />;
      case 'error':
        return <Error sx={{ color: 'error.main' }} />;
      default:
        return <Info sx={{ color: 'info.main' }} />;
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'conversation':
        return <Chat sx={{ fontSize: 16 }} />;
      case 'website':
        return <Web sx={{ fontSize: 16 }} />;
      case 'security':
        return <Security sx={{ fontSize: 16 }} />;
      case 'system':
        return <Settings sx={{ fontSize: 16 }} />;
      default:
        return <Notifications sx={{ fontSize: 16 }} />;
    }
  };

  const getStatusColor = (isRead) => {
    return isRead ? 'default' : 'primary';
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
          مدیریت اعلان‌ها
        </Typography>
        <Typography variant="body1" color="text.secondary">
          نظارت و مدیریت بر اعلان‌های سیستم
        </Typography>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {/* Filters and Actions */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                placeholder="جستجو در اعلان‌ها..."
                value={searchTerm}
                onChange={handleSearch}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>دسته‌بندی</InputLabel>
                <Select
                  value={categoryFilter}
                  label="دسته‌بندی"
                  onChange={handleCategoryFilterChange}
                >
                  <MenuItem value="all">همه</MenuItem>
                  <MenuItem value="conversation">گفتگو</MenuItem>
                  <MenuItem value="website">وب‌سایت</MenuItem>
                  <MenuItem value="security">امنیت</MenuItem>
                  <MenuItem value="system">سیستم</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>نوع</InputLabel>
                <Select
                  value={typeFilter}
                  label="نوع"
                  onChange={handleTypeFilterChange}
                >
                  <MenuItem value="all">همه</MenuItem>
                  <MenuItem value="info">اطلاعات</MenuItem>
                  <MenuItem value="success">موفقیت</MenuItem>
                  <MenuItem value="warning">هشدار</MenuItem>
                  <MenuItem value="error">خطا</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControlLabel
                control={
                  <Switch
                    checked={showUnreadOnly}
                    onChange={(e) => setShowUnreadOnly(e.target.checked)}
                  />
                }
                label="فقط نخوانده‌ها"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button
                  variant="outlined"
                  startIcon={<Refresh />}
                  onClick={fetchNotifications}
                >
                  بروزرسانی
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={() => {/* TODO: Open send notification dialog */}}
                >
                  ارسال اعلان
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Notifications Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>کاربر</TableCell>
                  <TableCell>عنوان</TableCell>
                  <TableCell>دسته‌بندی</TableCell>
                  <TableCell>نوع</TableCell>
                  <TableCell>وضعیت</TableCell>
                  <TableCell>تاریخ</TableCell>
                  <TableCell>عملیات</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {notifications.map((notification) => (
                  <TableRow key={notification.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Avatar sx={{ width: 32, height: 32 }}>
                          {notification.user_email?.charAt(0).toUpperCase()}
                        </Avatar>
                        <Typography variant="body2">
                          {notification.user_email}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 500 }}>
                        {notification.title}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {notification.message.substring(0, 50)}...
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getCategoryIcon(notification.category)}
                        label={notification.category}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getNotificationIcon(notification.type)}
                        <Typography variant="body2">
                          {notification.type}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={notification.is_read ? 'خوانده شده' : 'نخوانده'}
                        color={getStatusColor(notification.is_read)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Box>
                        <Typography variant="body2">
                          {formatDate(notification.created_at)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {formatTime(notification.created_at)}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="مشاهده جزئیات">
                          <IconButton
                            size="small"
                            onClick={() => handleViewNotification(notification)}
                          >
                            <Visibility />
                          </IconButton>
                        </Tooltip>
                        {!notification.is_read && (
                          <Tooltip title="علامت‌گذاری به عنوان خوانده شده">
                            <IconButton
                              size="small"
                              onClick={() => handleMarkAsRead(notification.id)}
                            >
                              <MarkEmailRead />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="حذف">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleDeleteNotification(notification.id)}
                          >
                            <Delete />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(event, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Notification Details Dialog */}
      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {selectedNotification && getNotificationIcon(selectedNotification.type)}
            <Typography variant="h6">
              جزئیات اعلان
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedNotification && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="h6" sx={{ mb: 1 }}>
                    {selectedNotification.title}
                  </Typography>
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    {selectedNotification.message}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    کاربر: {selectedNotification.user_email}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    تاریخ: {formatDate(selectedNotification.created_at)} {formatTime(selectedNotification.created_at)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    دسته‌بندی: {selectedNotification.category}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    نوع: {selectedNotification.type}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    وضعیت: {selectedNotification.is_read ? 'خوانده شده' : 'نخوانده'}
                  </Typography>
                </Grid>
                {selectedNotification.extra_data && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="text.secondary">
                      اطلاعات اضافی: {JSON.stringify(selectedNotification.extra_data, null, 2)}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>
            بستن
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NotificationManagement;
