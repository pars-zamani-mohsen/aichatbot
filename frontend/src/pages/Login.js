import React, { useState } from 'react';
import { useNavigate, Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  TextField,
  Button,
  Link,
  Box,
  Alert
} from '@mui/material';
import { auth } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await auth.login(formData.username, formData.password);

      // به‌روزرسانی context
      login(response.user);

      // هدایت بر اساس نقش کاربر
      if (response.user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error('Login error:', err);
      
      // بررسی انواع مختلف خطا
      if (err.response?.status === 401) {
        setError('ایمیل یا رمز عبور اشتباه است');
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.detail || 'اطلاعات ورودی نامعتبر است');
      } else if (err.response?.status === 422) {
        setError('لطفاً تمام فیلدها را پر کنید');
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setError('اتصال به سرور برقرار نشد. لطفاً دوباره تلاش کنید');
      } else if (err.message?.includes('Network Error')) {
        setError('خطا در اتصال به سرور. لطفاً اتصال اینترنت خود را بررسی کنید');
      } else {
        setError(err.response?.data?.detail || 'خطا در ورود به سیستم. لطفاً دوباره تلاش کنید');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          ورود به سیستم
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            margin="normal"
            required
            fullWidth
            id="username"
            label="نام کاربری"
            name="username"
            autoComplete="username"
            autoFocus
            value={formData.username}
            onChange={handleChange}
            dir="rtl"
          />
          <TextField
            margin="normal"
            required
            fullWidth
            name="password"
            label="رمز عبور"
            type="password"
            id="password"
            autoComplete="current-password"
            value={formData.password}
            onChange={handleChange}
            dir="rtl"
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? 'در حال ورود...' : 'ورود'}
          </Button>
          <Box sx={{ textAlign: 'center' }}>
            <Link component={RouterLink} to="/register" variant="body2">
              {'حساب کاربری ندارید؟ ثبت نام کنید'}
            </Link>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default Login; 