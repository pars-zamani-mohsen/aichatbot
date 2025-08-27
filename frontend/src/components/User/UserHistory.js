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
  Grid
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

const UserHistory = () => {
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // داده‌های نمونه
  const historyData = [
    {
      id: 1,
      type: 'website_added',
      title: 'وب‌سایت جدید اضافه شد',
      description: 'وب‌سایت example.com به سیستم اضافه شد',
      website: 'example.com',
      timestamp: '2024-01-15T10:30:00Z',
      status: 'completed',
      icon: <Language />,
      color: 'primary'
    },
    {
      id: 2,
      type: 'conversation_started',
      title: 'گفتگوی جدید شروع شد',
      description: 'گفتگوی جدید در وب‌سایت test.com شروع شد',
      website: 'test.com',
      timestamp: '2024-01-15T09:15:00Z',
      status: 'active',
      icon: <Chat />,
      color: 'success'
    },
    {
      id: 3,
      type: 'settings_changed',
      title: 'تنظیمات تغییر کرد',
      description: 'تنظیمات RAG برای وب‌سایت demo.com تغییر کرد',
      website: 'demo.com',
      timestamp: '2024-01-14T16:45:00Z',
      status: 'completed',
      icon: <Settings />,
      color: 'warning'
    },
    {
      id: 4,
      type: 'crawl_completed',
      title: 'کراول تکمیل شد',
      description: 'کراول وب‌سایت site.com با موفقیت تکمیل شد',
      website: 'site.com',
      timestamp: '2024-01-14T14:20:00Z',
      status: 'completed',
      icon: <Language />,
      color: 'info'
    },
    {
      id: 5,
      type: 'conversation_ended',
      title: 'گفتگو پایان یافت',
      description: 'گفتگوی وب‌سایت example.com پایان یافت',
      website: 'example.com',
      timestamp: '2024-01-14T11:30:00Z',
      status: 'completed',
      icon: <Chat />,
      color: 'secondary'
    },
    {
      id: 6,
      type: 'website_updated',
      title: 'وب‌سایت به‌روزرسانی شد',
      description: 'تنظیمات وب‌سایت test.com به‌روزرسانی شد',
      website: 'test.com',
      timestamp: '2024-01-13T15:10:00Z',
      status: 'completed',
      icon: <Edit />,
      color: 'primary'
    }
  ];

  useEffect(() => {
    // شبیه‌سازی دریافت داده‌ها
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

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

  const filteredHistory = historyData.filter(item => {
    const matchesFilter = filter === 'all' || item.type === filter;
    const matchesSearch = item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.website.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

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
              فعالیت‌های اخیر ({filteredHistory.length})
            </Typography>
            <Chip 
              label={`نمایش ${filteredHistory.length} از ${historyData.length} فعالیت`} 
              size="small" 
              variant="outlined" 
            />
          </Box>

          {filteredHistory.length === 0 ? (
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
              {filteredHistory.map((item, index) => (
                <React.Fragment key={item.id}>
                  <ListItem sx={{ px: 0, py: 2 }}>
                    <ListItemAvatar>
                      <Avatar sx={{ bgcolor: `${item.color}.main` }}>
                        {item.icon}
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
                  {index < filteredHistory.length - 1 && <Divider />}
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
                {historyData.filter(h => h.type === 'website_added').length}
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
                {historyData.filter(h => h.type.includes('conversation')).length}
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
                {historyData.filter(h => h.type === 'settings_changed').length}
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
                {historyData.filter(h => h.type === 'crawl_completed').length}
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
