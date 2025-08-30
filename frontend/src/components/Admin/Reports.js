import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Chip,
    LinearProgress,
    Alert,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper
} from '@mui/material';
import {
    TrendingUp,
    TrendingDown,
    Language,
    Chat,
    People,
    Assessment,
    Download,
    Refresh
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import { dashboard } from '../../services/api';

const Reports = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [timeRange, setTimeRange] = useState('7d');
    const [stats, setStats] = useState({
        users: { total: 0, active: 0, trend: 0 },
        websites: { total: 0, active: 0, trend: 0 },
        conversations: { total: 0, trend: 0 },
        messages: { total: 0, trend: 0 }
    });
    const [weeklyData, setWeeklyData] = useState([]);
    const [topWebsites, setTopWebsites] = useState([]);
    const [topUsers, setTopUsers] = useState([]);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError('');

            // دریافت آمار کلی
            const adminStats = await dashboard.getAdminStats();
            setStats(adminStats);

            // دریافت آمار هفتگی
            const weeklyStats = await dashboard.getAdminWeeklyStats();
            setWeeklyData(weeklyStats);

            // دریافت وب‌سایت‌های برتر
            const websitesResponse = await dashboard.getAdminWebsites(1, 10);
            setTopWebsites(websitesResponse.websites);

            // دریافت کاربران برتر
            const usersResponse = await dashboard.getAdminUsers(1, 10);
            setTopUsers(usersResponse.users);

        } catch (err) {
            console.error('Error fetching reports data:', err);
            setError('خطا در دریافت داده‌های گزارش');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [timeRange]);

    const handleExport = (type) => {
        // اینجا می‌توان منطق export را اضافه کرد
        console.log(`Exporting ${type} data...`);
    };

    const formatNumber = (num) => {
        return new Intl.NumberFormat('fa-IR').format(num);
    };

    const getTrendIcon = (trend) => {
        if (!trend) return null;
        if (trend > 0) {
            return <TrendingUp sx={{ color: 'success.main', fontSize: 16 }} />;
        } else if (trend < 0) {
            return <TrendingDown sx={{ color: 'error.main', fontSize: 16 }} />;
        }
        return null;
    };

    const getTrendColor = (trend) => {
        if (!trend) return 'text.secondary';
        if (trend > 0) return 'success.main';
        if (trend < 0) return 'error.main';
        return 'text.secondary';
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
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                        گزارشات سیستم
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        آمار و تحلیل عملکرد سیستم
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>بازه زمانی</InputLabel>
                        <Select
                            value={timeRange}
                            onChange={(e) => setTimeRange(e.target.value)}
                            label="بازه زمانی"
                        >
                            <MenuItem value="7d">7 روز گذشته</MenuItem>
                            <MenuItem value="30d">30 روز گذشته</MenuItem>
                            <MenuItem value="90d">90 روز گذشته</MenuItem>
                        </Select>
                    </FormControl>
                    <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={fetchData}
                        disabled={loading}
                    >
                        به‌روزرسانی
                    </Button>
                </Box>
            </Box>

            {/* Error Alert */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}

            {/* Summary Cards */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        color: 'white'
                    }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <Box>
                                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                                        {formatNumber(stats.users?.total || 0)}
                                    </Typography>
                                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                        کل کاربران
                                    </Typography>
                                    {stats.users?.trend !== 0 && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                            {getTrendIcon(stats.users?.trend)}
                                            <Typography variant="caption" sx={{ ml: 0.5, color: getTrendColor(stats.users?.trend) }}>
                                                {Math.abs(stats.users?.trend || 0)}% از هفته گذشته
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>
                                <People sx={{ fontSize: 40, opacity: 0.8 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                        color: 'white'
                    }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <Box>
                                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                                        {formatNumber(stats.websites?.total || 0)}
                                    </Typography>
                                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                        کل وب‌سایت‌ها
                                    </Typography>
                                    {stats.websites?.trend !== 0 && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                            {getTrendIcon(stats.websites?.trend)}
                                            <Typography variant="caption" sx={{ ml: 0.5, color: getTrendColor(stats.websites?.trend) }}>
                                                {Math.abs(stats.websites?.trend || 0)}% از هفته گذشته
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>
                                <Language sx={{ fontSize: 40, opacity: 0.8 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                        color: 'white'
                    }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <Box>
                                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                                        {formatNumber(stats.conversations?.total || 0)}
                                    </Typography>
                                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                        کل گفتگوها
                                    </Typography>
                                    {stats.conversations?.trend !== 0 && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                            {getTrendIcon(stats.conversations?.trend)}
                                            <Typography variant="caption" sx={{ ml: 0.5, color: getTrendColor(stats.conversations?.trend) }}>
                                                {Math.abs(stats.conversations?.trend || 0)}% از هفته گذشته
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>
                                <Chat sx={{ fontSize: 40, opacity: 0.8 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                <Grid item xs={12} sm={6} md={3}>
                    <Card sx={{
                        background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                        color: 'white'
                    }}>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <Box>
                                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                                        {formatNumber(stats.messages?.total || 0)}
                                    </Typography>
                                    <Typography variant="body2" sx={{ opacity: 0.9 }}>
                                        کل پیام‌ها
                                    </Typography>
                                    {stats.messages?.trend !== 0 && (
                                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                                            {getTrendIcon(stats.messages?.trend)}
                                            <Typography variant="caption" sx={{ ml: 0.5, color: getTrendColor(stats.messages?.trend) }}>
                                                {Math.abs(stats.messages?.trend || 0)}% از هفته گذشته
                                            </Typography>
                                        </Box>
                                    )}
                                </Box>
                                <Assessment sx={{ fontSize: 40, opacity: 0.8 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Charts */}
            <Grid container spacing={3} sx={{ mb: 4 }}>
                {/* Weekly Activity Chart */}
                <Grid item xs={12} lg={8}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    فعالیت هفتگی
                                </Typography>
                                <Button
                                    size="small"
                                    startIcon={<Download />}
                                    onClick={() => handleExport('weekly')}
                                >
                                    دانلود
                                </Button>
                            </Box>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={weeklyData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis dataKey="day" />
                                    <YAxis />
                                    <Tooltip />
                                    <Line type="monotone" dataKey="conversations" stroke="#667eea" strokeWidth={2} name="گفتگوها" />
                                    <Line type="monotone" dataKey="users" stroke="#10b981" strokeWidth={2} name="کاربران فعال" />
                                    <Line type="monotone" dataKey="websites" stroke="#f59e0b" strokeWidth={2} name="وب‌سایت‌های جدید" />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Status Distribution */}
                <Grid item xs={12} lg={4}>
                    <Card>
                        <CardContent>
                            <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                                وضعیت وب‌سایت‌ها
                            </Typography>
                            <ResponsiveContainer width="100%" height={200}>
                                <PieChart>
                                    <Pie
                                        data={[
                                            { name: 'فعال', value: stats.websites?.active || 0, color: '#10b981' },
                                            { name: 'غیرفعال', value: (stats.websites?.total || 0) - (stats.websites?.active || 0), color: '#ef4444' }
                                        ]}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={40}
                                        outerRadius={80}
                                        paddingAngle={5}
                                        dataKey="value"
                                    >
                                        {[
                                            { name: 'فعال', value: stats.websites?.active || 0, color: '#10b981' },
                                            { name: 'غیرفعال', value: (stats.websites?.total || 0) - (stats.websites?.active || 0), color: '#ef4444' }
                                        ].map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                            <Box sx={{ mt: 2 }}>
                                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#10b981', mr: 1 }} />
                                    <Typography variant="body2">فعال: {stats.websites?.active || 0}</Typography>
                                </Box>
                                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: '#ef4444', mr: 1 }} />
                                    <Typography variant="body2">غیرفعال: {(stats.websites?.total || 0) - (stats.websites?.active || 0)}</Typography>
                                </Box>
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Tables */}
            <Grid container spacing={3}>
                {/* Top Websites */}
                <Grid item xs={12} lg={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    وب‌سایت‌های برتر
                                </Typography>
                                <Button
                                    size="small"
                                    startIcon={<Download />}
                                    onClick={() => handleExport('websites')}
                                >
                                    دانلود
                                </Button>
                            </Box>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>وب‌سایت</TableCell>
                                            <TableCell>مالک</TableCell>
                                            <TableCell>وضعیت</TableCell>
                                            <TableCell>گفتگوها</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {topWebsites.map((website) => (
                                            <TableRow key={website.id}>
                                                <TableCell>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        {website.name}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {website.domain}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell>{website.owner_email}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={website.status === 'ready' ? 'فعال' : website.status}
                                                        color={website.status === 'ready' ? 'success' : 'warning'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip label={website.conversations_count} size="small" />
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Top Users */}
                <Grid item xs={12} lg={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    کاربران برتر
                                </Typography>
                                <Button
                                    size="small"
                                    startIcon={<Download />}
                                    onClick={() => handleExport('users')}
                                >
                                    دانلود
                                </Button>
                            </Box>
                            <TableContainer>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>کاربر</TableCell>
                                            <TableCell>نقش</TableCell>
                                            <TableCell>وضعیت</TableCell>
                                            <TableCell>وب‌سایت‌ها</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {topUsers.map((user) => (
                                            <TableRow key={user.id}>
                                                <TableCell>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        {user.email}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={user.role === 'admin' ? 'مدیر' : 'کاربر'}
                                                        color={user.role === 'admin' ? 'error' : 'default'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={user.is_active ? 'فعال' : 'غیرفعال'}
                                                        color={user.is_active ? 'success' : 'error'}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip label={user.websites_count} size="small" />
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default Reports;
