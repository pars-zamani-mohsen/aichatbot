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
    LinearProgress
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';

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

// Dialog آپلود فایل
export const FileUploadDialog = ({ open, onClose, onUpload, websiteId }) => {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [uploadProgress, setUploadProgress] = useState(0);

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        if (selectedFile) {
            // بررسی نوع فایل
            const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword', 'text/plain'];
            const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
            const allowedExtensions = ['pdf', 'docx', 'doc', 'txt'];

            if (!allowedTypes.includes(selectedFile.type) && !allowedExtensions.includes(fileExtension)) {
                setError('فرمت فایل پشتیبانی نمی‌شود. فقط PDF، DOC، DOCX و TXT مجاز است.');
                return;
            }

            // بررسی اندازه فایل (10MB)
            if (selectedFile.size > 10 * 1024 * 1024) {
                setError('اندازه فایل نباید از 10 مگابایت بیشتر باشد.');
                return;
            }

            setFile(selectedFile);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError('لطفاً فایلی انتخاب کنید');
            return;
        }

        try {
            setLoading(true);
            setError(null);
            setUploadProgress(0);

            const formData = new FormData();
            formData.append('file', file);

            // شبیه‌سازی progress
            const progressInterval = setInterval(() => {
                setUploadProgress(prev => {
                    if (prev >= 90) {
                        clearInterval(progressInterval);
                        return 90;
                    }
                    return prev + 10;
                });
            }, 200);

            // استفاده از API base URL
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
            const response = await fetch(`${API_URL}/api/${websiteId}/upload`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                    // Content-Type را تنظیم نکن - browser خودش multipart/form-data را تنظیم می‌کند
                },
                body: formData
            });

            clearInterval(progressInterval);
            setUploadProgress(100);

            console.log('Upload response status:', response.status);
            console.log('Upload response headers:', response.headers);
            console.log('Upload response ok:', response.ok);

            if (!response.ok) {
                let errorMessage = 'خطا در آپلود فایل';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    // اگر response JSON نباشد، متن خام را استفاده کن
                    const errorText = await response.text();
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            let result;
            try {
                result = await response.json();
            } catch (e) {
                // اگر response JSON نباشد، یک object ساده بساز
                const responseText = await response.text();
                result = {
                    message: responseText || 'فایل با موفقیت آپلود شد',
                    filename: file.name
                };
            }

            // فراخوانی callback
            if (onUpload) {
                onUpload(result);
            }

            // پاک کردن فرم
            setFile(null);
            setUploadProgress(0);

            // بستن dialog
            onClose();

        } catch (err) {
            console.error('Upload error:', err);
            setError(err.message || 'خطا در آپلود فایل');
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setFile(null);
            setError(null);
            setUploadProgress(0);
            onClose();
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
            <DialogTitle>آپلود فایل</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Alert severity="info">
                        فایل‌های PDF، DOC، DOCX و TXT تا حداکثر 10 مگابایت قابل آپلود هستند.
                    </Alert>

                    <Box
                        sx={{
                            border: '2px dashed #ccc',
                            borderRadius: 2,
                            p: 3,
                            textAlign: 'center',
                            cursor: 'pointer',
                            '&:hover': {
                                borderColor: 'primary.main',
                                backgroundColor: 'action.hover'
                            }
                        }}
                        onClick={() => document.getElementById('file-input').click()}
                    >
                        <input
                            id="file-input"
                            type="file"
                            accept=".pdf,.doc,.docx,.txt"
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                            disabled={loading}
                        />

                        <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                        <Typography variant="h6" gutterBottom>
                            {file ? file.name : 'فایل را انتخاب کنید'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            کلیک کنید یا فایل را اینجا بکشید
                        </Typography>
                    </Box>

                    {file && (
                        <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" color="text.secondary">
                                نام فایل: {file.name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                اندازه: {(file.size / 1024 / 1024).toFixed(2)} مگابایت
                            </Typography>
                        </Box>
                    )}

                    {loading && (
                        <Box sx={{ mt: 2 }}>
                            <Typography variant="body2" gutterBottom>
                                در حال آپلود و پردازش فایل...
                            </Typography>
                            <LinearProgress
                                variant="determinate"
                                value={uploadProgress}
                                sx={{ mt: 1 }}
                            />
                            <Typography variant="caption" color="text.secondary">
                                {uploadProgress}%
                            </Typography>
                        </Box>
                    )}

                    {error && (
                        <Alert severity="error">
                            {error}
                        </Alert>
                    )}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={loading}>
                    انصراف
                </Button>
                <Button
                    onClick={handleUpload}
                    variant="contained"
                    disabled={loading || !file}
                    startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
                >
                    آپلود و پردازش
                </Button>
            </DialogActions>
        </Dialog>
    );
};

// Dialog FAQ
export const FaqDialog = ({ open, onClose, onSubmit, websiteId }) => {
    const [formData, setFormData] = useState({
        question: '',
        answer: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleChange = (field) => (event) => {
        setFormData(prev => ({
            ...prev,
            [field]: event.target.value
        }));
    };

    const handleSubmit = async () => {
        if (!formData.question.trim() || !formData.answer.trim()) {
            setError('لطفاً سوال و جواب را وارد کنید');
            return;
        }

        setLoading(true);
        setError(null);

        try {
            // ایجاد URL منحصر به فرد برای FAQ
            const faqUrl = `https://${websiteId}/faq/${Date.now()}`;
            
            const faqData = {
                url: faqUrl,
                title: formData.question,
                text: formData.answer,
                links: []
            };

            // ارسال به API
            const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
            const response = await fetch(`${API_URL}/api/${websiteId}/pages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(faqData)
            });

            if (!response.ok) {
                let errorMessage = 'خطا در اضافه کردن سوال و جواب';
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.detail || errorMessage;
                } catch (e) {
                    const errorText = await response.text();
                    errorMessage = errorText || errorMessage;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            
            // فراخوانی callback
            if (onSubmit) {
                onSubmit(result);
            }

            // پاک کردن فرم
            setFormData({ question: '', answer: '' });
            onClose();

        } catch (err) {
            setError(err.message || 'خطا در اضافه کردن سوال و جواب');
            console.error('FAQ submission error:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setFormData({ question: '', answer: '' });
            setError(null);
            onClose();
        }
    };

    return (
        <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
            <DialogTitle>ایجاد سوال و جواب جدید</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <Alert severity="info">
                        سوال و جواب شما به عنوان یک صفحه جدید به سیستم اضافه می‌شود و در جستجو قابل دسترسی خواهد بود.
                    </Alert>
                    
                    <TextField
                        fullWidth
                        label="سوال"
                        value={formData.question}
                        onChange={handleChange('question')}
                        multiline
                        rows={2}
                        placeholder="سوال مشتری را اینجا وارد کنید..."
                        disabled={loading}
                    />
                    
                    <TextField
                        fullWidth
                        label="جواب"
                        value={formData.answer}
                        onChange={handleChange('answer')}
                        multiline
                        rows={6}
                        placeholder="جواب کامل را اینجا وارد کنید..."
                        disabled={loading}
                    />
                    
                    {error && (
                        <Alert severity="error">
                            {error}
                        </Alert>
                    )}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={handleClose} disabled={loading}>
                    انصراف
                </Button>
                <Button
                    onClick={handleSubmit}
                    variant="contained"
                    disabled={loading || !formData.question.trim() || !formData.answer.trim()}
                    startIcon={loading ? <CircularProgress size={20} /> : null}
                >
                    {loading ? 'در حال ذخیره...' : 'ذخیره سوال و جواب'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};
