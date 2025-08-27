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
  Paper
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

const UserReports = () => {
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d');

  // داده‌های نمونه برای نمودارها
  const weeklyData = [
    { day: 'شنبه', conversations: 8, messages: 25, websites: 2 },
    { day: 'یکشنبه', conversations: 12, messages: 35, websites: 2 },
    { day: 'دوشنبه', conversations: 6, messages: 18, websites: 1 },
    { day: 'سه‌شنبه', conversations: 15, messages: 42, websites: 3 },
    { day: 'چهارشنبه', conversations: 10, messages: 28, websites: 2 },
    { day: 'پنج‌شنبه', conversations: 18, messages: 55, websites: 3 },
    { day: 'جمعه', conversations: 14, messages: 38, websites: 2 },
  ];

  const websiteStats = [
    { name: 'example.com', conversations: 45, messages: 120, pages: 25 },
    { name: 'test.com', conversations: 32, messages: 85, pages: 18 },
    { name: 'demo.com', conversations: 28, messages: 72, pages: 15 },
  ];

  const pieData = [
    { name: 'فعال', value: 70, color: '#10b981' },
    { name: 'در انتظار', value: 20, color: '#f59e0b' },
    { name: 'تکمیل شده', value: 10, color: '#ef4444' },
  ];

  useEffect(() => {
    // شبیه‌سازی دریافت داده‌ها
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleExport = (type) => {
    // شبیه‌سازی export

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
                    83
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
                  +15% از هفته گذشته
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
                    253
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
                  +8% از هفته گذشته
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
                    3
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
                  +1 از هفته گذشته
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
                    92%
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
                  +3% از هفته گذشته
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
                {websiteStats.map((website) => (
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
                        <Speed sx={{ fontSize: 16, color: 'success.main' }} />
                        <Typography variant="body2" color="success.main">
                          عالی
                        </Typography>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default UserReports;
