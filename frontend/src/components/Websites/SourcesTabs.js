import React, { useState, useRef } from 'react';
import {
    Box,
    Typography,
    Button,
    TextField,
    Alert,
    Paper,
    IconButton,
    Chip,
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    Divider,
    CircularProgress,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    FormControl,
    InputLabel,
    Select,
    MenuItem
} from '@mui/material';
import {
    CloudUpload as CloudUploadIcon,
    Delete as DeleteIcon,
    Add as AddIcon,
    CheckCircle as CheckCircleIcon,
    Error as ErrorIcon
} from '@mui/icons-material';

// File Upload Tab
export const FileUploadTab = ({ website, onSuccess, onError, onLoading }) => {
    const [dragOver, setDragOver] = useState(false);
    const [uploadedFiles, setUploadedFiles] = useState([]);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        setDragOver(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setDragOver(false);
        const files = Array.from(e.dataTransfer.files);
        handleFiles(files);
    };

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        handleFiles(files);
    };

    const handleFiles = async (files) => {
        const allowedTypes = ['application/pdf', 'text/plain', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/msword'];
        const maxSize = 40 * 1024 * 1024; // 40MB

        for (const file of files) {
            if (!allowedTypes.includes(file.type)) {
                onError(`فرمت فایل ${file.name} پشتیبانی نمی‌شود. فرمت‌های مجاز: PDF, TXT, DOCX, DOC`);
                continue;
            }

            if (file.size > maxSize) {
                onError(`حجم فایل ${file.name} بیش از 40 مگابایت است`);
                continue;
            }

            const fileId = Date.now() + Math.random();
            const newFile = {
                id: fileId,
                name: file.name,
                size: file.size,
                type: file.type,
                status: 'uploading',
                file: file
            };

            setUploadedFiles(prev => [...prev, newFile]);

            try {
                onLoading(true);
                const formData = new FormData();
                formData.append('file', file);

                const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
                const response = await fetch(`${API_URL}/api/${website.id}/upload`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: formData
                });

                if (!response.ok) {
                    throw new Error('خطا در آپلود فایل');
                }

                const result = await response.json();

                setUploadedFiles(prev =>
                    prev.map(f =>
                        f.id === fileId
                            ? { ...f, status: 'success', result }
                            : f
                    )
                );

                onSuccess(`فایل ${file.name} با موفقیت آپلود شد`);
            } catch (error) {
                setUploadedFiles(prev =>
                    prev.map(f =>
                        f.id === fileId
                            ? { ...f, status: 'error' }
                            : f
                    )
                );
                onError(`خطا در آپلود فایل ${file.name}: ${error.message}`);
            } finally {
                onLoading(false);
            }
        }
    };

    const removeFile = (fileId) => {
        setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
    };

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <Box>
            {/* Upload Area */}
            <Paper
                sx={{
                    p: 4,
                    textAlign: 'center',
                    border: dragOver ? '2px dashed #1976d2' : '2px dashed #e0e0e0',
                    backgroundColor: dragOver ? '#f5f5f5' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    mb: 3
                }}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <CloudUploadIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.primary" gutterBottom>
                    کلیک کنید یا فایل را اینجا بکشید
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    فایل‌های PDF، CSV، DOCX یا TXT خود را اینجا بکشید، یا کلیک کنید تا انتخاب کنید. (حداکثر 40 مگابایت)
                </Typography>
                <Button
                    variant="contained"
                    color="primary"
                    startIcon={<CloudUploadIcon />}
                    sx={{ borderRadius: 2 }}
                >
                    آپلود فایل
                </Button>
            </Paper>

            <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".pdf,.csv,.docx,.txt,.doc"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
            />

            {/* Uploaded Files List */}
            {uploadedFiles.length > 0 && (
                <Box>
                    <Typography variant="h6" gutterBottom>
                        فایل‌های آپلود شده
                    </Typography>
                    <List>
                        {uploadedFiles.map((file, index) => (
                            <React.Fragment key={file.id}>
                                <ListItem>
                                    <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
                                        {file.status === 'success' && <CheckCircleIcon color="success" />}
                                        {file.status === 'error' && <ErrorIcon color="error" />}
                                        {file.status === 'uploading' && <CircularProgress size={20} />}
                                    </Box>
                                    <ListItemText
                                        primary={file.name}
                                        secondary={`${formatFileSize(file.size)} - ${file.type}`}
                                    />
                                    <ListItemSecondaryAction>
                                        <IconButton
                                            edge="end"
                                            onClick={() => removeFile(file.id)}
                                            disabled={file.status === 'uploading'}
                                        >
                                            <DeleteIcon />
                                        </IconButton>
                                    </ListItemSecondaryAction>
                                </ListItem>
                                {index < uploadedFiles.length - 1 && <Divider />}
                            </React.Fragment>
                        ))}
                    </List>
                </Box>
            )}
        </Box>
    );
};

