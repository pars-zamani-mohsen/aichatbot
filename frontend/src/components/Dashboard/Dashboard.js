import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip
} from '@mui/material';
import {
  Web as WebIcon,
  Chat as ChatIcon,
  Message as MessageIcon,
  Description as PageIcon,
  TrendingUp as TrendingIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import api from '../../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentActivity, setRecentActivity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [statsResponse, activityResponse] = await Promise.all([
        api.get('/api/dashboard/stats'),
        api.get('/api/dashboard/recent-activity')
      ]);
      
      setStats(statsResponse.data);
      setRecentActivity(activityResponse.data);
    } catch (err) {
      setError('خطا در دریافت اطلاعات داشبورد');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready': return 'success';
      case 'crawling': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'ready': return 'آماده';
      case 'crawling': return 'در حال کراول';
      case 'error': return 'خطا';
      default: return status;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        داشبورد مدیریت
      </Typography>

      {/* آمار کلی */}
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <WebIcon color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h4">{stats.websites.total}</Typography>
                    <Typography color="textSecondary">کل وب‌سایت‌ها</Typography>
                  </Box>
                </Box>
                <Box sx={{ mt: 2 }}>
                  <Chip 
                    label={`${stats.websites.ready} آماده`} 
                    color="success" 
                    size="small" 
                    sx={{ mr: 1 }} 
                  />
                  <Chip 
                    label={`${stats.websites.crawling} در حال کراول`} 
                    color="warning" 
                    size="small" 
                    sx={{ mr: 1 }} 
                  />
                  {stats.websites.error > 0 && (
                    <Chip 
                      label={`${stats.websites.error} خطا`} 
                      color="error" 
                      size="small" 
                    />
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <ChatIcon color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h4">{stats.chats.total}</Typography>
                    <Typography color="textSecondary">کل مکالمات</Typography>
                    <Typography variant="body2" color="success.main">
                      {stats.chats.today} امروز
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <MessageIcon color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h4">{stats.messages.total}</Typography>
                    <Typography color="textSecondary">کل پیام‌ها</Typography>
                    <Typography variant="body2" color="success.main">
                      {stats.messages.today} امروز
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center">
                  <PageIcon color="primary" sx={{ mr: 2 }} />
                  <Box>
                    <Typography variant="h4">{stats.pages.total_crawled}</Typography>
                    <Typography color="textSecondary">صفحات کراول شده</Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* فعالیت‌های اخیر */}
      {recentActivity && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                مکالمات اخیر
              </Typography>
              <List>
                {recentActivity.recent_chats.map((chat, index) => (
                  <React.Fragment key={chat.id}>
                    <ListItem>
                      <ListItemText
                        primary={chat.website_name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              {new Date(chat.created_at).toLocaleString('fa-IR')}
                            </Typography>
                            <Typography variant="body2">
                              {chat.message_count} پیام
                            </Typography>
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < recentActivity.recent_chats.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                وب‌سایت‌های اخیر
              </Typography>
              <List>
                {recentActivity.recent_websites.map((website, index) => (
                  <React.Fragment key={website.id}>
                    <ListItem>
                      <ListItemText
                        primary={website.name}
                        secondary={
                          <Box>
                            <Typography variant="body2" color="textSecondary">
                              {new Date(website.created_at).toLocaleString('fa-IR')}
                            </Typography>
                            <Chip 
                              label={getStatusText(website.status)} 
                              color={getStatusColor(website.status)} 
                              size="small" 
                            />
                          </Box>
                        }
                      />
                    </ListItem>
                    {index < recentActivity.recent_websites.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Dashboard;
