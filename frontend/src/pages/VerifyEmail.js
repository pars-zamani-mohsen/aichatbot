import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Card,
    CardContent,
    Typography,
    CircularProgress,
    Alert,
    Button,
    Container
} from '@mui/material';
import { CheckCircle, Error, Email } from '@mui/icons-material';
import { auth } from '../services/api';

const VerifyEmail = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');

    useEffect(() => {
        const verifyEmail = async () => {
            try {
                const token = searchParams.get('token');
                
                if (!token) {
                    setError('توکن تأیید یافت نشد');
                    setLoading(false);
                    return;
                }

                const response = await auth.verifyEmail(token);
                setSuccess(true);
                setMessage(response.message || 'ایمیل با موفقیت تأیید شد');
                
                // ریدایرکت به صفحه لاگین بعد از 3 ثانیه
                setTimeout(() => {
                    navigate('/login', { 
                        state: { 
                            message: 'ایمیل شما با موفقیت تأیید شد. حالا می‌توانید وارد شوید.' 
                        } 
                    });
                }, 3000);

            } catch (err) {
                console.error('Error verifying email:', err);
                setError(err.response?.data?.detail || 'خطا در تأیید ایمیل');
            } finally {
                setLoading(false);
            }
        };

        verifyEmail();
    }, [searchParams, navigate]);

    const handleGoToLogin = () => {
        navigate('/login', { 
            state: { 
                message: success ? 'ایمیل شما با موفقیت تأیید شد. حالا می‌توانید وارد شوید.' : '' 
            } 
        });
    };

    if (loading) {
        return (
            <Container maxWidth="sm">
                <Box
                    sx={{
                        minHeight: '100vh',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                    }}
                >
                    <Card sx={{ width: '100%', textAlign: 'center' }}>
                        <CardContent sx={{ py: 4 }}>
                            <CircularProgress size={60} sx={{ mb: 2 }} />
                            <Typography variant="h6" gutterBottom>
                                در حال تأیید ایمیل...
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                لطفاً صبر کنید
                            </Typography>
                        </CardContent>
                    </Card>
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="sm">
            <Box
                sx={{
                    minHeight: '100vh',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                }}
            >
                <Card sx={{ width: '100%', textAlign: 'center' }}>
                    <CardContent sx={{ py: 4 }}>
                        {success ? (
                            <>
                                <CheckCircle 
                                    sx={{ 
                                        fontSize: 80, 
                                        color: 'success.main', 
                                        mb: 2 
                                    }} 
                                />
                                <Typography variant="h5" gutterBottom color="success.main">
                                    تأیید موفق
                                </Typography>
                                <Typography variant="body1" sx={{ mb: 3 }}>
                                    {message}
                                </Typography>
                                <Alert severity="success" sx={{ mb: 3 }}>
                                    حساب کاربری شما فعال شد. در حال انتقال به صفحه ورود...
                                </Alert>
                            </>
                        ) : (
                            <>
                                <Error 
                                    sx={{ 
                                        fontSize: 80, 
                                        color: 'error.main', 
                                        mb: 2 
                                    }} 
                                />
                                <Typography variant="h5" gutterBottom color="error.main">
                                    خطا در تأیید
                                </Typography>
                                <Typography variant="body1" sx={{ mb: 3 }}>
                                    {error}
                                </Typography>
                                <Alert severity="error" sx={{ mb: 3 }}>
                                    لینک تأیید نامعتبر یا منقضی شده است.
                                </Alert>
                            </>
                        )}

                        <Box sx={{ mt: 3 }}>
                            <Button
                                variant="contained"
                                onClick={handleGoToLogin}
                                startIcon={<Email />}
                                size="large"
                            >
                                رفتن به صفحه ورود
                            </Button>
                        </Box>

                        {!success && (
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" color="text.secondary">
                                    اگر ایمیل تأیید دریافت نکرده‌اید،{' '}
                                    <Button
                                        variant="text"
                                        size="small"
                                        onClick={() => navigate('/resend-verification')}
                                    >
                                        درخواست ارسال مجدد
                                    </Button>
                                </Typography>
                            </Box>
                        )}
                    </CardContent>
                </Card>
            </Box>
        </Container>
    );
};

export default VerifyEmail;