// Website URL Tab
export const WebsiteUrlTab = ({ website, onSuccess, onError, onLoading }) => {
    const [url, setUrl] = useState('');
    const [urls, setUrls] = useState([]);

    const handleAddUrl = async () => {
        if (!url.trim()) {
            onError('لطفاً آدرس وب‌سایت را وارد کنید');
            return;
        }

        try {
            onLoading(true);
            // شبیه‌سازی اضافه کردن URL
            const newUrl = {
                id: Date.now(),
                url: url.trim(),
                status: 'pending'
            };

            setUrls(prev => [...prev, newUrl]);
            setUrl('');
            onSuccess(`آدرس ${url} اضافه شد`);
        } catch (error) {
            onError(`خطا در اضافه کردن آدرس: ${error.message}`);
        } finally {
            onLoading(false);
        }
    };

    const removeUrl = (id) => {
        setUrls(prev => prev.filter(u => u.id !== id));
    };

    return (
        <Box>
            <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                    اضافه کردن آدرس وب‌سایت
                </Typography>
                <Box display="flex" gap={2} alignItems="flex-start">
                    <TextField
                        fullWidth
                        label="آدرس وب‌سایت"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="https://example.com"
                        variant="outlined"
                    />
                    <Button
                        variant="contained"
                        onClick={handleAddUrl}
                        startIcon={<AddIcon />}
                        sx={{ minWidth: 120 }}
                    >
                        اضافه کردن
                    </Button>
                </Box>
            </Box>

            {urls.length > 0 && (
                <Box>
                    <Typography variant="h6" gutterBottom>
                        آدرس‌های اضافه شده
                    </Typography>
                    <List>
                        {urls.map((urlItem, index) => (
                            <React.Fragment key={urlItem.id}>
                                <ListItem>
                                    <ListItemText primary={urlItem.url} />
                                    <ListItemSecondaryAction>
                                        <IconButton edge="end" onClick={() => removeUrl(urlItem.id)}>
                                            <DeleteIcon />
                                        </IconButton>
                                    </ListItemSecondaryAction>
                                </ListItem>
                                {index < urls.length - 1 && <Divider />}
                            </React.Fragment>
                        ))}
                    </List>
                </Box>
            )}
        </Box>
    );
};

// Text Tab
export const TextTab = ({ website, onSuccess, onError, onLoading }) => {
    const [text, setText] = useState('');
    const [title, setTitle] = useState('');

    const handleSubmit = async () => {
        if (!title.trim() || !text.trim()) {
            onError('لطفاً عنوان و متن را وارد کنید');
            return;
        }

        try {
            onLoading(true);
            // شبیه‌سازی اضافه کردن متن
            onSuccess(`متن "${title}" با موفقیت اضافه شد`);
            setTitle('');
            setText('');
        } catch (error) {
            onError(`خطا در اضافه کردن متن: ${error.message}`);
        } finally {
            onLoading(false);
        }
    };

    return (
        <Box>
            <Typography variant="h6" gutterBottom>
                اضافه کردن متن
            </Typography>
            <Box sx={{ mb: 3 }}>
                <TextField
                    fullWidth
                    label="عنوان"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="عنوان متن"
                    variant="outlined"
                    sx={{ mb: 2 }}
                />
                <TextField
                    fullWidth
                    label="متن"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="متن خود را اینجا وارد کنید..."
                    multiline
                    rows={8}
                    variant="outlined"
                />
            </Box>
            <Button
                variant="contained"
                onClick={handleSubmit}
                startIcon={<AddIcon />}
                disabled={!title.trim() || !text.trim()}
            >
                اضافه کردن متن
            </Button>
        </Box>
    );
};

