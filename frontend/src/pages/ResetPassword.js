import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Alert,
    Link,
    CircularProgress,
    InputAdornment,
    IconButton
} from '@mui/material';
import { ArrowBack, Visibility, VisibilityOff } from '@mui/icons-material';
import { auth } from '../services/api';
import { useSearchParams } from 'react-router-dom';

const ResetPassword = () => {
    const [searchParams] = useSearchParams();
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [token, setToken] = useState('');

    useEffect(() => {
        const tokenFromUrl = searchParams.get('token');
        if (tokenFromUrl) {
            setToken(tokenFromUrl);
        } else {
            setError('توکن بازیابی کلمه عبور نامعتبر است');
        }
    }, [searchParams]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!token) {
            setError('توکن بازیابی کلمه عبور نامعتبر است');
            return;
        }

        if (!newPassword) {
            setError('لطفاً کلمه عبور جدید را وارد کنید');
            return;
        }

        if (newPassword.length < 6) {
            setError('کلمه عبور باید حداقل 6 کاراکتر باشد');
            return;
        }

        if (newPassword !== confirmPassword) {
            setError('کلمه عبور و تکرار آن یکسان نیستند');
            return;
        }

        try {
            setLoading(true);
            setError('');
            setSuccess('');

            await auth.resetPassword(token, newPassword);
            setSuccess('کلمه عبور شما با موفقیت تغییر یافت. حالا می‌توانید وارد شوید.');
            
            // پاک کردن فرم
            setNewPassword('');
            setConfirmPassword('');
        } catch (err) {
            console.error('Error resetting password:', err);
            if (err.response?.data?.detail) {
                setError(err.response.data.detail);
            } else {
                setError('خطا در تغییر کلمه عبور');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleTogglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    const handleToggleConfirmPasswordVisibility = () => {
        setShowConfirmPassword(!showConfirmPassword);
    };

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                p: 2
            }}
        >
            <Card sx={{ maxWidth: 400, width: '100%', borderRadius: 3 }}>
                <CardContent sx={{ p: 4 }}>
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
                        <Typography variant="h4" component="h1" align="center" gutterBottom>
                            تغییر کلمه عبور
                        </Typography>
                        <Typography variant="body2" color="text.secondary" align="center">
                            کلمه عبور جدید خود را وارد کنید
                        </Typography>
                    </Box>

                    {/* Alerts */}
                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                            {error}
                        </Alert>
                    )}
                    {success && (
                        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
                            {success}
                        </Alert>
                    )}

                    {/* Form */}
                    <Box component="form" onSubmit={handleSubmit}>
                        <TextField
                            fullWidth
                            label="کلمه عبور جدید"
                            type={showPassword ? 'text' : 'password'}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            sx={{ mb: 2 }}
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton
                                            onClick={handleTogglePasswordVisibility}
                                            edge="end"
                                        >
                                            {showPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    </InputAdornment>
                                )
                            }}
                            disabled={loading}
                            helperText="حداقل 6 کاراکتر"
                        />

                        <TextField
                            fullWidth
                            label="تکرار کلمه عبور جدید"
                            type={showConfirmPassword ? 'text' : 'password'}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            sx={{ mb: 3 }}
                            error={newPassword !== confirmPassword && confirmPassword !== ''}
                            helperText={newPassword !== confirmPassword && confirmPassword !== '' ? 'کلمه عبور و تکرار آن یکسان نیستند' : ''}
                            InputProps={{
                                endAdornment: (
                                    <InputAdornment position="end">
                                        <IconButton
                                            onClick={handleToggleConfirmPasswordVisibility}
                                            edge="end"
                                        >
                                            {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    </InputAdornment>
                                )
                            }}
                            disabled={loading}
                        />

                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            size="large"
                            disabled={loading || !newPassword || newPassword.length < 6 || newPassword !== confirmPassword}
                            sx={{ mb: 2, py: 1.5 }}
                        >
                            {loading ? (
                                <CircularProgress size={24} color="inherit" />
                            ) : (
                                'تغییر کلمه عبور'
                            )}
                        </Button>

                        <Box sx={{ textAlign: 'center' }}>
                            <Link
                                href="/login"
                                sx={{
                                    display: 'inline-flex',
                                    alignItems: 'center',
                                    textDecoration: 'none',
                                    color: 'primary.main',
                                    '&:hover': {
                                        textDecoration: 'underline'
                                    }
                                }}
                            >
                                <ArrowBack sx={{ mr: 0.5, fontSize: 16 }} />
                                بازگشت به صفحه ورود
                            </Link>
                        </Box>
                    </Box>
                </CardContent>
            </Card>
        </Box>
    );
};

export default ResetPassword;
