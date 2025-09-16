import React, { useState, useCallback, useEffect } from 'react';
import {
    Box,
    Typography,
    Paper,
    Tabs,
    Tab,
    Button,
    Alert,
    CircularProgress,
    Link,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    CloudUpload as CloudUploadIcon,
    Language as LanguageIcon,
    TextFields as TextIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
    Visibility as ViewIcon,
    Download as DownloadIcon,
    Upload as UploadIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { FileUploadTab, WebsiteUrlTab, TextTab, ExportDialog, ImportDialog } from './SourcesTabs';

const SourcesManager = ({ website }) => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);

    // States for pages list
    const [pages, setPages] = useState([]);
    const [pagesLoading, setPagesLoading] = useState(false);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [total, setTotal] = useState(0);

    // States for export/import
    const [exportDialogOpen, setExportDialogOpen] = useState(false);
    const [importDialogOpen, setImportDialogOpen] = useState(false);

    const handleTabChange = (event, newValue) => {
        setActiveTab(newValue);
        setError(null);
        setSuccess(null);
    };

    const handleSuccess = useCallback((message) => {
        setSuccess(message);
        setError(null);
        setLoading(false);
        // Refresh pages list after successful operation
        fetchPages();
    }, []);

    const handleError = useCallback((message) => {
        setError(message);
        setSuccess(null);
        setLoading(false);
    }, []);

    const handleLoading = useCallback((isLoading) => {
        setLoading(isLoading);
        if (isLoading) {
            setError(null);
            setSuccess(null);
        }
    }, []);

    // Fetch pages function
    const fetchPages = useCallback(async () => {
        if (!website?.id) return;

        try {
            setPagesLoading(true);
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
            const response = await fetch(`${API_URL}/api/${website.id}/pages?page=${page + 1}&limit=${rowsPerPage}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('خطا در دریافت صفحات');
            }

            const data = await response.json();
            setPages(data.pages || []);
            setTotal(data.total || 0);
        } catch (error) {
            console.error('Error fetching pages:', error);
            setError('خطا در دریافت صفحات');
        } finally {
            setPagesLoading(false);
        }
    }, [website?.id, page, rowsPerPage]);

    // Load pages on component mount and when website changes
    useEffect(() => {
        fetchPages();
    }, [fetchPages]);

    // Export handler
    const handleExport = async (format, exportType = 'full', maxTextLength = 1000) => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
            const response = await fetch(`${API_URL}/api/${website.id}/export?format=${format}&export_type=${exportType}&max_text_length=${maxTextLength}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('خطا در صادرات داده‌ها');
            }

            const data = await response.json();
            const suffix = exportType === 'excel_compatible' ? '_excel' : '_full';

            if (format === 'csv') {
                const blob = new Blob([data.data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${website.domain}_export${suffix}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const blob = new Blob([JSON.stringify(data.data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${website.domain}_export${suffix}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            }

            setExportDialogOpen(false);
            setSuccess('داده‌ها با موفقیت صادر شدند');
        } catch (error) {
            setError(`خطا در صادرات: ${error.message}`);
        }
    };

    // Import handler
    const handleImport = async (importData) => {
        try {
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
            const response = await fetch(`${API_URL}/api/${website.id}/import`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(importData)
            });

            if (!response.ok) {
                throw new Error('خطا در واردات داده‌ها');
            }

            const result = await response.json();
            setImportDialogOpen(false);
            setSuccess(`داده‌ها با موفقیت وارد شدند. ${result.imported_pages} صفحه اضافه شد.`);
            fetchPages(); // Refresh pages list
        } catch (error) {
            setError(`خطا در واردات: ${error.message}`);
        }
    };

    // Render pages list component
    const renderPagesList = () => (
        <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                    لیست صفحات موجود
                </Typography>
                <Box display="flex" gap={1}>
                    <Tooltip title="صادرات داده‌ها">
                        <IconButton onClick={() => setExportDialogOpen(true)} color="success">
                            <DownloadIcon />
                        </IconButton>
                    </Tooltip>
                    <Tooltip title="واردات داده‌ها">
                        <IconButton onClick={() => setImportDialogOpen(true)} color="info">
                            <UploadIcon />
                        </IconButton>
                    </Tooltip>
                </Box>
            </Box>

            {pagesLoading ? (
                <Box display="flex" justifyContent="center" alignItems="center" sx={{ py: 4 }}>
                    <CircularProgress />
                </Box>
            ) : (
                <TableContainer component={Paper}>
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
                            {pages.map((page, index) => (
                                <TableRow key={index}>
                                    <TableCell>{page.title}</TableCell>
                                    <TableCell>
                                        <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {page.url}
                                        </Typography>
                                    </TableCell>
                                    <TableCell>{page.links_count || 0}</TableCell>
                                    <TableCell>
                                        <Tooltip title="مشاهده">
                                            <IconButton size="small">
                                                <ViewIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="ویرایش">
                                            <IconButton size="small">
                                                <EditIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="حذف">
                                            <IconButton size="small" color="error">
                                                <DeleteIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            <TablePagination
                component="div"
                count={total}
                page={page}
                onPageChange={(event, newPage) => setPage(newPage)}
                rowsPerPage={rowsPerPage}
                onRowsPerPageChange={(event) => {
                    setRowsPerPage(parseInt(event.target.value, 10));
                    setPage(0);
                }}
                labelRowsPerPage="تعداد ردیف در صفحه:"
                labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
            />
        </Box>
    );

    if (!website) {
        return (
            <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="h6" color="text.secondary">
                    لطفاً یک وب‌سایت انتخاب کنید
                </Typography>
            </Box>
        );
    }

    const tabs = [
        {
            label: 'آپلود فایل',
            icon: <CloudUploadIcon />,
            component: <FileUploadTab
                website={website}
                onSuccess={handleSuccess}
                onError={handleError}
                onLoading={handleLoading}
            />
        },
        {
            label: 'آدرس وب‌سایت',
            icon: <LanguageIcon />,
            component: <WebsiteUrlTab
                website={website}
                onSuccess={handleSuccess}
                onError={handleError}
                onLoading={handleLoading}
            />
        },
        {
            label: 'متن',
            icon: <TextIcon />,
            component: <TextTab
                website={website}
                onSuccess={handleSuccess}
                onError={handleError}
                onLoading={handleLoading}
            />
        }
    ];

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 4 }}>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Box>
                        <Typography variant="h4" color="text.primary" gutterBottom>
                            منابع
                        </Typography>
                        <Typography variant="body1" color="text.secondary">
                            اسناد یا لینک‌ها را برای افزایش دانش ربات هوش مصنوعی خود اضافه کنید
                        </Typography>
                    </Box>
                    <Link
                        href="#"
                        color="text.secondary"
                        underline="hover"
                        sx={{ fontSize: '0.875rem' }}
                    >
                        نکات
                    </Link>
                </Box>
            </Box>

            {/* Tabs */}
            <Paper sx={{ mb: 3 }}>
                <Tabs
                    value={activeTab}
                    onChange={handleTabChange}
                    variant="fullWidth"
                    sx={{
                        borderBottom: 1,
                        borderColor: 'divider',
                        '& .MuiTab-root': {
                            minHeight: 48,
                            textTransform: 'none',
                            fontSize: '0.875rem',
                            fontWeight: 500,
                            color: 'text.secondary',
                            '&.Mui-selected': {
                                color: 'text.primary',
                                fontWeight: 600
                            }
                        },
                        '& .MuiTabs-indicator': {
                            backgroundColor: 'text.primary',
                            height: 2
                        }
                    }}
                >
                    {tabs.map((tab, index) => (
                        <Tab
                            key={index}
                            label={tab.label}
                            icon={tab.icon}
                            iconPosition="start"
                        />
                    ))}
                </Tabs>
            </Paper>

            {/* Messages */}
            {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                    {error}
                </Alert>
            )}

            {success && (
                <Alert severity="success" sx={{ mb: 3 }}>
                    {success}
                </Alert>
            )}

            {/* Loading */}
            {loading && (
                <Box display="flex" justifyContent="center" alignItems="center" sx={{ mb: 3 }}>
                    <CircularProgress size={24} sx={{ mr: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                        در حال پردازش...
                    </Typography>
                </Box>
            )}

            {/* Tab Content */}
            <Paper sx={{ p: 3, minHeight: 400, mb: 3 }}>
                {tabs[activeTab].component}
            </Paper>

            {/* Pages List */}
            <Paper sx={{ p: 3 }}>
                {renderPagesList()}
            </Paper>

            {/* Export Dialog */}
            <ExportDialog
                open={exportDialogOpen}
                onClose={() => setExportDialogOpen(false)}
                onExport={handleExport}
            />

            {/* Import Dialog */}
            <ImportDialog
                open={importDialogOpen}
                onClose={() => setImportDialogOpen(false)}
                onImport={handleImport}
            />
        </Box>
    );
};

export default SourcesManager;