// Export Dialog
export const ExportDialog = ({ open, onClose, onExport }) => {
    const [format, setFormat] = useState('csv');
    const [exportType, setExportType] = useState('full');
    const [maxTextLength, setMaxTextLength] = useState(1000);

    const handleExport = () => {
        onExport(format, exportType, maxTextLength);
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>صادرات داده‌ها</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                        <InputLabel>فرمت</InputLabel>
                        <Select value={format} onChange={(e) => setFormat(e.target.value)}>
                            <MenuItem value="csv">CSV</MenuItem>
                            <MenuItem value="json">JSON</MenuItem>
                        </Select>
                    </FormControl>
                    
                    <FormControl fullWidth>
                        <InputLabel>نوع صادرات</InputLabel>
                        <Select value={exportType} onChange={(e) => setExportType(e.target.value)}>
                            <MenuItem value="full">کامل</MenuItem>
                            <MenuItem value="excel_compatible">سازگار با Excel</MenuItem>
                        </Select>
                    </FormControl>
                    
                    {exportType === 'excel_compatible' && (
                        <TextField
                            fullWidth
                            label="حداکثر طول متن"
                            type="number"
                            value={maxTextLength}
                            onChange={(e) => setMaxTextLength(parseInt(e.target.value))}
                        />
                    )}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>انصراف</Button>
                <Button onClick={handleExport} variant="contained">
                    صادرات
                </Button>
            </DialogActions>
        </Dialog>
    );
};

// Import Dialog
export const ImportDialog = ({ open, onClose, onImport }) => {
    const [format, setFormat] = useState('csv');
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleFileChange = (event) => {
        const selectedFile = event.target.files[0];
        setFile(selectedFile);
    };

    const handleImport = async () => {
        if (!file) return;

        setLoading(true);
        try {
            const text = await file.text();
            let data;
            
            if (format === 'json') {
                data = JSON.parse(text);
            } else {
                // For CSV, we'll send the raw text and let backend parse it
                data = text;
            }

            onImport({
                format: format,
                data: data
            });
        } catch (error) {
            console.error('Import error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
            <DialogTitle>واردات داده‌ها</DialogTitle>
            <DialogContent>
                <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <FormControl fullWidth>
                        <InputLabel>فرمت فایل</InputLabel>
                        <Select value={format} onChange={(e) => setFormat(e.target.value)}>
                            <MenuItem value="csv">CSV</MenuItem>
                            <MenuItem value="json">JSON</MenuItem>
                        </Select>
                    </FormControl>
                    
                    <input
                        type="file"
                        accept={format === 'json' ? '.json' : '.csv'}
                        onChange={handleFileChange}
                        style={{ display: 'none' }}
                        id="import-file-input"
                    />
                    <label htmlFor="import-file-input">
                        <Button variant="outlined" component="span" fullWidth>
                            انتخاب فایل
                        </Button>
                    </label>
                    
                    {file && (
                        <Typography variant="body2" color="text.secondary">
                            فایل انتخاب شده: {file.name}
                        </Typography>
                    )}
                </Box>
            </DialogContent>
            <DialogActions>
                <Button onClick={onClose}>انصراف</Button>
                <Button 
                    onClick={handleImport} 
                    variant="contained" 
                    disabled={!file || loading}
                >
                    {loading ? 'در حال واردات...' : 'واردات'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};


