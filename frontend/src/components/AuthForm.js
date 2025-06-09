import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  TextField,
  Typography,
  Container,
  Paper,
  Alert,
  CircularProgress
} from '@mui/material';
import { auth } from '../services/api';

const AuthForm = ({ type }) => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: ''
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
      if (type === 'register' && formData.password !== formData.confirmPassword) {
        throw new Error('رمز عبور و تکرار آن مطابقت ندارند');
      }

      const response = type === 'login'
        ? await auth.login(formData.email, formData.password)
        : await auth.register(formData.email, formData.password);

      if (response.data.access_token) {
        localStorage.setItem('token', response.data.access_token);
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container component="main" maxWidth="xs">
      <Paper elevation={3} sx={{ p: 4, mt: 8 }}>
        <Typography component="h1" variant="h5" align="center" gutterBottom>
          {type === 'login' ? 'ورود به سیستم' : 'ثبت نام'}
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
            id="email"
            label="ایمیل"
            name="email"
            autoComplete="email"
            autoFocus
            value={formData.email}
            onChange={handleChange}
            dir="ltr"
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
            dir="ltr"
          />
          {type === 'register' && (
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="تکرار رمز عبور"
              type="password"
              id="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              dir="ltr"
            />
          )}
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? (
              <CircularProgress size={24} color="inherit" />
            ) : type === 'login' ? (
              'ورود'
            ) : (
              'ثبت نام'
            )}
          </Button>
          <Button
            fullWidth
            variant="text"
            onClick={() => navigate(type === 'login' ? '/register' : '/login')}
          >
            {type === 'login'
              ? 'حساب کاربری ندارید؟ ثبت نام کنید'
              : 'قبلاً ثبت نام کرده‌اید؟ وارد شوید'}
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default AuthForm; 