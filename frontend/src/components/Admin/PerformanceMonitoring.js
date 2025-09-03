import React, { useState, useEffect } from 'react';
import {
    Card,
    CardContent,
    CardHeader,
    Grid,
    Button,
    Alert,
    CircularProgress,
    Chip,
    LinearProgress,
    Typography,
    Box,
    Divider,
    Paper
} from '@mui/material';
import {
    Speed,
    Storage,
    Language,
    Cached,
    Warning,
    Favorite,
    Delete,
    Refresh,
    TrendingUp
} from '@mui/icons-material';
import api from '../../services/api';

const PerformanceMonitoring = () => {
    const [loading, setLoading] = useState(false);
    const [systemMetrics, setSystemMetrics] = useState(null);
    const [databaseMetrics, setDatabaseMetrics] = useState(null);
    const [apiMetrics, setApiMetrics] = useState(null);
    const [cacheInfo, setCacheInfo] = useState(null);
    const [alerts, setAlerts] = useState([]);
    const [systemHealth, setSystemHealth] = useState(null);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);

    // دریافت تمام آمار
    const fetchAllMetrics = async () => {
        setLoading(true);
        setError(null);

        try {
            const [
                systemRes,
                dbRes,
                apiRes,
                cacheRes,
                alertsRes,
                healthRes
            ] = await Promise.all([
                api.get('/api/performance/metrics/system'),
                api.get('/api/performance/metrics/database'),
                api.get('/api/performance/metrics/api'),
                api.get('/api/performance/metrics/cache'),
                api.get('/api/performance/alerts'),
                api.get('/api/performance/health')
            ]);

            setSystemMetrics(systemRes.data.data);
            setDatabaseMetrics(dbRes.data.data);
            setApiMetrics(apiRes.data.data);
            setCacheInfo(cacheRes.data.data.cache_info);
            setAlerts(alertsRes.data.data);
            setSystemHealth(healthRes.data.data);
            setLastUpdate(new Date());

        } catch (err) {
            setError('خطا در دریافت آمار عملکرد: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    // پاکسازی cache
    const clearCache = async (pattern = '*') => {
        try {
            const response = await api.post('/api/performance/cache/clear', null, {
                params: { pattern }
            });

            if (response.data.success) {
                alert(`Cache پاک شد: ${response.data.message}`);
                fetchAllMetrics(); // به‌روزرسانی آمار
            }
        } catch (err) {
            alert('خطا در پاکسازی cache: ' + (err.response?.data?.detail || err.message));
        }
    };

    // گرم کردن cache
    const warmUpCache = async () => {
        try {
            const response = await api.post('/api/performance/cache/warm-up');

            if (response.data.success) {
                alert('Cache با موفقیت گرم شد');
                fetchAllMetrics(); // به‌روزرسانی آمار
            }
        } catch (err) {
            alert('خطا در گرم کردن cache: ' + (err.response?.data?.detail || err.message));
        }
    };

    // دریافت وضعیت سلامت
    const getHealthStatusColor = (status) => {
        switch (status) {
            case 'healthy': return 'success';
            case 'warning': return 'warning';
            case 'critical': return 'error';
            default: return 'default';
        }
    };

    // دریافت رنگ برای درصد CPU/Memory
    const getResourceColor = (percent) => {
        if (percent < 50) return 'success';
        if (percent < 80) return 'warning';
        return 'error';
    };

    useEffect(() => {
        fetchAllMetrics();

        // به‌روزرسانی خودکار هر 30 ثانیه
        const interval = setInterval(fetchAllMetrics, 30000);

        return () => clearInterval(interval);
    }, []);

    if (loading && !systemMetrics) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
                <Typography variant="h6" sx={{ ml: 2 }}>
                    در حال دریافت آمار عملکرد...
                </Typography>
            </Box>
        );
    }

    return (
        <Box className="performance-monitoring" sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h4" component="h1">
                    <Speed sx={{ mr: 1, verticalAlign: 'middle' }} />
                    نظارت بر عملکرد سیستم
                </Typography>
                <Box>
                    <Button
                        variant="outlined"
                        onClick={fetchAllMetrics}
                        disabled={loading}
                        sx={{ mr: 1 }}
                        startIcon={<Refresh className={loading ? 'spinning' : ''} />}
                    >
                        به‌روزرسانی
                    </Button>
                    <Button
                        variant="outlined"
                        color="warning"
                        onClick={() => clearCache()}
                        sx={{ mr: 1 }}
                        startIcon={<Delete />}
                    >
                        پاکسازی Cache
                    </Button>
                    <Button
                        variant="outlined"
                        color="info"
                        onClick={warmUpCache}
                        startIcon={<TrendingUp />}
                    >
                        گرم کردن Cache
                    </Button>
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            {lastUpdate && (
                <Alert severity="info" sx={{ mb: 3 }}>
                    آخرین به‌روزرسانی: {lastUpdate.toLocaleString('fa-IR')}
                </Alert>
            )}

            {/* وضعیت سلامت سیستم */}
            {systemHealth && (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Favorite color={getHealthStatusColor(systemHealth.status)} />}
                        title="وضعیت سلامت سیستم"
                        action={
                            <Chip
                                label={systemHealth.status === 'healthy' ? 'سالم' :
                                    systemHealth.status === 'warning' ? 'هشدار' : 'بحرانی'}
                                color={getHealthStatusColor(systemHealth.status)}
                                variant="outlined"
                            />
                        }
                    />
                    <CardContent>
                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Typography variant="body2">
                                    <strong>وضعیت:</strong> {systemHealth.status}
                                </Typography>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Typography variant="body2">
                                    <strong>آخرین بررسی:</strong> {systemHealth.timestamp ?
                                        new Date(systemHealth.timestamp).toLocaleString('fa-IR') : 'نامشخص'}
                                </Typography>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            )}

            {/* آمار سیستم */}
            {systemMetrics && (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Storage />}
                        title="آمار سیستم"
                    />
                    <CardContent>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography
                                        variant="h4"
                                        color={getResourceColor(systemMetrics.cpu?.avg || 0)}
                                    >
                                        {systemMetrics.cpu?.avg?.toFixed(1) || 0}%
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        CPU متوسط
                                    </Typography>
                                    <LinearProgress
                                        variant="determinate"
                                        value={systemMetrics.cpu?.avg || 0}
                                        color={getResourceColor(systemMetrics.cpu?.avg || 0)}
                                        sx={{ mt: 1, height: 8, borderRadius: 4 }}
                                    />
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography
                                        variant="h4"
                                        color={getResourceColor(systemMetrics.memory?.avg || 0)}
                                    >
                                        {systemMetrics.memory?.avg?.toFixed(1) || 0}%
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        حافظه متوسط
                                    </Typography>
                                    <LinearProgress
                                        variant="determinate"
                                        value={systemMetrics.memory?.avg || 0}
                                        color={getResourceColor(systemMetrics.memory?.avg || 0)}
                                        sx={{ mt: 1, height: 8, borderRadius: 4 }}
                                    />
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography
                                        variant="h4"
                                        color={getResourceColor(systemMetrics.disk?.avg || 0)}
                                    >
                                        {systemMetrics.disk?.avg?.toFixed(1) || 0}%
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        دیسک متوسط
                                    </Typography>
                                    <LinearProgress
                                        variant="determinate"
                                        value={systemMetrics.disk?.avg || 0}
                                        color={getResourceColor(systemMetrics.disk?.avg || 0)}
                                        sx={{ mt: 1, height: 8, borderRadius: 4 }}
                                    />
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="primary">
                                        {systemMetrics.sample_count || 0}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        تعداد نمونه‌ها
                                    </Typography>
                                </Box>
                            </Grid>
                        </Grid>

                        <Divider sx={{ my: 2 }} />

                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Typography variant="body2">
                                    <strong>CPU:</strong>
                                    <Typography component="span" variant="body2" color="textSecondary" sx={{ ml: 1 }}>
                                        حداقل: {systemMetrics.cpu?.min?.toFixed(1) || 0}% |
                                        حداکثر: {systemMetrics.cpu?.max?.toFixed(1) || 0}%
                                    </Typography>
                                </Typography>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Typography variant="body2">
                                    <strong>حافظه:</strong>
                                    <Typography component="span" variant="body2" color="textSecondary" sx={{ ml: 1 }}>
                                        حداقل: {systemMetrics.memory?.min?.toFixed(1) || 0}% |
                                        حداکثر: {systemMetrics.memory?.max?.toFixed(1) || 0}%
                                    </Typography>
                                </Typography>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            )}

            {/* آمار دیتابیس */}
            {databaseMetrics && (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Storage />}
                        title="آمار دیتابیس"
                    />
                    <CardContent>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="primary">
                                        {databaseMetrics.total_queries || 0}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        کل Queries
                                    </Typography>
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="success.main">
                                        {databaseMetrics.successful_queries || 0}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        Queries موفق
                                    </Typography>
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="error.main">
                                        {databaseMetrics.failed_queries || 0}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        Queries ناموفق
                                    </Typography>
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="info.main">
                                        {databaseMetrics.success_rate?.toFixed(1) || 0}%
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        نرخ موفقیت
                                    </Typography>
                                </Box>
                            </Grid>
                        </Grid>

                        <Divider sx={{ my: 2 }} />

                        <Grid container spacing={2}>
                            <Grid item xs={12} md={6}>
                                <Typography variant="body2">
                                    <strong>زمان اجرای متوسط:</strong>
                                    <Typography component="span" sx={{ ml: 1 }}>
                                        {(databaseMetrics.avg_execution_time * 1000).toFixed(2)}ms
                                    </Typography>
                                </Typography>
                            </Grid>
                            <Grid item xs={12} md={6}>
                                <Typography variant="body2">
                                    <strong>زمان اجرای حداکثر:</strong>
                                    <Typography component="span" sx={{ ml: 1 }}>
                                        {(databaseMetrics.max_execution_time * 1000).toFixed(2)}ms
                                    </Typography>
                                </Typography>
                            </Grid>
                        </Grid>
                    </CardContent>
                </Card>
            )}

            {/* آمار API */}
            {apiMetrics && (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Language />}
                        title="آمار API"
                    />
                    <CardContent>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="primary">
                                        {apiMetrics.total_calls || 0}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        کل فراخوانی‌ها
                                    </Typography>
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="info.main">
                                        {(apiMetrics.avg_response_time * 1000).toFixed(2)}ms
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        زمان پاسخ متوسط
                                    </Typography>
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="warning.main">
                                        {(apiMetrics.max_response_time * 1000).toFixed(2)}ms
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        زمان پاسخ حداکثر
                                    </Typography>
                                </Box>
                            </Grid>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="success.main">
                                        {(apiMetrics.min_response_time * 1000).toFixed(2)}ms
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        زمان پاسخ حداقل
                                    </Typography>
                                </Box>
                            </Grid>
                        </Grid>

                        {/* آمار Endpoints */}
                        {apiMetrics.endpoints && Object.keys(apiMetrics.endpoints).length > 0 && (
                            <>
                                <Divider sx={{ my: 2 }} />
                                <Typography variant="h6" sx={{ mb: 2 }}>
                                    آمار Endpoints:
                                </Typography>
                                <Grid container spacing={2}>
                                    {Object.entries(apiMetrics.endpoints).map(([endpoint, stats]) => (
                                        <Grid item xs={12} md={6} key={endpoint}>
                                            <Paper elevation={1} sx={{ p: 2 }}>
                                                <Typography variant="subtitle1" fontWeight="bold">
                                                    {endpoint}
                                                </Typography>
                                                <Typography variant="body2" color="textSecondary">
                                                    تعداد: {stats.call_count} |
                                                    زمان متوسط: {(stats.avg_response_time * 1000).toFixed(2)}ms |
                                                    نرخ موفقیت: {stats.success_rate.toFixed(1)}%
                                                </Typography>
                                            </Paper>
                                        </Grid>
                                    ))}
                                </Grid>
                            </>
                        )}
                    </CardContent>
                </Card>
            )}

            {/* اطلاعات Cache */}
            {cacheInfo && (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Cached />}
                        title="اطلاعات Cache"
                    />
                    <CardContent>
                        <Grid container spacing={3}>
                            <Grid item xs={12} md={3}>
                                <Box textAlign="center">
                                    <Typography variant="h4" color="info.main">
                                        {cacheInfo.type}
                                    </Typography>
                                    <Typography variant="body2" color="textSecondary">
                                        نوع Cache
                                    </Typography>
                                </Box>
                            </Grid>
                            {cacheInfo.type === 'redis' ? (
                                <>
                                    <Grid item xs={12} md={3}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="primary">
                                                {cacheInfo.connected_clients || 0}
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                کلاینت‌های متصل
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} md={3}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="success.main">
                                                {cacheInfo.used_memory_human || '0B'}
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                حافظه استفاده شده
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} md={3}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="warning.main">
                                                {cacheInfo.keyspace_hits || 0}
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                Cache Hits
                                            </Typography>
                                        </Box>
                                    </Grid>
                                </>
                            ) : (
                                <>
                                    <Grid item xs={12} md={3}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="primary">
                                                {cacheInfo.total_keys || 0}
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                کل کلیدها
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} md={3}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="success.main">
                                                {cacheInfo.expired_keys_cleaned || 0}
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                کلیدهای منقضی شده
                                            </Typography>
                                        </Box>
                                    </Grid>
                                    <Grid item xs={12} md={3}>
                                        <Box textAlign="center">
                                            <Typography variant="h4" color="warning.main">
                                                Memory
                                            </Typography>
                                            <Typography variant="body2" color="textSecondary">
                                                نوع ذخیره
                                            </Typography>
                                        </Box>
                                    </Grid>
                                </>
                            )}
                        </Grid>
                    </CardContent>
                </Card>
            )}

            {/* هشدارهای عملکرد */}
            {alerts.length > 0 ? (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Warning />}
                        title={`هشدارهای عملکرد (${alerts.length})`}
                    />
                    <CardContent>
                        {alerts.map((alert, index) => (
                            <Alert
                                key={index}
                                severity={alert.severity === 'critical' ? 'error' : 'warning'}
                                sx={{ mb: 2 }}
                            >
                                <Box display="flex" justifyContent="space-between" alignItems="center" width="100%">
                                    <Box>
                                        <Typography variant="subtitle2" fontWeight="bold">
                                            {alert.type}
                                        </Typography>
                                        {alert.message}
                                    </Box>
                                    <Chip
                                        label={alert.severity === 'critical' ? 'بحرانی' : 'هشدار'}
                                        color={alert.severity === 'critical' ? 'error' : 'warning'}
                                        size="small"
                                    />
                                </Box>
                                <Typography variant="caption" color="textSecondary" display="block" sx={{ mt: 1 }}>
                                    {new Date(alert.timestamp).toLocaleString('fa-IR')}
                                </Typography>
                            </Alert>
                        ))}
                    </CardContent>
                </Card>
            ) : (
                <Card sx={{ mb: 3 }}>
                    <CardHeader
                        avatar={<Warning />}
                        title="هشدارهای عملکرد"
                    />
                    <CardContent>
                        <Alert severity="success">
                            هیچ هشدار عملکردی وجود ندارد. سیستم در وضعیت مطلوبی قرار دارد.
                        </Alert>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
};

export default PerformanceMonitoring;
