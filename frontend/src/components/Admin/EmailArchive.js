import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Button,
    IconButton,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Alert,
    LinearProgress,
    Avatar,
    Tooltip,
    Pagination,
    InputAdornment,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    Grid,
    Divider
} from '@mui/material';
import {
    Delete,
    Visibility,
    Email,
    CheckCircle,
    Error,
    Refresh,
    Search,
    Schedule,
    Person,
    Language,
    CalendarToday,
    Info
} from '@mui/icons-material';
import { emailArchive } from '../../services/api';

const EmailArchive = () => {
    const [emails, setEmails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedEmail, setSelectedEmail] = useState(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [emailTypeFilter, setEmailTypeFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');
    const [stats, setStats] = useState({});

    const fetchEmails = async () => {
        try {
            setLoading(true);
            setError('');

            const params = {
                page,
                limit: 20
            };

            if (searchTerm) params.recipient_email = searchTerm;
            if (emailTypeFilter !== 'all') params.email_type = emailTypeFilter;
            if (statusFilter !== 'all') params.is_sent = statusFilter === 'sent';

            const response = await emailArchive.getAdminEmailArchive(params);

            setEmails(response.emails || []);
            setTotalPages(response.total_pages || 1);
        } catch (err) {
            console.error('Error fetching emails:', err);
            setError('خطا در دریافت لیست ایمیل‌ها');
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await emailArchive.getAdminEmailStats();
            setStats(response);
        } catch (err) {
            console.error('Error fetching stats:', err);
        }
    };

    useEffect(() => {
        fetchEmails();
        fetchStats();
    }, [page, searchTerm, emailTypeFilter, statusFilter]);

    const handleViewEmail = async (emailId) => {
        try {
            const response = await emailArchive.getAdminEmailDetail(emailId);
            setSelectedEmail(response);
            setOpenDialog(true);
        } catch (err) {
            console.error('Error fetching email detail:', err);
            setError('خطا در دریافت جزئیات ایمیل');
        }
    };

    const handleDeleteEmail = async (emailId) => {
        if (window.confirm('آیا از حذف این ایمیل اطمینان دارید؟')) {
            try {
                await emailArchive.deleteAdminEmail(emailId);
                setSuccess('ایمیل با موفقیت حذف شد');
                fetchEmails();
                fetchStats();
            } catch (err) {
                console.error('Error deleting email:', err);
                setError('خطا در حذف ایمیل');
            }
        }
    };

    const handleRetryFailed = async () => {
        try {
            const response = await emailArchive.retryFailedEmails();
            setSuccess(response.message);
            fetchEmails();
            fetchStats();
        } catch (err) {
            console.error('Error retrying failed emails:', err);
            setError('خطا در ارسال مجدد ایمیل‌ها');
        }
    };

    const getStatusColor = (isSent) => {
        return isSent ? 'success' : 'error';
    };

    const getStatusIcon = (isSent) => {
        return isSent ? <CheckCircle /> : <Error />;
    };

    const getEmailTypeColor = (type) => {
        const colors = {
            'verification': 'primary',
            'reset_password': 'warning',
            '2fa': 'info',
            'notification': 'secondary',
            'custom': 'default'
        };
        return colors[type] || 'default';
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('fa-IR');
    };

    const formatTime = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleTimeString('fa-IR');
    };

    const emailTypes = [
        { value: 'all', label: 'همه انواع' },
        { value: 'verification', label: 'تأیید ایمیل' },
        { value: 'reset_password', label: 'بازیابی رمز عبور' },
        { value: '2fa', label: 'احراز هویت دو مرحله‌ای' },
        { value: 'notification', label: 'اعلان' },
        { value: 'custom', label: 'سفارشی' }
    ];

    const statusOptions = [
        { value: 'all', label: 'همه وضعیت‌ها' },
        { value: 'sent', label: 'ارسال شده' },
        { value: 'failed', label: 'ناموفق' }
    ];

    return (
        <Box sx={{ p: 3 }}>
            <Typography variant="h4" gutterBottom>
                آرشیو ایمیل‌ها
            </Typography>

            {/* آمار کلی */}
            <Grid container spacing={3} sx={{ mb: 3 }}>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                کل ایمیل‌ها
                            </Typography>
                            <Typography variant="h4">
                                {stats.total_emails || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                ارسال شده
                            </Typography>
                            <Typography variant="h4" color="success.main">
                                {stats.sent_emails || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                ناموفق
                            </Typography>
                            <Typography variant="h4" color="error.main">
                                {stats.failed_emails || 0}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                    <Card>
                        <CardContent>
                            <Typography color="textSecondary" gutterBottom>
                                نرخ موفقیت
                            </Typography>
                            <Typography variant="h4" color="primary.main">
                                {stats.success_rate ? `${stats.success_rate.toFixed(1)}%` : '0%'}
                            </Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* فیلترها و جستجو */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} sm={6} md={3}>
                            <TextField
                                fullWidth
                                label="جستجو بر اساس ایمیل"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <Search />
                                        </InputAdornment>
                                    ),
                                }}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <FormControl fullWidth>
                                <InputLabel>نوع ایمیل</InputLabel>
                                <Select
                                    value={emailTypeFilter}
                                    onChange={(e) => setEmailTypeFilter(e.target.value)}
                                    label="نوع ایمیل"
                                >
                                    {emailTypes.map((type) => (
                                        <MenuItem key={type.value} value={type.value}>
                                            {type.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <FormControl fullWidth>
                                <InputLabel>وضعیت</InputLabel>
                                <Select
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    label="وضعیت"
                                >
                                    {statusOptions.map((status) => (
                                        <MenuItem key={status.value} value={status.value}>
                                            {status.label}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Button
                                variant="outlined"
                                startIcon={<Refresh />}
                                onClick={fetchEmails}
                                disabled={loading}
                                fullWidth
                            >
                                به‌روزرسانی
                            </Button>
                        </Grid>
                    </Grid>

                    {stats.failed_emails > 0 && (
                        <Box sx={{ mt: 2 }}>
                            <Button
                                variant="contained"
                                color="warning"
                                startIcon={<Refresh />}
                                onClick={handleRetryFailed}
                            >
                                ارسال مجدد ایمیل‌های ناموفق ({stats.failed_emails})
                            </Button>
                        </Box>
                    )}
                </CardContent>
            </Card>

            {/* جدول ایمیل‌ها */}
            <Card>
                <CardContent>
                    {loading ? (
                        <LinearProgress />
                    ) : (
                        <>
                            <TableContainer>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>شناسه</TableCell>
                                            <TableCell>نوع</TableCell>
                                            <TableCell>گیرنده</TableCell>
                                            <TableCell>موضوع</TableCell>
                                            <TableCell>وضعیت</TableCell>
                                            <TableCell>تاریخ ایجاد</TableCell>
                                            <TableCell>عملیات</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {(emails || []).map((email) => (
                                            <TableRow key={email.id}>
                                                <TableCell>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        #{email.id}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={email.email_type}
                                                        color={getEmailTypeColor(email.email_type)}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Typography variant="body2">
                                                        {email.recipient_email}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell>
                                                    <Typography variant="body2" noWrap>
                                                        {email.subject}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        icon={getStatusIcon(email.is_sent)}
                                                        label={email.is_sent ? 'ارسال شده' : 'ناموفق'}
                                                        color={getStatusColor(email.is_sent)}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Box>
                                                        <Typography variant="body2">
                                                            {formatDate(email.created_at)}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {formatTime(email.created_at)}
                                                        </Typography>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Tooltip title="مشاهده جزئیات">
                                                        <IconButton
                                                            onClick={() => handleViewEmail(email.id)}
                                                            color="primary"
                                                        >
                                                            <Visibility />
                                                        </IconButton>
                                                    </Tooltip>
                                                    <Tooltip title="حذف">
                                                        <IconButton
                                                            onClick={() => handleDeleteEmail(email.id)}
                                                            color="error"
                                                        >
                                                            <Delete />
                                                        </IconButton>
                                                    </Tooltip>
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>

                            {/* صفحه‌بندی */}
                            {totalPages > 1 && (
                                <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                                    <Pagination
                                        count={totalPages}
                                        page={page}
                                        onChange={(e, value) => setPage(value)}
                                        color="primary"
                                    />
                                </Box>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>

            {/* دیالوگ جزئیات ایمیل */}
            <Dialog
                open={openDialog}
                onClose={() => setOpenDialog(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    جزئیات ایمیل #{selectedEmail?.id}
                </DialogTitle>
                <DialogContent>
                    {selectedEmail && (
                        <Box>
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        نوع ایمیل:
                                    </Typography>
                                    <Chip
                                        label={selectedEmail.email_type}
                                        color={getEmailTypeColor(selectedEmail.email_type)}
                                        sx={{ mb: 1 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        وضعیت:
                                    </Typography>
                                    <Chip
                                        icon={getStatusIcon(selectedEmail.is_sent)}
                                        label={selectedEmail.is_sent ? 'ارسال شده' : 'ناموفق'}
                                        color={getStatusColor(selectedEmail.is_sent)}
                                        sx={{ mb: 1 }}
                                    />
                                </Grid>
                                <Grid item xs={12}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        گیرنده:
                                    </Typography>
                                    <Typography variant="body1">
                                        {selectedEmail.recipient_email}
                                    </Typography>
                                </Grid>
                                <Grid item xs={12}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        فرستنده:
                                    </Typography>
                                    <Typography variant="body1">
                                        {selectedEmail.from_email}
                                    </Typography>
                                </Grid>
                                <Grid item xs={12}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        موضوع:
                                    </Typography>
                                    <Typography variant="body1">
                                        {selectedEmail.subject}
                                    </Typography>
                                </Grid>
                                <Grid item xs={12}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        محتوا:
                                    </Typography>
                                    <Box
                                        sx={{
                                            p: 2,
                                            bgcolor: 'grey.50',
                                            borderRadius: 1,
                                            maxHeight: 300,
                                            overflow: 'auto'
                                        }}
                                    >
                                        <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                                            {selectedEmail.body}
                                        </Typography>
                                    </Box>
                                </Grid>
                                {selectedEmail.error_message && (
                                    <Grid item xs={12}>
                                        <Typography variant="subtitle2" color="error">
                                            پیام خطا:
                                        </Typography>
                                        <Typography variant="body2" color="error">
                                            {selectedEmail.error_message}
                                        </Typography>
                                    </Grid>
                                )}
                                <Grid item xs={12} sm={6}>
                                    <Typography variant="subtitle2" color="textSecondary">
                                        تاریخ ایجاد:
                                    </Typography>
                                    <Typography variant="body2">
                                        {formatDate(selectedEmail.created_at)} - {formatTime(selectedEmail.created_at)}
                                    </Typography>
                                </Grid>
                                {selectedEmail.sent_at && (
                                    <Grid item xs={12} sm={6}>
                                        <Typography variant="subtitle2" color="textSecondary">
                                            تاریخ ارسال:
                                        </Typography>
                                        <Typography variant="body2">
                                            {formatDate(selectedEmail.sent_at)} - {formatTime(selectedEmail.sent_at)}
                                        </Typography>
                                    </Grid>
                                )}
                            </Grid>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenDialog(false)}>
                        بستن
                    </Button>
                </DialogActions>
            </Dialog>

            {/* پیام‌های موفقیت و خطا */}
            {success && (
                <Alert severity="success" sx={{ mt: 2 }} onClose={() => setSuccess('')}>
                    {success}
                </Alert>
            )}
            {error && (
                <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}
        </Box>
    );
};

export default EmailArchive;
