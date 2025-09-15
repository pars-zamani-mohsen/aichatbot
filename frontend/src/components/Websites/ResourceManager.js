import React, { useState, useEffect } from 'react';
import {
    Box,
    Typography,
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    Button,
    IconButton,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Alert,
    CircularProgress,
    Tooltip
} from '@mui/material';
import {
    Refresh as RefreshIcon,
    Delete as DeleteIcon,
    Visibility as ViewIcon,
    Settings as SettingsIcon
} from '@mui/icons-material';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';

const ResourceManager = ({ website }) => {
    const { user } = useAuth();
    const [pages, setPages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [totalPages, setTotalPages] = useState(0);
    const [total, setTotal] = useState(0);
    const [reCrawlLoading, setReCrawlLoading] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [selectedPage, setSelectedPage] = useState(null);
    const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
    const [crawlSettings, setCrawlSettings] = useState({});
    const [viewDialogOpen, setViewDialogOpen] = useState(false);
    const [selectedPageForView, setSelectedPageForView] = useState(null);

    // بررسی نقش ادمین
    const isAdmin = user && user.role === 'admin';

    useEffect(() => {
        if (website) {
            fetchPages();
            // فقط ادمین‌ها می‌توانند تنظیمات کراولینگ را ببینند
            if (isAdmin) {
                fetchCrawlSettings();
            }
        }
    }, [website, page, rowsPerPage, isAdmin]);

    const fetchPages = async () => {
        try {
            setLoading(true);
            const response = await api.get(`/api/${website.id}/pages`, {
                params: {
                    page: page + 1,
                    limit: rowsPerPage
                }
            });

            setPages(response.data.pages);
            setTotal(response.data.total);
            setTotalPages(response.data.total_pages);
        } catch (err) {
            setError('خطا در دریافت صفحات');
            console.error('Fetch pages error:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchCrawlSettings = async () => {
        try {
            const response = await api.get(`/api/${website.id}/crawl-settings`);
            setCrawlSettings(response.data.crawl_settings || {});
        } catch (err) {
            console.error('Fetch crawl settings error:', err);
            if (err.response?.status === 403) {
                setError('شما دسترسی لازم برای مشاهده تنظیمات کراولینگ را ندارید');
            }
        }
    };

    const handleReCrawl = async () => {
        try {
            setReCrawlLoading(true);
            await api.post(`/api/${website.id}/re-crawl`);
            setError(null);
            // نمایش پیام موفقیت
        } catch (err) {
            setError('خطا در شروع کراولینگ مجدد');
            console.error('Re-crawl error:', err);
        } finally {
            setReCrawlLoading(false);
        }
    };

    const handleDeletePage = async () => {
        try {
            await api.delete(`/api/${website.id}/pages/${encodeURIComponent(selectedPage.url)}`);
            setDeleteDialogOpen(false);
            setSelectedPage(null);
            fetchPages(); // بارگذاری مجدد
        } catch (err) {
            setError('خطا در حذف صفحه');
            console.error('Delete page error:', err);
        }
    };

    const handleUpdateCrawlSettings = async () => {
        try {
            await api.put(`/api/${website.id}/crawl-settings`, crawlSettings);
            setSettingsDialogOpen(false);
            setError(null);
            // نمایش پیام موفقیت
        } catch (err) {
            console.error('Update settings error:', err);
            if (err.response?.status === 403) {
                setError('شما دسترسی لازم برای تغییر تنظیمات کراولینگ را ندارید');
            } else {
                setError('خطا در به‌روزرسانی تنظیمات');
            }
        }
    };

    const handleViewPage = (page) => {
        setSelectedPageForView(page);
        setViewDialogOpen(true);
    };

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    if (!website) {
        return <Typography>لطفاً یک وب‌سایت انتخاب کنید</Typography>;
    }

    return (
        <Box sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                <Typography variant="h5">
                    مدیریت منابع - {website.name || website.domain}
                </Typography>
                <Box>
                    {/* فقط ادمین‌ها می‌توانند تنظیمات کراولینگ را ببینند */}
                    {isAdmin && (
                        <Tooltip title="تنظیمات کراولینگ (فقط ادمین)">
                            <IconButton onClick={() => setSettingsDialogOpen(true)}>
                                <SettingsIcon />
                            </IconButton>
                        </Tooltip>
                    )}
                    {/* دکمه کراول مجدد مخفی شده است */}
                    {/* <Button
                        variant="contained"
                        startIcon={reCrawlLoading ? <CircularProgress size={20} /> : <RefreshIcon />}
                        onClick={handleReCrawl}
                        disabled={reCrawlLoading || website.status === 'crawling'}
                        sx={{ mr: 1 }}
                    >
                        کراول مجدد
                    </Button> */}
                </Box>
            </Box>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            <Paper>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>عنوان</TableCell>
                                <TableCell>URL</TableCell>
                                <TableCell>تعداد لینک‌ها</TableCell>
                                <TableCell>عملیات</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={4} align="center">
                                        <CircularProgress />
                                    </TableCell>
                                </TableRow>
                            ) : pages.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={4} align="center">
                                        صفحه‌ای یافت نشد
                                    </TableCell>
                                </TableRow>
                            ) : (
                                pages.map((page, index) => (
                                    <TableRow key={index}>
                                        <TableCell>
                                            <Typography variant="body2" noWrap>
                                                {page.title}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                                                {page.url}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip label={page.links_count} size="small" />
                                        </TableCell>
                                        <TableCell>
                                            <Tooltip title="مشاهده">
                                                <IconButton
                                                    size="small"
                                                    onClick={() => handleViewPage(page)}
                                                >
                                                    <ViewIcon />
                                                </IconButton>
                                            </Tooltip>
                                            <Tooltip title="حذف">
                                                <IconButton
                                                    size="small"
                                                    color="error"
                                                    onClick={() => {
                                                        setSelectedPage(page);
                                                        setDeleteDialogOpen(true);
                                                    }}
                                                >
                                                    <DeleteIcon />
                                                </IconButton>
                                            </Tooltip>
                                        </TableCell>
                                    </TableRow>
                                ))
                            )}
                        </TableBody>
                    </Table>
                </TableContainer>
                <TablePagination
                    component="div"
                    count={total}
                    page={page}
                    onPageChange={handleChangePage}
                    rowsPerPage={rowsPerPage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    labelRowsPerPage="ردیف در صفحه:"
                    labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
                />
            </Paper>

            {/* Dialog حذف صفحه */}
            <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
                <DialogTitle>حذف صفحه</DialogTitle>
                <DialogContent>
                    <Typography>
                        آیا از حذف صفحه "{selectedPage?.title}" اطمینان دارید؟
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>انصراف</Button>
                    <Button onClick={handleDeletePage} color="error">حذف</Button>
                </DialogActions>
            </Dialog>

            {/* Dialog تنظیمات کراولینگ */}
            <Dialog
                open={settingsDialogOpen}
                onClose={() => setSettingsDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle>تنظیمات کراولینگ</DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
                        <TextField
                            fullWidth
                            label="حداکثر تعداد صفحات"
                            type="number"
                            value={crawlSettings.max_pages || 100}
                            onChange={(e) => setCrawlSettings({
                                ...crawlSettings,
                                max_pages: parseInt(e.target.value)
                            })}
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            fullWidth
                            label="حداکثر عمق"
                            type="number"
                            value={crawlSettings.max_depth || 3}
                            onChange={(e) => setCrawlSettings({
                                ...crawlSettings,
                                max_depth: parseInt(e.target.value)
                            })}
                            sx={{ mb: 2 }}
                        />
                        <TextField
                            fullWidth
                            label="تأخیر بین درخواست‌ها (ثانیه)"
                            type="number"
                            value={crawlSettings.delay || 1}
                            onChange={(e) => setCrawlSettings({
                                ...crawlSettings,
                                delay: parseFloat(e.target.value)
                            })}
                            sx={{ mb: 2 }}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setSettingsDialogOpen(false)}>انصراف</Button>
                    <Button onClick={handleUpdateCrawlSettings} variant="contained">
                        ذخیره
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Dialog مشاهده صفحه */}
            <Dialog
                open={viewDialogOpen}
                onClose={() => setViewDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>
                    مشاهده صفحه - {selectedPageForView?.title}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                            URL:
                        </Typography>
                        <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                            {selectedPageForView?.url}
                        </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                            عنوان:
                        </Typography>
                        <Typography variant="body2">
                            {selectedPageForView?.title}
                        </Typography>
                    </Box>

                    <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                            تعداد لینک‌ها:
                        </Typography>
                        <Typography variant="body2">
                            {selectedPageForView?.links_count}
                        </Typography>
                    </Box>

                    <Box>
                        <Typography variant="subtitle2" color="primary" gutterBottom>
                            پیش‌نمایش متن:
                        </Typography>
                        <Typography
                            variant="body2"
                            sx={{
                                maxHeight: 300,
                                overflow: 'auto',
                                bgcolor: 'grey.50',
                                p: 2,
                                borderRadius: 1,
                                border: '1px solid',
                                borderColor: 'grey.300'
                            }}
                        >
                            {selectedPageForView?.text_preview || 'متن در دسترس نیست'}
                        </Typography>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setViewDialogOpen(false)}>بستن</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ResourceManager;
