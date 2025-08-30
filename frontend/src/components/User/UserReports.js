import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Download,
  Assessment,
  TrendingUp,
  TrendingDown,
  Language,
  Chat,
  People,
  Speed
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { dashboard } from '../../services/api';

const UserReports = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('7d');
  const [reportsData, setReportsData] = useState(null);
  const [weeklyData, setWeeklyData] = useState([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  useEffect(() => {
    fetchReportsData();
  }, [timeRange]);

  const fetchReportsData = async () => {
    try {
      setLoading(true);
      setError(null);

      // دریافت گزارشات و آمار هفتگی
      const [reportsResponse, weeklyResponse] = await Promise.all([
        dashboard.getUserReports(timeRange),
        dashboard.getWeeklyStats()
      ]);

      setReportsData(reportsResponse);
      setWeeklyData(weeklyResponse);
    } catch (err) {
      setError('خطا در دریافت گزارشات');
      console.error('Error fetching reports:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = (type) => {
    try {
      setSnackbar({
        open: true,
        message: 'در حال آماده‌سازی گزارش...',
        severity: 'info'
      });

      // ایجاد داده‌های CSV
      let csvData = [];

      if (type === 'all') {
        csvData = [
          ['گزارش کلی', ''],
          ['کل گفتگوها', reportsData?.summary?.total_conversations || 0],
          ['کل پیام‌ها', reportsData?.summary?.total_messages || 0],
          ['وب‌سایت‌های فعال', reportsData?.summary?.active_websites || 0],
          ['رضایت کاربران', `${reportsData?.summary?.satisfaction_rate || 0}%`],
          [''],
          ['عملکرد وب‌سایت‌ها', ''],
          ['نام وب‌سایت', 'گفتگوها', 'پیام‌ها', 'صفحات', 'وضعیت']
        ];

        reportsData?.websites_stats?.forEach(website => {
          csvData.push([
            website.name,
            website.conversations,
            website.messages,
            website.pages,
            website.status
          ]);
        });
      } else if (type === 'websites') {
        csvData = [
          ['نام وب‌سایت', 'گفتگوها', 'پیام‌ها', 'صفحات', 'وضعیت']
        ];

        reportsData?.websites_stats?.forEach(website => {
          csvData.push([
            website.name,
            website.conversations,
            website.messages,
            website.pages,
            website.status
          ]);
        });
      }

      // تبدیل به CSV
      const csvContent = csvData.map(row => row.join(',')).join('\n');

      // ایجاد فایل و دانلود
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `reports_${type}_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSnackbar({
        open: true,
        message: 'گزارش با موفقیت دانلود شد',
        severity: 'success'
      });
    } catch (err) {
      console.error('Error exporting report:', err);
      setSnackbar({
        open: true,
        message: 'خطا در دانلود گزارش',
        severity: 'error'
      });
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
        <Button variant="outlined" onClick={fetchReportsData}>
          تلاش مجدد
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
            گزارشات من
          </Typography>
          <Typography variant="body1" color="text.secondary">
            تحلیل عملکرد وب‌سایت‌ها و گفتگوهای شما
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>بازه زمانی</InputLabel>
            <Select
              value={timeRange}
              label="بازه زمانی"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="7d">7 روز گذشته</MenuItem>
              <MenuItem value="30d">30 روز گذشته</MenuItem>
              <MenuItem value="90d">90 روز گذشته</MenuItem>
              <MenuItem value="1y">1 سال گذشته</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={() => handleExport('all')}
          >
            دانلود گزارش
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, #667eea15 0%, #667eea05 100%)',
            border: '1px solid #667eea20'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#667eea', mb: 1 }}>
                    {reportsData?.summary?.total_conversations || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    کل گفتگوها
                  </Typography>
                </Box>
                <Chat sx={{ fontSize: 48, color: '#667eea' }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                <Typography variant="caption" color="success.main">
                  {reportsData?.summary?.period_conversations || 0} در این بازه
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, #10b98115 0%, #10b98105 100%)',
            border: '1px solid #10b98120'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#10b981', mb: 1 }}>
                    {reportsData?.summary?.total_messages || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    پیام‌های ارسالی
                  </Typography>
                </Box>
                <Assessment sx={{ fontSize: 48, color: '#10b981' }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                <Typography variant="caption" color="success.main">
                  {reportsData?.summary?.period_messages || 0} در این بازه
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, #f59e0b15 0%, #f59e0b05 100%)',
            border: '1px solid #f59e0b20'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#f59e0b', mb: 1 }}>
                    {reportsData?.summary?.active_websites || 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    وب‌سایت‌های فعال
                  </Typography>
                </Box>
                <Language sx={{ fontSize: 48, color: '#f59e0b' }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                <Typography variant="caption" color="success.main">
                  آماده برای استفاده
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: 'linear-gradient(135deg, #ef444415 0%, #ef444405 100%)',
            border: '1px solid #ef444420'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 'bold', color: '#ef4444', mb: 1 }}>
                    {reportsData?.summary?.satisfaction_rate || 0}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    رضایت کاربران
                  </Typography>
                </Box>
                <Assessment sx={{ fontSize: 48, color: '#ef4444' }} />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
                <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                <Typography variant="caption" color="success.main">
                  بر اساس بازخوردها
                </Typography>
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
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Chip label="گفتگوها" size="small" color="primary" />
                  <Chip label="پیام‌ها" size="small" color="secondary" />
                  <Chip label="وب‌سایت‌ها" size="small" color="warning" />
                </Box>
              </Box>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={weeklyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="conversations" stroke="#667eea" strokeWidth={2} />
                  <Line type="monotone" dataKey="messages" stroke="#10b981" strokeWidth={2} />
                  <Line type="monotone" dataKey="websites" stroke="#f59e0b" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Conversation Status Pie Chart */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 'bold', mb: 3 }}>
                وضعیت گفتگوها
              </Typography>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={reportsData?.conversation_status || []}
                    cx="50%"
                    cy="50%"
                    innerRadius={40}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {(reportsData?.conversation_status || []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <Box sx={{ mt: 2 }}>
                {(reportsData?.conversation_status || []).map((item, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: item.color, mr: 1 }} />
                    <Typography variant="body2">{item.name}: {item.value}%</Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Website Performance Table */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
              عملکرد وب‌سایت‌ها
            </Typography>
            <Button
              variant="outlined"
              size="small"
              startIcon={<Download />}
              onClick={() => handleExport('websites')}
            >
              دانلود
            </Button>
          </Box>
          <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>وب‌سایت</TableCell>
                  <TableCell align="center">گفتگوها</TableCell>
                  <TableCell align="center">پیام‌ها</TableCell>
                  <TableCell align="center">صفحات</TableCell>
                  <TableCell align="center">عملکرد</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(reportsData?.websites_stats || []).length > 0 ? (
                  reportsData.websites_stats.map((website) => (
                    <TableRow key={website.name}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Language sx={{ fontSize: 16, color: 'text.secondary' }} />
                          {website.name}
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip label={website.conversations} size="small" color="primary" />
                      </TableCell>
                      <TableCell align="center">
                        <Chip label={website.messages} size="small" color="secondary" />
                      </TableCell>
                      <TableCell align="center">
                        <Chip label={website.pages} size="small" color="warning" />
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Speed sx={{ fontSize: 16, color: website.status === 'ready' ? 'success.main' : 'warning.main' }} />
                          <Typography variant="body2" color={website.status === 'ready' ? 'success.main' : 'warning.main'}>
                            {website.status === 'ready' ? 'آماده' : website.status}
                          </Typography>
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Language sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                          هیچ وب‌سایتی یافت نشد
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          هنوز هیچ وب‌سایتی اضافه نکرده‌اید
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default UserReports;
