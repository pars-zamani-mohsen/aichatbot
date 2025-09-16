import React, { useState, useEffect, useCallback } from 'react';
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
    Tooltip,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Grid,
    Card,
    CardContent,
    Checkbox,
    Menu,
    ListItemIcon,
    ListItemText
} from '@mui/material';
import {
    Delete as DeleteIcon,
    Visibility as ViewIcon,
    Settings as SettingsIcon,
    Edit as EditIcon,
    Add as AddIcon,
    Search as SearchIcon,
    Download as DownloadIcon,
    Upload as UploadIcon,
    FilterList as FilterIcon,
    ArrowDropDown as ArrowDropDownIcon,
    Article as ArticleIcon,
    QuestionAnswer as QuestionAnswerIcon,
    Description as DescriptionIcon
} from '@mui/icons-material';
import api from '../../services/api';
import { useAuth } from '../../contexts/AuthContext';
import { EditPageDialog, AddPageDialog, ExportDialog, ImportDialog, FileUploadDialog, FaqDialog } from './ResourceManagerDialogs';

const ResourceManager = ({ website }) => {
    const { user } = useAuth();
    const [pages, setPages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [total, setTotal] = useState(0);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [selectedPage, setSelectedPage] = useState(null);
    const [settingsDialogOpen, setSettingsDialogOpen] = useState(false);
    const [crawlSettings, setCrawlSettings] = useState({});
    const [viewDialogOpen, setViewDialogOpen] = useState(false);
    const [selectedPageForView, setSelectedPageForView] = useState(null);

    // حالت‌های جدید
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [addDialogOpen, setAddDialogOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterBy, setFilterBy] = useState('all');
    const [sortBy, setSortBy] = useState('title');
    const [sortOrder, setSortOrder] = useState('asc');
    const [selectedPages, setSelectedPages] = useState([]);
    const [importDialogOpen, setImportDialogOpen] = useState(false);
    const [exportDialogOpen, setExportDialogOpen] = useState(false);
    const [fileUploadDialogOpen, setFileUploadDialogOpen] = useState(false);
    
    // Menu states
    const [addMenuAnchor, setAddMenuAnchor] = useState(null);
    const [faqDialogOpen, setFaqDialogOpen] = useState(false);

    // بررسی نقش ادمین
    const isAdmin = user && user.role === 'admin';

    const fetchPages = useCallback(async () => {
        try {
            setLoading(true);
            let response;

            if (searchQuery) {
                // استفاده از API جستجو
                response = await api.get(`/api/${website.id}/pages/search`, {
                    params: {
                        query: searchQuery,
                        filter_by: filterBy,
                        sort_by: sortBy,
                        sort_order: sortOrder,
                        page: page + 1,
                        limit: rowsPerPage
                    }
                });
            } else {
                // استفاده از API عادی
                response = await api.get(`/api/${website.id}/pages`, {
                    params: {
                        page: page + 1,
                        limit: rowsPerPage
                    }
                });
            }

            setPages(response.data.pages);
            setTotal(response.data.total);
        } catch (err) {
            setError('خطا در دریافت صفحات');
            console.error('Fetch pages error:', err);
        } finally {
            setLoading(false);
        }
    }, [website, searchQuery, filterBy, sortBy, sortOrder, page, rowsPerPage]);

    const fetchCrawlSettings = useCallback(async () => {
        try {
            const response = await api.get(`/api/${website.id}/crawl-settings`);
            setCrawlSettings(response.data.crawl_settings || {});
        } catch (err) {
            console.error('Fetch crawl settings error:', err);
            if (err.response?.status === 403) {
                setError('شما دسترسی لازم برای مشاهده تنظیمات کراولینگ را ندارید');
            }
        }
    }, [website]);

    useEffect(() => {
        if (website) {
            fetchPages();
            // فقط ادمین‌ها می‌توانند تنظیمات کراولینگ را ببینند
            if (isAdmin) {
                fetchCrawlSettings();
            }
        }
    }, [website, isAdmin, fetchPages, fetchCrawlSettings]);


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

    const handleEditPage = (page) => {
        setSelectedPageForView(page);
        setEditDialogOpen(true);
    };

    const handleSearch = () => {
        setPage(0);
        fetchPages();
    };

    const handleClearSearch = () => {
        setSearchQuery('');
        setFilterBy('all');
        setSortBy('title');
        setSortOrder('asc');
        setPage(0);
        fetchPages();
    };

    const handleExport = async (format, exportType = 'full', maxTextLength = 1000) => {
        try {
            const response = await api.get(`/api/${website.id}/export`, {
                params: {
                    format,
                    export_type: exportType,
                    max_text_length: maxTextLength
                }
            });

            const suffix = exportType === 'excel_compatible' ? '_excel' : '_full';

            if (format === 'csv') {
                const blob = new Blob([response.data.data], { type: 'text/csv' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${website.domain}_export${suffix}.csv`;
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                const blob = new Blob([JSON.stringify(response.data.data, null, 2)], { type: 'application/json' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${website.domain}_export${suffix}.json`;
                a.click();
                window.URL.revokeObjectURL(url);
            }

            setExportDialogOpen(false);
        } catch (err) {
            setError('خطا در صادرات داده‌ها');
            console.error('Export error:', err);
        }
    };

    const handleImport = async (file, format) => {
        try {
            const fileContent = await file.text();
            const importData = {
                format: format,
                data: format === 'json' ? JSON.parse(fileContent) : fileContent
            };

            await api.post(`/api/${website.id}/import`, importData);
            setImportDialogOpen(false);
            fetchPages();
            setError(null);
        } catch (err) {
            setError('خطا در واردات داده‌ها');
            console.error('Import error:', err);
        }
    };

    const handleFileUpload = async (result) => {
        try {
            setFileUploadDialogOpen(false);
            fetchPages();
            setError(null);
            // نمایش پیام موفقیت
            console.log('File uploaded successfully:', result);
        } catch (err) {
            setError('خطا در آپلود فایل');
            console.error('File upload error:', err);
        }
    };

    // Menu handlers
    const handleAddMenuClick = (event) => {
        setAddMenuAnchor(event.currentTarget);
    };

    const handleAddMenuClose = () => {
        setAddMenuAnchor(null);
    };

    const handleAddPage = () => {
        setAddMenuAnchor(null);
        setAddDialogOpen(true);
    };

    const handleAddFAQ = () => {
        setAddMenuAnchor(null);
        setFaqDialogOpen(true);
    };

    const handleAddFile = () => {
        setAddMenuAnchor(null);
        setFileUploadDialogOpen(true);
    };

    const handleFaqSubmit = async (faqData) => {
        try {
            setFaqDialogOpen(false);
            fetchPages();
            setError(null);
            console.log('FAQ added successfully:', faqData);
        } catch (err) {
            setError('خطا در اضافه کردن سوال و جواب');
            console.error('FAQ error:', err);
        }
    };

    const handleUpdatePage = async (pageData) => {
        try {
            await api.put(`/api/${website.id}/pages/${encodeURIComponent(selectedPageForView.url)}`, pageData);
            setEditDialogOpen(false);
            fetchPages();
            setError(null);
        } catch (err) {
            console.error('Update page error:', err);
            // نمایش پیام خطای دقیق از backend
            const errorMessage = err.response?.data?.detail || err.message || 'خطا در به‌روزرسانی صفحه';
            setError(errorMessage);
        }
    };

    const handleAddNewPage = async (pageData) => {
        try {
            await api.post(`/api/${website.id}/pages`, pageData);
            setAddDialogOpen(false);
            fetchPages();
            setError(null);
        } catch (err) {
            console.error('Add page error:', err);
            // نمایش پیام خطای دقیق از backend
            const errorMessage = err.response?.data?.detail || err.message || 'خطا در اضافه کردن صفحه';
            setError(errorMessage);
        }
    };

    const handleSelectPage = (pageUrl) => {
        setSelectedPages(prev =>
            prev.includes(pageUrl)
                ? prev.filter(url => url !== pageUrl)
                : [...prev, pageUrl]
        );
    };

    const handleSelectAll = () => {
        if (selectedPages.length === pages.length) {
            setSelectedPages([]);
        } else {
            setSelectedPages(pages.map(page => page.url));
        }
    };

    const handleBulkDelete = async () => {
        try {
            for (const pageUrl of selectedPages) {
                await api.delete(`/api/${website.id}/pages/${encodeURIComponent(pageUrl)}`);
            }
            setSelectedPages([]);
            fetchPages();
            setError(null);
        } catch (err) {
            setError('خطا در حذف صفحات');
            console.error('Bulk delete error:', err);
        }
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
                <Box display="flex" gap={1}>
                    <Tooltip title="اضافه کردن محتوا">
                        <Button
                            variant="contained"
                            color="primary"
                            startIcon={<AddIcon />}
                            endIcon={<ArrowDropDownIcon />}
                            onClick={handleAddMenuClick}
                        >
                            اضافه کردن
                        </Button>
                    </Tooltip>
                    <Menu
                        anchorEl={addMenuAnchor}
                        open={Boolean(addMenuAnchor)}
                        onClose={handleAddMenuClose}
                        anchorOrigin={{
                            vertical: 'bottom',
                            horizontal: 'left',
                        }}
                        transformOrigin={{
                            vertical: 'top',
                            horizontal: 'left',
                        }}
                    >
                        <MenuItem onClick={handleAddPage}>
                            <ListItemIcon>
                                <ArticleIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText>ایجاد یک صفحه جدید</ListItemText>
                        </MenuItem>
                        <MenuItem onClick={handleAddFAQ}>
                            <ListItemIcon>
                                <QuestionAnswerIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText>ایجاد یک پرسش و پاسخ جدید</ListItemText>
                        </MenuItem>
                        <MenuItem onClick={handleAddFile}>
                            <ListItemIcon>
                                <DescriptionIcon fontSize="small" />
                            </ListItemIcon>
                            <ListItemText>ایجاد با فایل‌های متنی</ListItemText>
                        </MenuItem>
                    </Menu>
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
                    {/* فقط ادمین‌ها می‌توانند تنظیمات کراولینگ را ببینند */}
                    {isAdmin && (
                        <Tooltip title="تنظیمات کراولینگ (فقط ادمین)">
                            <IconButton onClick={() => setSettingsDialogOpen(true)}>
                                <SettingsIcon />
                            </IconButton>
                        </Tooltip>
                    )}
                </Box>
            </Box>

            {/* بخش جستجو و فیلتر */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
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
                            />
                        </Grid>
                        <Grid item xs={12} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>فیلتر بر اساس</InputLabel>
                                <Select
                                    value={filterBy}
                                    onChange={(e) => setFilterBy(e.target.value)}
                                >
                                    <MenuItem value="all">همه</MenuItem>
                                    <MenuItem value="title">عنوان</MenuItem>
                                    <MenuItem value="text">محتوا</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>مرتب‌سازی بر اساس</InputLabel>
                                <Select
                                    value={sortBy}
                                    onChange={(e) => setSortBy(e.target.value)}
                                >
                                    <MenuItem value="title">عنوان</MenuItem>
                                    <MenuItem value="url">URL</MenuItem>
                                    <MenuItem value="links_count">تعداد لینک‌ها</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>ترتیب</InputLabel>
                                <Select
                                    value={sortOrder}
                                    onChange={(e) => setSortOrder(e.target.value)}
                                >
                                    <MenuItem value="asc">صعودی</MenuItem>
                                    <MenuItem value="desc">نزولی</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} md={2}>
                            <Button
                                fullWidth
                                variant="outlined"
                                onClick={handleClearSearch}
                                startIcon={<FilterIcon />}
                            >
                                پاک کردن
                            </Button>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
                    {error}
                </Alert>
            )}

            <Paper>
                {selectedPages.length > 0 && (
                    <Box sx={{ p: 2, bgcolor: 'primary.light', color: 'primary.contrastText' }}>
                        <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography>
                                {selectedPages.length} صفحه انتخاب شده
                            </Typography>
                            <Button
                                variant="contained"
                                color="error"
                                size="small"
                                onClick={handleBulkDelete}
                                startIcon={<DeleteIcon />}
                            >
                                حذف انتخاب شده‌ها
                            </Button>
                        </Box>
                    </Box>
                )}
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell padding="checkbox">
                                    <Checkbox
                                        checked={selectedPages.length === pages.length && pages.length > 0}
                                        indeterminate={selectedPages.length > 0 && selectedPages.length < pages.length}
                                        onChange={handleSelectAll}
                                    />
                                </TableCell>
                                <TableCell>عنوان</TableCell>
                                <TableCell>URL</TableCell>
                                <TableCell>تعداد لینک‌ها</TableCell>
                                <TableCell>عملیات</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loading ? (
                                <TableRow>
                                    <TableCell colSpan={5} align="center">
                                        <CircularProgress />
                                    </TableCell>
                                </TableRow>
                            ) : pages.length === 0 ? (
                                <TableRow>
                                    <TableCell colSpan={5} align="center">
                                        صفحه‌ای یافت نشد
                                    </TableCell>
                                </TableRow>
                            ) : (
                                pages.map((page, index) => (
                                    <TableRow key={index} selected={selectedPages.includes(page.url)}>
                                        <TableCell padding="checkbox">
                                            <Checkbox
                                                checked={selectedPages.includes(page.url)}
                                                onChange={() => handleSelectPage(page.url)}
                                            />
                                        </TableCell>
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
                                            <Tooltip title="ویرایش">
                                                <IconButton
                                                    size="small"
                                                    color="primary"
                                                    onClick={() => handleEditPage(page)}
                                                >
                                                    <EditIcon />
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

            {/* Dialog ویرایش صفحه */}
            <EditPageDialog
                open={editDialogOpen}
                onClose={() => setEditDialogOpen(false)}
                page={selectedPageForView}
                onSave={handleUpdatePage}
            />

            {/* Dialog اضافه کردن صفحه */}
            <AddPageDialog
                open={addDialogOpen}
                onClose={() => setAddDialogOpen(false)}
                onSave={handleAddNewPage}
            />

            {/* Dialog صادرات */}
            <ExportDialog
                open={exportDialogOpen}
                onClose={() => setExportDialogOpen(false)}
                onExport={handleExport}
            />

            {/* Dialog واردات */}
            <ImportDialog
                open={importDialogOpen}
                onClose={() => setImportDialogOpen(false)}
                onImport={handleImport}
            />

            {/* Dialog آپلود فایل */}
            <FileUploadDialog
                open={fileUploadDialogOpen}
                onClose={() => setFileUploadDialogOpen(false)}
                onUpload={handleFileUpload}
                websiteId={website.id}
            />

            {/* Dialog FAQ */}
            <FaqDialog
                open={faqDialogOpen}
                onClose={() => setFaqDialogOpen(false)}
                onSubmit={handleFaqSubmit}
                websiteId={website.id}
            />
        </Box>
    );
};

export default ResourceManager;
