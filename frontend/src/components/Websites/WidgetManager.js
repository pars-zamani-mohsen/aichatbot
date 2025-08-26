import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Alert,
  Snackbar,
  Paper,
  Divider,
  Chip,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  Code as CodeIcon,
  Preview as PreviewIcon,
  Clear as ClearIcon
} from '@mui/icons-material';
import api from '../../services/api';

const WidgetManager = ({ website }) => {
  const [publicKey, setPublicKey] = useState('');
  const [widgetSnippet, setWidgetSnippet] = useState('');
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [showSnippet, setShowSnippet] = useState(false);

  useEffect(() => {
    // اول کلید ذخیره شده در localStorage را بررسی کن
    const savedKey = localStorage.getItem('widget_public_key');
    if (savedKey) {
      setPublicKey(savedKey);
    } else if (website?.public_key) {
      // اگر کلید ذخیره شده نبود، از وب‌سایت بگیر
      setPublicKey(website.public_key);
      localStorage.setItem('widget_public_key', website.public_key);
    }
  }, [website]);

  const generateWidgetKey = async () => {
    if (!website) return;

    setLoading(true);
    try {
      const response = await api.post(`/api/${website.id}/generate-widget-key`);
      const newPublicKey = response.data.public_key;
      setPublicKey(newPublicKey);

      // ذخیره کلید در localStorage
      localStorage.setItem('widget_public_key', newPublicKey);

      setSnackbar({
        open: true,
        message: 'کلید عمومی با موفقیت تولید شد و ذخیره شد',
        severity: 'success'
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'خطا در تولید کلید عمومی',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const clearWidgetKey = () => {
    localStorage.removeItem('widget_public_key');
    setPublicKey('');
    setSnackbar({
      open: true,
      message: 'کلید عمومی پاک شد',
      severity: 'info'
    });
  };

  const getWidgetSnippet = async () => {
    if (!website) return;

    setLoading(true);
    try {
      const response = await api.get(`/api/widget/snippet/${website.id}`);
      setWidgetSnippet(response.data.snippet);
      setShowSnippet(true);
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'خطا در دریافت کد ویجت',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      setSnackbar({
        open: true,
        message: 'کد در کلیپ‌بورد کپی شد',
        severity: 'success'
      });
    });
  };

  const previewWidget = async () => {
    // ابتدا کد اسنیپت جدید را دریافت کن
    try {
      const response = await api.get(`/api/widget/snippet/${website.id}`);
      const freshSnippet = response.data.snippet;
      
      const newWindow = window.open('', '_blank');
      newWindow.document.write(`
        <!DOCTYPE html>
        <html dir="rtl" lang="fa">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>پیش‌نمایش ویجت چت</title>
          <style>
            body { font-family: 'Vazirmatn', Arial, sans-serif; margin: 0; padding: 20px; }
            .demo-content { max-width: 800px; margin: 0 auto; }
          </style>
        </head>
        <body>
          <div class="demo-content">
            <h1>پیش‌نمایش ویجت چت هوشمند</h1>
            <p>این صفحه برای نمایش عملکرد ویجت چت طراحی شده است. دکمه چت در گوشه سمت چپ پایین صفحه قرار دارد.</p>
            <p>برای تست ویجت، روی دکمه چت کلیک کنید و سوال خود را بپرسید.</p>
          </div>
          ${freshSnippet}
        </body>
        </html>
      `);
      newWindow.document.close();
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'خطا در دریافت کد ویجت برای پیش‌نمایش',
        severity: 'error'
      });
    }
  };

  if (!website) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" color="text.secondary">
            لطفاً یک وب‌سایت را انتخاب کنید
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            مدیریت ویجت چت
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            ویجت چت هوشمند برای وب‌سایت: {website.name || website.url}
          </Typography>

          <Divider sx={{ my: 2 }} />

          {/* کلید عمومی */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              کلید عمومی ویجت
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <TextField
                fullWidth
                size="small"
                value={publicKey}
                placeholder="کلید عمومی تولید نشده"
                InputProps={{ readOnly: true }}
              />
              <Tooltip title="تولید کلید جدید">
                <IconButton
                  onClick={generateWidgetKey}
                  disabled={loading}
                  color="primary"
                >
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
              {publicKey && (
                <>
                  <Tooltip title="کپی کلید">
                    <IconButton
                      onClick={() => copyToClipboard(publicKey)}
                      color="primary"
                    >
                      <CopyIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="پاک کردن کلید">
                    <IconButton
                      onClick={clearWidgetKey}
                      color="warning"
                    >
                      <ClearIcon />
                    </IconButton>
                  </Tooltip>
                </>
              )}
            </Box>
            <Typography variant="caption" color="text.secondary">
              این کلید برای احراز هویت ویجت استفاده می‌شود
            </Typography>
          </Box>

          {/* کد اسنیپت */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              کد اسنیپت ویجت
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button
                variant="outlined"
                startIcon={<CodeIcon />}
                onClick={getWidgetSnippet}
                disabled={loading || !publicKey}
              >
                دریافت کد ویجت
              </Button>
              {widgetSnippet && (
                <>
                  <Button
                    variant="outlined"
                    startIcon={<CopyIcon />}
                    onClick={() => copyToClipboard(widgetSnippet)}
                  >
                    کپی کد
                  </Button>
                  <Button
                    variant="outlined"
                    startIcon={<PreviewIcon />}
                    onClick={previewWidget}
                  >
                    پیش‌نمایش
                  </Button>
                </>
              )}
            </Box>

            {showSnippet && widgetSnippet && (
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  این کد را در بخش &lt;head&gt; یا قبل از تگ &lt;/body&gt; وب‌سایت خود قرار دهید:
                </Typography>
                <Box
                  component="pre"
                  sx={{
                    mt: 1,
                    p: 2,
                    bgcolor: 'white',
                    border: '1px solid #ddd',
                    borderRadius: 1,
                    overflow: 'auto',
                    fontSize: '12px',
                    maxHeight: '300px'
                  }}
                >
                  {widgetSnippet}
                </Box>
              </Paper>
            )}
          </Box>

          {/* راهنمای نصب */}
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              راهنمای نصب
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Chip label="1. کلید عمومی را تولید کنید" color="primary" variant="outlined" />
              <Chip label="2. کد ویجت را دریافت کنید" color="primary" variant="outlined" />
              <Chip label="3. کد را در وب‌سایت خود قرار دهید" color="primary" variant="outlined" />
              <Chip label="4. ویجت آماده استفاده است" color="success" variant="outlined" />
            </Box>
          </Box>
        </CardContent>
      </Card>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WidgetManager;
