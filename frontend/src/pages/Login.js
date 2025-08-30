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
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress
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
  const [show2FADialog, setShow2FADialog] = useState(false);
  const [twoFACode, setTwoFACode] = useState('');
  const [twoFALoading, setTwoFALoading] = useState(false);
  const [userEmail, setUserEmail] = useState('');

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
      if (err.response?.status === 202) {
        // نیاز به 2FA
        setUserEmail(formData.username);
        setShow2FADialog(true);
        setError('');
      } else if (err.response?.status === 429) {
        setError(err.response?.data?.detail || 'تعداد درخواست‌ها بیش از حد مجاز است. لطفاً صبر کنید');
      } else if (err.response?.status === 401) {
        setError(err.response?.data?.detail || 'ایمیل یا رمز عبور اشتباه است');
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

  const handle2FASubmit = async () => {
    if (!twoFACode.trim()) {
      setError('لطفاً کد احراز هویت را وارد کنید');
      return;
    }

    setTwoFALoading(true);
    setError('');

    try {
      const response = await auth.loginWith2FA(twoFACode, userEmail);

      // به‌روزرسانی context
      login(response.user);

      // بستن dialog
      setShow2FADialog(false);
      setTwoFACode('');

      // هدایت بر اساس نقش کاربر
      if (response.user.role === 'admin') {
        navigate('/admin/dashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      console.error('2FA error:', err);
      setError(err.response?.data?.detail || 'کد احراز هویت اشتباه است');
    } finally {
      setTwoFALoading(false);
    }
  };

  const handle2FAClose = () => {
    setShow2FADialog(false);
    setTwoFACode('');
    setError('');
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        {/* Logo */}
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <Box sx={{ 
            width: 100, 
            height: 100, 
            mx: 'auto',
            borderRadius: '50%',
            overflow: 'hidden',
            border: '3px solid #e3f2fd',
            boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
            mb: 2
          }}>
            <img 
              src="/logo.png" 
              alt="لوگو" 
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'cover' 
              }} 
            />
          </Box>
        </Box>

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
          
          <Box sx={{ textAlign: 'center', mb: 2 }}>
            <Link component={RouterLink} to="/forgot-password" variant="body2" sx={{ color: 'text.secondary' }}>
              {'فراموشی کلمه عبور؟'}
            </Link>
          </Box>
          
          <Box sx={{ textAlign: 'center' }}>
            <Link component={RouterLink} to="/register" variant="body2">
              {'حساب کاربری ندارید؟ ثبت نام کنید'}
            </Link>
          </Box>
        </Box>
      </Paper>

      {/* Dialog برای 2FA */}
      <Dialog open={show2FADialog} onClose={handle2FAClose} maxWidth="sm" fullWidth>
        <DialogTitle>
          احراز هویت دو مرحله‌ای
        </DialogTitle>
        <DialogContent>
          <Typography variant="body1" sx={{ mb: 2 }}>
            کد احراز هویت به ایمیل {userEmail} ارسال شد. لطفاً کد را وارد کنید:
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TextField
            fullWidth
            label="کد احراز هویت"
            value={twoFACode}
            onChange={(e) => setTwoFACode(e.target.value)}
            placeholder="000000"
            inputProps={{ maxLength: 6 }}
            dir="rtl"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handle2FAClose} disabled={twoFALoading}>
            انصراف
          </Button>
          <Button
            onClick={handle2FASubmit}
            variant="contained"
            disabled={twoFALoading || !twoFACode.trim()}
          >
            {twoFALoading ? <CircularProgress size={20} /> : 'تأیید'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Login; 