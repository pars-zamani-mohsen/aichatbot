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
    Grid
} from '@mui/material';
import {
    Delete,
    Edit,
    Visibility,
    Language,
    Person,
    CalendarToday,
    Search,
    Refresh,
    Chat,
    Message,
    Storage
} from '@mui/icons-material';
import { dashboard } from '../../services/api';

const WebsiteManagement = () => {
    const [websites, setWebsites] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedWebsite, setSelectedWebsite] = useState(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [ownerFilter, setOwnerFilter] = useState('all');

    const fetchWebsites = async () => {
        try {
            setLoading(true);
            setError('');
            
            const response = await dashboard.getAdminWebsites(
                page, 
                20, 
                searchTerm || null, 
                statusFilter !== 'all' ? statusFilter : null,
                ownerFilter !== 'all' ? parseInt(ownerFilter) : null
            );
            
            setWebsites(response.websites);
            setTotalPages(response.total_pages);
        } catch (err) {
            console.error('Error fetching websites:', err);
            setError('خطا در دریافت لیست وب‌سایت‌ها');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWebsites();
    }, [page, searchTerm, statusFilter, ownerFilter]);

    const handleViewWebsite = (website) => {
        setSelectedWebsite(website);
        setOpenDialog(true);
    };

    const handleDeleteWebsite = async (websiteId) => {
        if (window.confirm('آیا از حذف این وب‌سایت اطمینان دارید؟ تمام گفتگوهای مربوطه نیز حذف خواهند شد.')) {
            try {
                await dashboard.deleteAdminWebsite(websiteId);
                setSuccess('وب‌سایت با موفقیت حذف شد');
                fetchWebsites();
            } catch (err) {
                console.error('Error deleting website:', err);
                setError('خطا در حذف وب‌سایت');
            }
        }
    };

    const handleSearch = (event) => {
        setSearchTerm(event.target.value);
        setPage(1);
    };

    const handleStatusFilterChange = (event) => {
        setStatusFilter(event.target.value);
        setPage(1);
    };

    const handleOwnerFilterChange = (event) => {
        setOwnerFilter(event.target.value);
        setPage(1);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('fa-IR');
    };

    const formatTime = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleTimeString('fa-IR');
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'ready': return 'success';
            case 'crawling': return 'warning';
            case 'error': return 'error';
            case 'pending': return 'info';
            default: return 'default';
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'ready': return 'آماده';
            case 'crawling': return 'در حال کراول';
            case 'error': return 'خطا';
            case 'pending': return 'در انتظار';
            default: return status;
        }
    };

    const getCrawlInfo = (crawlInfo) => {
        if (!crawlInfo) return { pages: 0, lastCrawl: null };
        return {
            pages: crawlInfo.total_pages || 0,
            lastCrawl: crawlInfo.crawled_at || null
        };
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                    مدیریت وب‌سایت‌ها
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    نظارت و مدیریت بر تمام وب‌سایت‌های سیستم
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

            {/* Filters and Actions */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                        <TextField
                            placeholder="جستجو در وب‌سایت‌ها..."
                            value={searchTerm}
                            onChange={handleSearch}
                            size="small"
                            sx={{ minWidth: 250 }}
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <Search />
                                    </InputAdornment>
                                ),
                            }}
                        />
                        
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                            <InputLabel>وضعیت</InputLabel>
                            <Select
                                value={statusFilter}
                                onChange={handleStatusFilterChange}
                                label="وضعیت"
                            >
                                <MenuItem value="all">همه وضعیت‌ها</MenuItem>
                                <MenuItem value="ready">آماده</MenuItem>
                                <MenuItem value="crawling">در حال کراول</MenuItem>
                                <MenuItem value="error">خطا</MenuItem>
                                <MenuItem value="pending">در انتظار</MenuItem>
                            </Select>
                        </FormControl>
                        
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                            <InputLabel>مالک</InputLabel>
                            <Select
                                value={ownerFilter}
                                onChange={handleOwnerFilterChange}
                                label="مالک"
                            >
                                <MenuItem value="all">همه مالکان</MenuItem>
                                {/* اینجا می‌توان لیست کاربران را اضافه کرد */}
                            </Select>
                        </FormControl>
                        
                        <Button
                            variant="outlined"
                            startIcon={<Refresh />}
                            onClick={fetchWebsites}
                            disabled={loading}
                        >
                            به‌روزرسانی
                        </Button>
                    </Box>
                </CardContent>
            </Card>

            {/* Websites Table */}
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
                                            <TableCell>وب‌سایت</TableCell>
                                            <TableCell>مالک</TableCell>
                                            <TableCell>وضعیت</TableCell>
                                            <TableCell>گفتگوها</TableCell>
                                            <TableCell>پیام‌ها</TableCell>
                                            <TableCell>صفحات کراول شده</TableCell>
                                            <TableCell>تاریخ ایجاد</TableCell>
                                            <TableCell>آخرین به‌روزرسانی</TableCell>
                                            <TableCell>عملیات</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {websites.map((website) => {
                                            const crawlInfo = getCrawlInfo(website.crawl_info);
                                            return (
                                                <TableRow key={website.id}>
                                                    <TableCell>
                                                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                            <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                                                                <Language />
                                                            </Avatar>
                                                            <Box>
                                                                <Typography variant="body2" fontWeight="bold">
                                                                    {website.name}
                                                                </Typography>
                                                                <Typography variant="caption" color="text.secondary">
                                                                    {website.domain}
                                                                </Typography>
                                                                <Typography variant="caption" display="block" color="text.secondary">
                                                                    {website.url}
                                                                </Typography>
                                                            </Box>
                                                        </Box>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                            <Avatar sx={{ mr: 2, bgcolor: 'secondary.main', width: 32, height: 32 }}>
                                                                <Person />
                                                            </Avatar>
                                                            <Box>
                                                                <Typography variant="body2" fontWeight="bold">
                                                                    {website.owner_email}
                                                                </Typography>
                                                                <Typography variant="caption" color="text.secondary">
                                                                    ID: {website.owner_id}
                                                                </Typography>
                                                            </Box>
                                                        </Box>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip
                                                            label={getStatusText(website.status)}
                                                            color={getStatusColor(website.status)}
                                                            size="small"
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip 
                                                            label={website.conversations_count} 
                                                            size="small" 
                                                            icon={<Chat />}
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        <Chip 
                                                            label={website.messages_count} 
                                                            size="small" 
                                                            icon={<Message />}
                                                        />
                                                    </TableCell>
                                                    <TableCell>
                                                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                            <Storage sx={{ fontSize: 16, mr: 0.5, color: 'text.secondary' }} />
                                                            <Typography variant="body2">
                                                                {crawlInfo.pages}
                                                            </Typography>
                                                        </Box>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Box>
                                                            <Typography variant="body2">
                                                                {formatDate(website.created_at)}
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary">
                                                                {formatTime(website.created_at)}
                                                            </Typography>
                                                        </Box>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Box>
                                                            <Typography variant="body2">
                                                                {formatDate(website.updated_at)}
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary">
                                                                {formatTime(website.updated_at)}
                                                            </Typography>
                                                        </Box>
                                                    </TableCell>
                                                    <TableCell>
                                                        <Box sx={{ display: 'flex', gap: 1 }}>
                                                            <Tooltip title="مشاهده جزئیات">
                                                                <IconButton
                                                                    size="small"
                                                                    onClick={() => handleViewWebsite(website)}
                                                                >
                                                                    <Visibility />
                                                                </IconButton>
                                                            </Tooltip>
                                                            <Tooltip title="حذف وب‌سایت">
                                                                <IconButton
                                                                    size="small"
                                                                    color="error"
                                                                    onClick={() => handleDeleteWebsite(website.id)}
                                                                >
                                                                    <Delete />
                                                                </IconButton>
                                                            </Tooltip>
                                                        </Box>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                            
                            {/* Pagination */}
                            {totalPages > 1 && (
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                                    <Pagination
                                        count={totalPages}
                                        page={page}
                                        onChange={(event, value) => setPage(value)}
                                        color="primary"
                                    />
                                </Box>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>

            {/* Website Details Dialog */}
            <Dialog 
                open={openDialog} 
                onClose={() => setOpenDialog(false)} 
                maxWidth="md" 
                fullWidth
            >
                <DialogTitle>
                    جزئیات وب‌سایت
                    {selectedWebsite && (
                        <Typography variant="body2" color="text.secondary">
                            {selectedWebsite.name} - {selectedWebsite.domain}
                        </Typography>
                    )}
                </DialogTitle>
                <DialogContent>
                    {selectedWebsite && (
                        <Box sx={{ mt: 2 }}>
                            <Grid container spacing={3}>
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" sx={{ mb: 2 }}>
                                        اطلاعات عمومی
                                    </Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">نام:</Typography>
                                        <Typography variant="body1">{selectedWebsite.name}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">دامنه:</Typography>
                                        <Typography variant="body1">{selectedWebsite.domain}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">URL:</Typography>
                                        <Typography variant="body1">{selectedWebsite.url}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">وضعیت:</Typography>
                                        <Chip
                                            label={getStatusText(selectedWebsite.status)}
                                            color={getStatusColor(selectedWebsite.status)}
                                            size="small"
                                        />
                                    </Box>
                                </Grid>
                                
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" sx={{ mb: 2 }}>
                                        اطلاعات مالک
                                    </Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">ایمیل:</Typography>
                                        <Typography variant="body1">{selectedWebsite.owner_email}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">شناسه کاربر:</Typography>
                                        <Typography variant="body1">{selectedWebsite.owner_id}</Typography>
                                    </Box>
                                </Grid>
                                
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" sx={{ mb: 2 }}>
                                        آمار
                                    </Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">تعداد گفتگوها:</Typography>
                                        <Typography variant="body1">{selectedWebsite.conversations_count}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">تعداد پیام‌ها:</Typography>
                                        <Typography variant="body1">{selectedWebsite.messages_count}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">صفحات کراول شده:</Typography>
                                        <Typography variant="body1">{getCrawlInfo(selectedWebsite.crawl_info).pages}</Typography>
                                    </Box>
                                </Grid>
                                
                                <Grid item xs={12} md={6}>
                                    <Typography variant="h6" sx={{ mb: 2 }}>
                                        تاریخ‌ها
                                    </Typography>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">تاریخ ایجاد:</Typography>
                                        <Typography variant="body1">{formatDate(selectedWebsite.created_at)}</Typography>
                                    </Box>
                                    <Box sx={{ mb: 2 }}>
                                        <Typography variant="body2" color="text.secondary">آخرین به‌روزرسانی:</Typography>
                                        <Typography variant="body1">{formatDate(selectedWebsite.updated_at)}</Typography>
                                    </Box>
                                    {getCrawlInfo(selectedWebsite.crawl_info).lastCrawl && (
                                        <Box sx={{ mb: 2 }}>
                                            <Typography variant="body2" color="text.secondary">آخرین کراول:</Typography>
                                            <Typography variant="body1">{formatDate(getCrawlInfo(selectedWebsite.crawl_info).lastCrawl)}</Typography>
                                        </Box>
                                    )}
                                </Grid>
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
        </Box>
    );
};

export default WebsiteManagement;
