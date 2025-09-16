import React, { useState, useEffect } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Button,
    TextField,
    Box,
    Typography,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Alert,
    CircularProgress,
    FormControlLabel,
    Checkbox
} from '@mui/material';

// Dialog ویرایش صفحه
export const EditPageDialog = ({ open, onClose, page, onSave }) => {
    const [formData, setFormData] = useState({
        title: '',
        text: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (page) {
            setFormData({
                title: page.title || '',
                text: page.text || page.text_preview || ''
            });
        }
    }, [page]);

    const handleSave = async () => {
        try {
            setLoading(true);
            setError(null);
            await onSave(formData);
        } catch (err) {
            console.error('Edit page error:', err);
            // نمایش پیام خطای دقیق از backend
            const errorMessage = err.response?.data?.detail || err.message || 'خطا در ذخیره تغییرات';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>ویرایش صفحه</DialogTitle>
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}
                <Box sx={{ pt: 2 }}>
                    <TextField
                        fullWidth
                        label="عنوان"
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        sx={{ mb: 2 }}
                    />
                    <TextField
                        fullWidth
                        label="محتوا"
                        multiline
                        rows={10}
                        value={formData.text}
                        onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                        sx={{ mb: 2 }}
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>انصراف</Button>
                <Button
                    onClick={handleSave}
                    variant="contained"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                    ذخیره
                </Button>
            </DialogActions>
        </Dialog>
    );
};

// Dialog اضافه کردن صفحه
export const AddPageDialog = ({ open, onClose, onSave }) => {
    const [formData, setFormData] = useState({
        url: '',
        title: '',
        text: '',
        links: []
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSave = async () => {
        try {
            setLoading(true);
            setError(null);

            if (!formData.url || !formData.title || !formData.text) {
                setError('تمام فیلدها الزامی است');
                return;
            }

            await onSave(formData);
            setFormData({ url: '', title: '', text: '', links: [] });
        } catch (err) {
            console.error('Add page error:', err);
            // نمایش پیام خطای دقیق از backend
            const errorMessage = err.response?.data?.detail || err.message || 'خطا در اضافه کردن صفحه';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
            <DialogTitle>اضافه کردن صفحه جدید</DialogTitle>
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}
                <Box sx={{ pt: 2 }}>
                    <TextField
                        fullWidth
                        label="URL"
                        value={formData.url}
                        onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                        sx={{ mb: 2 }}
                        required
                    />
                    <TextField
                        fullWidth
                        label="عنوان"
                        value={formData.title}
                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                        sx={{ mb: 2 }}
                        required
                    />
                    <TextField
                        fullWidth
                        label="محتوا"
                        multiline
                        rows={10}
                        value={formData.text}
                        onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                        sx={{ mb: 2 }}
                        required
                    />
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>انصراف</Button>
                <Button
                    onClick={handleSave}
                    variant="contained"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                    اضافه کردن
                </Button>
            </DialogActions>
        </Dialog>
    );
};

// Dialog صادرات
export const ExportDialog = ({ open, onClose, onExport }) => {
    const [format, setFormat] = useState('csv');
    const [exportType, setExportType] = useState('full');
    const [maxTextLength, setMaxTextLength] = useState(1000);
    const [loading, setLoading] = useState(false);

    const handleExport = async () => {
        try {
            setLoading(true);
            await onExport(format, exportType, maxTextLength);
        } catch (err) {
            console.error('Export error:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>صادرات داده‌ها</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                        <InputLabel>فرمت صادرات</InputLabel>
                        <Select
                            value={format}
                            onChange={(e) => setFormat(e.target.value)}
                        >
                            <MenuItem value="csv">CSV</MenuItem>
                            <MenuItem value="json">JSON</MenuItem>
                        </Select>
                    </FormControl>

                    <FormControl fullWidth>
                        <InputLabel>نوع صادرات</InputLabel>
                        <Select
                            value={exportType}
                            onChange={(e) => setExportType(e.target.value)}
                        >
                            <MenuItem value="full">صادرات کامل (برای بک‌آپ و واردات مجدد)</MenuItem>
                            <MenuItem value="excel_compatible">سازگار با Excel (متن‌های کوتاه شده)</MenuItem>
                        </Select>
                    </FormControl>

                    {exportType === "excel_compatible" && (
                        <TextField
                            label="حداکثر طول متن در هر سلول"
                            type="number"
                            value={maxTextLength}
                            onChange={(e) => setMaxTextLength(parseInt(e.target.value) || 1000)}
                            inputProps={{ min: 100, max: 10000 }}
                            helperText="متن‌های طولانی‌تر از این مقدار کوتاه می‌شوند - قابل واردات مجدد نیست"
                        />
                    )}

                    {exportType === "full" && (
                        <Alert severity="info">
                            صادرات کامل شامل تمام داده‌ها است و قابل واردات مجدد می‌باشد
                        </Alert>
                    )}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>انصراف</Button>
                <Button
                    onClick={handleExport}
                    variant="contained"
                    disabled={loading}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                    صادرات
                </Button>
            </DialogActions>
        </Dialog>
    );
};

// Dialog واردات
export const ImportDialog = ({ open, onClose, onImport }) => {
    const [file, setFile] = useState(null);
    const [format, setFormat] = useState('csv');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        setFile(selectedFile);

        // تشخیص فرمت بر اساس پسوند فایل
        if (selectedFile) {
            const extension = selectedFile.name.split('.').pop().toLowerCase();
            if (extension === 'json') {
                setFormat('json');
            } else if (extension === 'csv') {
                setFormat('csv');
            }
        }
    };

    const handleImport = async () => {
        try {
            setLoading(true);
            setError(null);

            if (!file) {
                setError('لطفاً فایل را انتخاب کنید');
                return;
            }

            await onImport(file, format);
        } catch (err) {
            setError('خطا در واردات فایل');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>واردات داده‌ها</DialogTitle>
            <DialogContent>
                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}
                <Box sx={{ pt: 2 }}>
                    <input
                        type="file"
                        accept=".csv,.json"
                        onChange={handleFileChange}
                        style={{ marginBottom: '16px' }}
                    />
                    <FormControl fullWidth>
                        <InputLabel>فرمت فایل</InputLabel>
                        <Select
                            value={format}
                            onChange={(e) => setFormat(e.target.value)}
                        >
                            <MenuItem value="csv">CSV</MenuItem>
                            <MenuItem value="json">JSON</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>انصراف</Button>
                <Button
                    onClick={handleImport}
                    variant="contained"
                    disabled={loading || !file}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                    واردات
                </Button>
            </DialogActions>
        </Dialog>
    );
};
