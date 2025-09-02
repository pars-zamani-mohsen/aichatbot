import React, { useState } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    Alert,
    Link,
    CircularProgress
} from '@mui/material';
import { ArrowBack, Email } from '@mui/icons-material';
import { auth } from '../services/api';

const ForgotPassword = () => {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!email) {
            setError('لطفاً ایمیل خود را وارد کنید');
            return;
        }

        if (!email.includes('@')) {
            setError('لطفاً یک ایمیل معتبر وارد کنید');
            return;
        }

        try {
            setLoading(true);
            setError('');
            setSuccess('');

            await auth.forgotPassword(email);
            setSuccess('ایمیل بازیابی کلمه عبور ارسال شد. لطفاً صندوق ورودی خود را بررسی کنید.');
            setEmail('');
        } catch (err) {
            console.error('Error requesting password reset:', err);
            if (err.response?.data?.detail) {
                setError(err.response.data.detail);
            } else {
                setError('خطا در ارسال درخواست بازیابی کلمه عبور');
            }
        } finally {
            setLoading(false);
        }
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
                            بازیابی کلمه عبور
                        </Typography>
                        <Typography variant="body2" color="text.secondary" align="center">
                            ایمیل خود را وارد کنید تا لینک بازیابی کلمه عبور برای شما ارسال شود
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
                            label="ایمیل"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            sx={{ mb: 3 }}
                            InputProps={{
                                startAdornment: <Email sx={{ mr: 1, color: 'text.secondary' }} />
                            }}
                            disabled={loading}
                        />

                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            size="large"
                            disabled={loading || !email}
                            sx={{ mb: 2, py: 1.5 }}
                        >
                            {loading ? (
                                <CircularProgress size={24} color="inherit" />
                            ) : (
                                'ارسال لینک بازیابی'
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

export default ForgotPassword;
