import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip,
  LinearProgress,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  InputAdornment,
  Divider,
  IconButton,
  Tooltip,
  Grid,
  Alert
} from '@mui/material';
import {
  Search,
  FilterList,
  Language,
  Chat,
  Settings,
  Add,
  Edit,
  Delete,
  Visibility,
  CalendarToday,
  AccessTime,
  Person
} from '@mui/icons-material';
import { dashboard } from '../../services/api';

const UserHistory = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [historyData, setHistoryData] = useState([]);
  const [stats, setStats] = useState({
    websites_added: 0,
    conversations: 0,
    crawls_completed: 0,
    settings_changed: 0
  });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchHistoryData();
  }, [page, filter, searchTerm]);

  const fetchHistoryData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('Fetching history with params:', { page, filter, searchTerm });

      const response = await dashboard.getUserHistory(
        page,
        20,
        filter === 'all' ? null : filter,
        searchTerm || null
      );

      console.log('History response:', response);

      setHistoryData(response.activities || []);
      setStats(response.stats || {});
      setTotal(response.total || 0);
    } catch (err) {
      setError('خطا در دریافت تاریخچه فعالیت‌ها');
      console.error('Error fetching history:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fa-IR');
  };

  const formatTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('fa-IR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'success';
      case 'completed': return 'info';
      case 'pending': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'active': return 'فعال';
      case 'completed': return 'تکمیل شده';
      case 'pending': return 'در انتظار';
      case 'error': return 'خطا';
      default: return 'نامشخص';
    }
  };

  const getIconComponent = (iconName) => {
    switch (iconName) {
      case 'Language': return <Language />;
      case 'Chat': return <Chat />;
      case 'Settings': return <Settings />;
      case 'Edit': return <Edit />;
      default: return <Language />;
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <LinearProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="outlined" onClick={fetchHistoryData}>
          تلاش مجدد
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
          تاریخچه فعالیت‌ها
        </Typography>
        <Typography variant="body1" color="text.secondary">
          مشاهده تمام فعالیت‌ها و تغییرات انجام شده
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
            <TextField
              size="small"
              placeholder="جستجو در تاریخچه..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              sx={{ minWidth: 250 }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <Search sx={{ color: 'text.secondary' }} />
                  </InputAdornment>
                )
              }}
            />

            <FilterList sx={{ color: 'text.secondary' }} />

            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>نوع فعالیت</InputLabel>
              <Select
                value={filter}
                label="نوع فعالیت"
                onChange={(e) => setFilter(e.target.value)}
              >
                <MenuItem value="all">همه فعالیت‌ها</MenuItem>
                <MenuItem value="website_added">افزودن وب‌سایت</MenuItem>
                <MenuItem value="conversation_started">شروع گفتگو</MenuItem>
                <MenuItem value="conversation_ended">پایان گفتگو</MenuItem>
                <MenuItem value="settings_changed">تغییر تنظیمات</MenuItem>
                <MenuItem value="crawl_completed">تکمیل کراول</MenuItem>
                <MenuItem value="website_updated">به‌روزرسانی وب‌سایت</MenuItem>
              </Select>
            </FormControl>

            <Button
              variant="outlined"
              size="small"
              onClick={() => {
                setFilter('all');
                setSearchTerm('');
                setPage(1);
              }}
            >
              پاک کردن فیلترها
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* History List */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              فعالیت‌های اخیر ({historyData.length})
            </Typography>
            <Chip
              label={`نمایش ${historyData.length} از ${total} فعالیت`}
              size="small"
              variant="outlined"
            />
          </Box>

          {historyData.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                هیچ فعالیتی یافت نشد
              </Typography>
              <Typography variant="body2" color="text.secondary">
                فیلترهای خود را تغییر دهید یا فعالیت جدیدی انجام دهید
              </Typography>
            </Box>
          ) : (
            <List sx={{ p: 0 }}>
              {historyData.map((item, index) => (
                <React.Fragment key={item.id}>
                  <ListItem sx={{ px: 0, py: 2 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: `${item.color}.main` }}>
                        {getIconComponent(item.icon)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                          <Typography variant="body1" sx={{ fontWeight: 500 }}>
                            {item.title}
                          </Typography>
                          <Chip
                            label={getStatusText(item.status)}
                            size="small"
                            color={getStatusColor(item.status)}
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {item.description}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <Language sx={{ fontSize: 16, color: 'text.secondary' }} />
                              <Typography variant="caption" color="text.secondary">
                                {item.website}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <CalendarToday sx={{ fontSize: 16, color: 'text.secondary' }} />
                              <Typography variant="caption" color="text.secondary">
                                {formatDate(item.timestamp)}
                              </Typography>
                            </Box>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                              <AccessTime sx={{ fontSize: 16, color: 'text.secondary' }} />
                              <Typography variant="caption" color="text.secondary">
                                {formatTime(item.timestamp)}
                              </Typography>
                            </Box>
                          </Box>
                        </Box>
                      }
                    />
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="مشاهده جزئیات">
                        <IconButton size="small">
                          <Visibility />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                  {index < historyData.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mt: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                {stats.websites_added}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                وب‌سایت‌های اضافه شده
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main', mb: 1 }}>
                {stats.conversations}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                گفتگوهای انجام شده
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main', mb: 1 }}>
                {stats.settings_changed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                تغییرات تنظیمات
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'info.main', mb: 1 }}>
                {stats.crawls_completed}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                کراول‌های تکمیل شده
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default UserHistory;
