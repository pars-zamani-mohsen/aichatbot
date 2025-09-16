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
    Tooltip,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Grid,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions
} from '@mui/material';
import {
    CloudUpload as CloudUploadIcon,
    Language as LanguageIcon,
    TextFields as TextIcon,
    Delete as DeleteIcon,
    Edit as EditIcon,
    Visibility as ViewIcon,
    Download as DownloadIcon,
    Upload as UploadIcon,
    Search as SearchIcon
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
    
    // States for page operations
    const [viewDialogOpen, setViewDialogOpen] = useState(false);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [selectedPage, setSelectedPage] = useState(null);

    // States for search and filter
    const [searchQuery, setSearchQuery] = useState('');
    const [filterBy, setFilterBy] = useState('all');
    const [sortBy, setSortBy] = useState('title');
    const [sortOrder, setSortOrder] = useState('asc');

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

            let url = `${API_URL}/api/${website.id}/pages?page=${page + 1}&limit=${rowsPerPage}`;

            // Add search and filter parameters
            if (searchQuery) {
                url += `&query=${encodeURIComponent(searchQuery)}`;
            }
            if (filterBy !== 'all') {
                url += `&filter_by=${filterBy}`;
            }
            if (sortBy) {
                url += `&sort_by=${sortBy}`;
            }
            if (sortOrder) {
                url += `&sort_order=${sortOrder}`;
            }

            const response = await fetch(url, {
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
    }, [website?.id, page, rowsPerPage, searchQuery, filterBy, sortBy, sortOrder]);

    // Load pages on component mount and when website changes
    useEffect(() => {
        fetchPages();
    }, [fetchPages]);

    // Search and filter handlers
    const handleSearch = () => {
        setPage(0); // Reset to first page when searching
        fetchPages();
    };

    const handleFilterChange = (newFilter) => {
        setFilterBy(newFilter);
        setPage(0); // Reset to first page when filtering
    };

    const handleSortChange = (newSort) => {
        setSortBy(newSort);
        setPage(0); // Reset to first page when sorting
    };

    const handleSortOrderChange = (newOrder) => {
        setSortOrder(newOrder);
        setPage(0); // Reset to first page when changing sort order
    };

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

    // Page operation handlers
    const handleViewPage = (page) => {
        setSelectedPage(page);
        setViewDialogOpen(true);
    };

    const handleEditPage = (page) => {
        setSelectedPage(page);
        setEditDialogOpen(true);
    };

    const handleDeletePage = (page) => {
        setSelectedPage(page);
        setDeleteDialogOpen(true);
    };

    const confirmDeletePage = async () => {
        if (!selectedPage) return;

        try {
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
            const response = await fetch(`${API_URL}/api/${website.id}/pages/${encodeURIComponent(selectedPage.url)}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (!response.ok) {
                throw new Error('خطا در حذف صفحه');
            }

            setDeleteDialogOpen(false);
            setSelectedPage(null);
            setSuccess(`صفحه "${selectedPage.title}" با موفقیت حذف شد`);
            fetchPages(); // Refresh pages list
        } catch (error) {
            setError(`خطا در حذف صفحه: ${error.message}`);
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

            {/* Search and Filter Section */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={4}>
                        <TextField
                            fullWidth
                            label="جستجو"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            InputProps={{
                                endAdornment: (
                                    <IconButton onClick={handleSearch}>
                                        <SearchIcon />
                                    </IconButton>
                                )
                            }}
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        />
                    </Grid>
                    <Grid item xs={12} md={2}>
                        <FormControl fullWidth>
                            <InputLabel>فیلتر بر اساس</InputLabel>
                            <Select
                                value={filterBy}
                                onChange={(e) => handleFilterChange(e.target.value)}
                            >
                                <MenuItem value="all">همه</MenuItem>
                                <MenuItem value="title">عنوان</MenuItem>
                                <MenuItem value="text">محتوا</MenuItem>
                                <MenuItem value="url">URL</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={2}>
                        <FormControl fullWidth>
                            <InputLabel>مرتب‌سازی بر اساس</InputLabel>
                            <Select
                                value={sortBy}
                                onChange={(e) => handleSortChange(e.target.value)}
                            >
                                <MenuItem value="title">عنوان</MenuItem>
                                <MenuItem value="url">URL</MenuItem>
                                <MenuItem value="links_count">تعداد لینک‌ها</MenuItem>
                                <MenuItem value="created_at">تاریخ ایجاد</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={2}>
                        <FormControl fullWidth>
                            <InputLabel>ترتیب</InputLabel>
                            <Select
                                value={sortOrder}
                                onChange={(e) => handleSortOrderChange(e.target.value)}
                            >
                                <MenuItem value="asc">صعودی</MenuItem>
                                <MenuItem value="desc">نزولی</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                </Grid>
            </Paper>

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
                                            <IconButton 
                                                size="small"
                                                onClick={() => handleViewPage(page)}
                                            >
                                                <ViewIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="ویرایش">
                                            <IconButton 
                                                size="small"
                                                onClick={() => handleEditPage(page)}
                                            >
                                                <EditIcon />
                                            </IconButton>
                                        </Tooltip>
                                        <Tooltip title="حذف">
                                            <IconButton 
                                                size="small" 
                                                color="error"
                                                onClick={() => handleDeletePage(page)}
                                            >
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

            {/* View Page Dialog */}
            <Dialog 
                open={viewDialogOpen} 
                onClose={() => setViewDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>مشاهده صفحه</DialogTitle>
                <DialogContent>
                    {selectedPage && (
                        <Box>
                            <Typography variant="h6" gutterBottom>
                                {selectedPage.title}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                URL: {selectedPage.url}
                            </Typography>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                تعداد لینک‌ها: {selectedPage.links_count || 0}
                            </Typography>
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="subtitle2" gutterBottom>
                                    محتوا:
                                </Typography>
                                <Box 
                                    sx={{ 
                                        maxHeight: 400, 
                                        overflow: 'auto', 
                                        p: 2, 
                                        bgcolor: 'grey.50',
                                        borderRadius: 1,
                                        border: '1px solid',
                                        borderColor: 'grey.200'
                                    }}
                                >
                                    <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                        {selectedPage.text || 'محتوایی موجود نیست'}
                                    </Typography>
                                </Box>
                            </Box>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setViewDialogOpen(false)}>
                        بستن
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Edit Page Dialog */}
            <Dialog 
                open={editDialogOpen} 
                onClose={() => setEditDialogOpen(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogTitle>ویرایش صفحه</DialogTitle>
                <DialogContent>
                    {selectedPage && (
                        <Box sx={{ mt: 2 }}>
                            <TextField
                                fullWidth
                                label="عنوان"
                                value={selectedPage.title || ''}
                                onChange={(e) => setSelectedPage(prev => ({ ...prev, title: e.target.value }))}
                                sx={{ mb: 2 }}
                            />
                            <TextField
                                fullWidth
                                label="محتوا"
                                multiline
                                rows={8}
                                value={selectedPage.text || ''}
                                onChange={(e) => setSelectedPage(prev => ({ ...prev, text: e.target.value }))}
                            />
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setEditDialogOpen(false)}>
                        انصراف
                    </Button>
                    <Button 
                        variant="contained"
                        onClick={async () => {
                            try {
                                const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
                                const response = await fetch(`${API_URL}/api/${website.id}/pages/${encodeURIComponent(selectedPage.url)}`, {
                                    method: 'PUT',
                                    headers: {
                                        'Content-Type': 'application/json',
                                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                                    },
                                    body: JSON.stringify({
                                        title: selectedPage.title,
                                        text: selectedPage.text
                                    })
                                });

                                if (!response.ok) {
                                    throw new Error('خطا در ویرایش صفحه');
                                }

                                setEditDialogOpen(false);
                                setSelectedPage(null);
                                setSuccess('صفحه با موفقیت ویرایش شد');
                                fetchPages();
                            } catch (error) {
                                setError(`خطا در ویرایش صفحه: ${error.message}`);
                            }
                        }}
                    >
                        ذخیره
                    </Button>
                </DialogActions>
            </Dialog>

            {/* Delete Page Confirmation Dialog */}
            <Dialog 
                open={deleteDialogOpen} 
                onClose={() => setDeleteDialogOpen(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogTitle sx={{ color: 'error.main' }}>
                    حذف صفحه
                </DialogTitle>
                <DialogContent>
                    {selectedPage && (
                        <Box>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                                آیا از حذف صفحه <strong>"{selectedPage.title}"</strong> اطمینان دارید؟
                            </Typography>
                            <Alert severity="warning">
                                این عمل غیرقابل بازگشت است و صفحه از پایگاه دانش حذف خواهد شد.
                            </Alert>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteDialogOpen(false)}>
                        انصراف
                    </Button>
                    <Button 
                        variant="contained"
                        color="error"
                        onClick={confirmDeletePage}
                    >
                        حذف
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default SourcesManager;
