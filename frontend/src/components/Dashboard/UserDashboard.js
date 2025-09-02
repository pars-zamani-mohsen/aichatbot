import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Avatar,
    LinearProgress,
    Chip,
    List,
    ListItem,
    ListItemText,
    ListItemAvatar,
    Divider,
    Button,
    useTheme
} from '@mui/material';
import {
    TrendingUp,
    TrendingDown,
    Language,
    Chat,
    Assessment,
    Speed,
    Storage,
    History,
    Settings
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { websites, dashboard } from '../../services/api';

const UserDashboard = () => {
    const theme = useTheme();
    const navigate = useNavigate();
    const [stats, setStats] = useState({
        totalWebsites: 0,
        totalConversations: 0,
        totalMessages: 0,
        activeWebsites: 0
    });

    const [recentActivity, setRecentActivity] = useState([]);
    const [loading, setLoading] = useState(true);
    const [websiteList, setWebsiteList] = useState([]);
    const [chartData, setChartData] = useState([]);

    useEffect(() => {
        const fetchData = async () => {
            let websitesData = []; // تعریف متغیر در ابتدای تابع

            try {
                setLoading(true);

                // دریافت وب‌سایت‌های کاربر
                websitesData = await websites.getAll();
                setWebsiteList(websitesData);

                // دریافت آمار داشبورد
                const dashboardStats = await dashboard.getUserStats();

                // محاسبه آمار با بررسی وجود داده‌ها
                setStats({
                    totalWebsites: dashboardStats?.websites?.total || 0,
                    totalConversations: dashboardStats?.chats?.total || 0,
                    totalMessages: dashboardStats?.messages?.total || 0,
                    activeWebsites: dashboardStats?.websites?.ready || 0,
                    // اضافه کردن trend ها
                    chatTrend: dashboardStats?.chats?.trend || 0,
                    messageTrend: dashboardStats?.messages?.trend || 0
                });

                // دریافت فعالیت‌های اخیر
                const recentActivityData = await dashboard.getUserRecentActivity(5);

                // دریافت آمار هفتگی
                const weeklyStats = await dashboard.getWeeklyStats();

                setChartData(weeklyStats);

                // تبدیل داده‌ها به فرمت مورد نیاز
                const activities = [];

                // وب‌سایت‌های جدید
                (recentActivityData?.recent_websites || []).slice(0, 2).forEach(website => {
                    activities.push({
                        id: `website-${website.id}`,
                        type: 'website',
                        action: 'وب‌سایت جدید اضافه شد',
                        time: formatTimeAgo(website.created_at),
                        website: website.name
                    });
                });

                // چت‌های جدید
                (recentActivityData?.recent_chats || []).slice(0, 2).forEach(chat => {
                    activities.push({
                        id: `chat-${chat.id}`,
                        type: 'conversation',
                        action: 'گفتگوی جدید شروع شد',
                        time: formatTimeAgo(chat.created_at),
                        website: chat.website_name
                    });
                });

                // پیام‌های جدید
                (recentActivityData?.recent_messages || []).slice(0, 1).forEach(message => {
                    activities.push({
                        id: `message-${message.id}`,
                        type: 'message',
                        action: 'پیام جدید دریافت شد',
                        time: formatTimeAgo(message.created_at),
                        website: message.website_name
                    });
                });

                setRecentActivity(activities);
            } catch (error) {
                console.error('Error fetching dashboard data:', error);

                // اگر درخواست abort شده یا timeout، از داده‌های خالی استفاده کنیم
                if (error.code === 'ECONNABORTED' || error.message === 'Request aborted' || error.message.includes('timeout')) {
                    setStats({
                        totalWebsites: Array.isArray(websitesData) ? websitesData.length : 0,
                        totalConversations: 0,
                        totalMessages: 0,
                        activeWebsites: Array.isArray(websitesData) ? websitesData.filter(w => w.status === 'completed').length : 0,
                        chatTrend: 0,
                        messageTrend: 0
                    });
                    setChartData([
                        { day: 'دوشنبه', conversations: 0, messages: 0 },
                        { day: 'سه‌شنبه', conversations: 0, messages: 0 },
                        { day: 'چهارشنبه', conversations: 0, messages: 0 },
                        { day: 'پنج‌شنبه', conversations: 0, messages: 0 },
                        { day: 'جمعه', conversations: 0, messages: 0 },
                        { day: 'شنبه', conversations: 0, messages: 0 },
                        { day: 'یکشنبه', conversations: 0, messages: 0 },
                    ]);
                    setRecentActivity([]);
                } else {
                    // در صورت خطای دیگر، از داده‌های خالی استفاده می‌کنیم
                    setStats({
                        totalWebsites: Array.isArray(websitesData) ? websitesData.length : 0,
                        totalConversations: 0,
                        totalMessages: 0,
                        activeWebsites: Array.isArray(websitesData) ? websitesData.filter(w => w.status === 'completed').length : 0,
                        chatTrend: 0,
                        messageTrend: 0
                    });
                    setChartData([
                        { day: 'دوشنبه', conversations: 0, messages: 0 },
                        { day: 'سه‌شنبه', conversations: 0, messages: 0 },
                        { day: 'چهارشنبه', conversations: 0, messages: 0 },
                        { day: 'پنج‌شنبه', conversations: 0, messages: 0 },
                        { day: 'جمعه', conversations: 0, messages: 0 },
                        { day: 'شنبه', conversations: 0, messages: 0 },
                        { day: 'یکشنبه', conversations: 0, messages: 0 },
                    ]);
                    setRecentActivity([]);
                }
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

    const StatCard = ({ title, value, icon, color, subtitle, trend }) => (
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
                {trend !== undefined && (
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
                    bgcolor: activity.type === 'website' ? 'primary.main' :
                        activity.type === 'conversation' ? 'success.main' :
                            activity.type === 'crawl' ? 'info.main' : 'warning.main',
                    width: 32,
                    height: 32
                }}>
                    {activity.type === 'website' ? <Language /> :
                        activity.type === 'conversation' ? <Chat /> :
                            activity.type === 'crawl' ? <Speed /> : <Assessment />}
                </Avatar>
            </ListItemAvatar>
            <ListItemText
                primary={activity.action}
                secondary={`${activity.website} • ${activity.time}`}
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
                    داشبورد شخصی
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    نمای کلی فعالیت‌ها و وب‌سایت‌های شما
                </Typography>
            </Box>

            {/* Stats Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="وب‌سایت‌های من"
                        value={stats.totalWebsites}
                        icon={<Language />}
                        color="#667eea"
                        subtitle={`${stats.activeWebsites} وب‌سایت فعال`}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="گفتگوها"
                        value={stats.totalConversations}
                        icon={<Chat />}
                        color="#10b981"
                        subtitle={`${stats.totalConversations} گفتگو`}
                        trend={stats.chatTrend}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="پیام‌ها"
                        value={stats.totalMessages}
                        icon={<Assessment />}
                        color="#f59e0b"
                        subtitle={`${stats.totalMessages} پیام`}
                        trend={stats.messageTrend}
                    />
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <StatCard
                        title="وب‌سایت‌های فعال"
                        value={stats.activeWebsites}
                        icon={<Speed />}
                        color="#ef4444"
                        subtitle="آماده برای چت"
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
                                    <Chip label="پیام‌ها" size="small" color="secondary" />
                                </Box>
                            </Box>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="day" />
                                    <YAxis />
                                    <Tooltip />
                                    <Line type="monotone" dataKey="conversations" stroke="#667eea" strokeWidth={2} />
                                    <Line type="monotone" dataKey="messages" stroke="#10b981" strokeWidth={2} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Recent Activity */}
                <Grid item xs={12} lg={4}>
                    <Card sx={{ height: 400 }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    فعالیت‌های اخیر
                                </Typography>
                                <Button size="small" color="primary" onClick={() => navigate('/history')}>
                                    مشاهده همه
                                </Button>
                            </Box>
                            <List sx={{ p: 0, maxHeight: 300, overflow: 'auto' }}>
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

                {/* Website Status */}
                <Grid item xs={12} lg={6}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                                وضعیت وب‌سایت‌ها
                            </Typography>
                            {websiteList.length === 0 ? (
                                <Box sx={{ textAlign: 'center', py: 4 }}>
                                    <Language sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                                    <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                                        هنوز وب‌سایتی اضافه نکرده‌اید
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        اولین وب‌سایت خود را اضافه کنید تا شروع کنید
                                    </Typography>
                                </Box>
                            ) : (
                                <Box>
                                    {websiteList.map((website) => (
                                        <Box key={website.id} sx={{ mb: 2, p: 2, border: '1px solid #e5e7eb', borderRadius: 2 }}>
                                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                                <Typography variant="body1" sx={{ fontWeight: 500 }}>
                                                    {website.name || website.url}
                                                </Typography>
                                                <Chip
                                                    label={website.status === 'completed' ? 'فعال' : 'در حال پردازش'}
                                                    size="small"
                                                    color={website.status === 'completed' ? 'success' : 'warning'}
                                                />
                                            </Box>
                                            <Typography variant="body2" color="text.secondary">
                                                {website.url}
                                            </Typography>
                                        </Box>
                                    ))}
                                </Box>
                            )}
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
                                        startIcon={<Language />}
                                        sx={{ py: 2 }}
                                        onClick={() => navigate('/websites')}
                                    >
                                        افزودن وب‌سایت
                                    </Button>
                                </Grid>
                                <Grid item xs={6}>
                                    <Button
                                        variant="outlined"
                                        fullWidth
                                        startIcon={<Chat />}
                                        sx={{ py: 2 }}
                                        onClick={() => navigate('/websites')}
                                    >
                                        شروع چت
                                    </Button>
                                </Grid>
                                <Grid item xs={6}>
                                    <Button
                                        variant="outlined"
                                        fullWidth
                                        startIcon={<History />}
                                        sx={{ py: 2 }}
                                        onClick={() => navigate('/history')}
                                    >
                                        مشاهده تاریخچه
                                    </Button>
                                </Grid>
                                <Grid item xs={6}>
                                    <Button
                                        variant="outlined"
                                        fullWidth
                                        startIcon={<Settings />}
                                        sx={{ py: 2 }}
                                        onClick={() => navigate('/settings')}
                                    >
                                        تنظیمات
                                    </Button>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default UserDashboard;
