import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  IconButton,
  Avatar,
  LinearProgress,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Button,
  Paper,
  useTheme
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Language,
  Chat,
  People,
  Assessment,
  Notifications,
  MoreVert,
  Visibility,
  VisibilityOff,
  Speed,
  Storage,
  Security,
  Analytics
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { dashboard } from '../../services/api';

const AdminDashboard = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    totalWebsites: 0,
    totalUsers: 0,
    totalConversations: 0,
    totalMessages: 0,
    activeUsers: 0,
    systemHealth: 95
  });

  const [recentActivity, setRecentActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState([]);

  const pieData = [
    { name: 'فعال', value: 75, color: '#10b981' },
    { name: 'غیرفعال', value: 15, color: '#f59e0b' },
    { name: 'در انتظار', value: 10, color: '#ef4444' },
  ];

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // دریافت آمار ادمین
        const adminStats = await dashboard.getAdminStats();
        setStats({
          totalWebsites: adminStats?.websites?.total || 0,
          totalUsers: adminStats?.users?.total || 0,
          totalConversations: adminStats?.chats?.total || 0,
          totalMessages: adminStats?.messages?.total || 0,
          activeUsers: adminStats?.users?.active || 0,
          systemHealth: 95,
          // اضافه کردن trend ها
          websiteTrend: adminStats?.websites?.trend || 0,
          userTrend: adminStats?.users?.trend || 0,
          chatTrend: adminStats?.chats?.trend || 0,
          messageTrend: adminStats?.messages?.trend || 0
        });

        // دریافت فعالیت‌های اخیر
        const recentActivityData = await dashboard.getAdminRecentActivity(5);

        // دریافت آمار هفتگی
        const weeklyStats = await dashboard.getAdminWeeklyStats();
        setChartData(weeklyStats);

        // تبدیل داده‌ها به فرمت مورد نیاز
        const activities = [];

        // کاربران جدید
        (recentActivityData?.recent_users || []).slice(0, 2).forEach(user => {
          activities.push({
            id: `user-${user.id}`,
            type: 'user',
            action: 'کاربر جدید ثبت‌نام کرد',
            time: formatTimeAgo(user.created_at),
            user: user.email
          });
        });

        // وب‌سایت‌های جدید
        (recentActivityData?.recent_websites || []).slice(0, 2).forEach(website => {
          activities.push({
            id: `website-${website.id}`,
            type: 'website',
            action: 'وب‌سایت جدید اضافه شد',
            time: formatTimeAgo(website.created_at),
            user: website.owner_email
          });
        });

        // چت‌های جدید
        (recentActivityData?.recent_chats || []).slice(0, 1).forEach(chat => {
          activities.push({
            id: `chat-${chat.id}`,
            type: 'conversation',
            action: 'گفتگوی جدید شروع شد',
            time: formatTimeAgo(chat.created_at),
            user: chat.owner_email
          });
        });

        setRecentActivity(activities);
      } catch (error) {
        console.error('Error fetching admin dashboard data:', error);
        // در صورت خطا، از داده‌های خالی استفاده می‌کنیم
        setStats({
          totalWebsites: 0,
          totalUsers: 0,
          totalConversations: 0,
          totalMessages: 0,
          activeUsers: 0,
          systemHealth: 0,
          websiteTrend: 0,
          userTrend: 0,
          chatTrend: 0,
          messageTrend: 0
        });
        setChartData([
          { day: 'شنبه', conversations: 0, users: 0 },
          { day: 'یکشنبه', conversations: 0, users: 0 },
          { day: 'دوشنبه', conversations: 0, users: 0 },
          { day: 'سه‌شنبه', conversations: 0, users: 0 },
          { day: 'چهارشنبه', conversations: 0, users: 0 },
          { day: 'پنج‌شنبه', conversations: 0, users: 0 },
          { day: 'جمعه', conversations: 0, users: 0 },
        ]);
        setRecentActivity([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = Math.floor((now - date) / (1000 * 60));

    if (diffInMinutes < 1) return 'لحظاتی پیش';
    if (diffInMinutes < 60) return `${diffInMinutes} دقیقه پیش`;

    const diffInHours = Math.floor(diffInMinutes / 60);
    if (diffInHours < 24) return `${diffInHours} ساعت پیش`;

    const diffInDays = Math.floor(diffInHours / 24);
    return `${diffInDays} روز پیش`;
  };

  const StatCard = ({ title, value, icon, color, trend, subtitle }) => (
    <Card sx={{
      height: '100%',
      background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
      border: `1px solid ${color}20`,
      transition: 'all 0.3s ease',
      '&:hover': {
        transform: 'translateY(-4px)',
        boxShadow: `0 8px 25px ${color}20`
      }
    }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: color, mb: 1 }}>
              {value}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {title}
            </Typography>
            {subtitle && (
              <Typography variant="caption" color="text.secondary">
                {subtitle}
              </Typography>
            )}
          </Box>
          <Avatar sx={{ bgcolor: color, width: 56, height: 56 }}>
            {icon}
          </Avatar>
        </Box>
        {trend && (
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            {trend > 0 ? (
              <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
            ) : (
              <TrendingDown sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
            )}
            <Typography variant="caption" color={trend > 0 ? 'success.main' : 'error.main'}>
              {Math.abs(trend)}% از هفته گذشته
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );

  const ActivityItem = ({ activity }) => (
    <ListItem sx={{ px: 0 }}>
      <ListItemAvatar>
        <Avatar sx={{
          bgcolor: activity.type === 'user' ? 'primary.main' :
            activity.type === 'website' ? 'success.main' :
              activity.type === 'conversation' ? 'info.main' : 'warning.main',
          width: 32,
          height: 32
        }}>
          {activity.type === 'user' ? <People /> :
            activity.type === 'website' ? <Language /> :
              activity.type === 'conversation' ? <Chat /> : <Notifications />}
        </Avatar>
      </ListItemAvatar>
      <ListItemText
        primary={activity.action}
        secondary={`${activity.user} • ${activity.time}`}
        primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
        secondaryTypographyProps={{ variant: 'caption' }}
      />
    </ListItem>
  );

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
          داشبورد مدیریت
        </Typography>
        <Typography variant="body1" color="text.secondary">
          نمای کلی سیستم و آمار عملکرد
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="کل وب‌سایت‌ها"
            value={stats.totalWebsites}
            icon={<Language />}
            color="#667eea"
            trend={stats.websiteTrend || 0}
            subtitle={`${stats.totalWebsites} وب‌سایت فعال`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="کل کاربران"
            value={stats.totalUsers}
            icon={<People />}
            color="#10b981"
            trend={stats.userTrend || 0}
            subtitle={`${stats.activeUsers} کاربر فعال`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="کل گفتگوها"
            value={stats.totalConversations}
            icon={<Chat />}
            color="#f59e0b"
            trend={stats.chatTrend || 0}
            subtitle={`${stats.totalConversations} گفتگو`}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="پیام‌ها"
            value={stats.totalMessages}
            icon={<Assessment />}
            color="#ef4444"
            trend={stats.messageTrend || 0}
            subtitle={`${stats.totalMessages} پیام`}
          />
        </Grid>
      </Grid>

      {/* Charts and Activity */}
      <Grid container spacing={3}>
        {/* Line Chart */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  آمار هفتگی
                </Typography>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label="گفتگوها" size="small" color="primary" />
                  <Chip label="کاربران" size="small" color="secondary" />
                </Box>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="conversations" stroke="#667eea" strokeWidth={2} />
                  <Line type="monotone" dataKey="users" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Pie Chart */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                وضعیت وب‌سایت‌ها
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 2 }}>
                {pieData.map((item, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: item.color, mr: 1 }} />
                    <Typography variant="body2">{item.name}: {item.value}%</Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                  فعالیت‌های اخیر
                </Typography>
                <Button size="small" color="primary" onClick={() => navigate('/admin/reports')}>
                  مشاهده همه
                </Button>
              </Box>
              <List sx={{ p: 0 }}>
                {recentActivity.map((activity, index) => (
                  <React.Fragment key={activity.id}>
                    <ActivityItem activity={activity} />
                    {index < recentActivity.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                اقدامات سریع
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<People />}
                    sx={{ py: 2 }}
                    onClick={() => navigate('/admin/users')}
                  >
                    مدیریت کاربران
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Language />}
                    sx={{ py: 2 }}
                    onClick={() => navigate('/admin/websites')}
                  >
                    مدیریت وب‌سایت‌ها
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Analytics />}
                    sx={{ py: 2 }}
                    onClick={() => navigate('/admin/reports')}
                  >
                    گزارش‌ها
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<Security />}
                    sx={{ py: 2 }}
                    onClick={() => navigate('/admin/settings')}
                  >
                    تنظیمات سیستم
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* System Health */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                سلامت سیستم
              </Typography>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">CPU</Typography>
                  <Typography variant="body2">45%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={45} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">RAM</Typography>
                  <Typography variant="body2">62%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={62} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                  <Typography variant="body2">Storage</Typography>
                  <Typography variant="body2">78%</Typography>
                </Box>
                <LinearProgress variant="determinate" value={78} sx={{ height: 8, borderRadius: 4 }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Security sx={{ color: 'success.main' }} />
                <Typography variant="body2" color="success.main">
                  سیستم در وضعیت مطلوب
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminDashboard;
