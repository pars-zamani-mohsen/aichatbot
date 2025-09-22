import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Grid
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import api from '../../services/api';
import { dashboard } from '../../services/api';

const RAGSettings = ({ website }) => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [systemSettings, setSystemSettings] = useState({});

  useEffect(() => {
    if (website) {
      fetchRAGSettings();
      fetchSystemSettings();
    }
  }, [website]);

  const fetchRAGSettings = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/${website.id}/rag-settings`);
      setSettings(response.data.rag_settings || {});
    } catch (err) {
      setError('خطا در دریافت تنظیمات RAG');
      console.error('Fetch RAG settings error:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemSettings = async () => {
    try {
      const response = await dashboard.getSystemSettings();
      setSystemSettings(response);

      // بررسی و تصحیح مدل انتخاب شده
      validateAndFixSelectedModel(response);
    } catch (err) {
      console.error('Fetch system settings error:', err);
    }
  };

  const validateAndFixSelectedModel = (systemSettings) => {
    const currentModel = settings.chatbot_type || 'openai';
    let isValidModel = false;
    let fallbackModel = null;

    // بررسی اینکه مدل فعلی فعال است یا نه
    if (currentModel === 'openai' && systemSettings.enableOpenAI) {
      isValidModel = true;
    } else if (currentModel === 'gemini' && systemSettings.enableGemini) {
      isValidModel = true;
    } else if (currentModel === 'local' && systemSettings.enableLocal) {
      isValidModel = true;
    }

    // اگر مدل فعلی غیرفعال است، مدل جایگزین پیدا کن
    if (!isValidModel) {
      if (systemSettings.enableOpenAI) {
        fallbackModel = 'openai';
      } else if (systemSettings.enableGemini) {
        fallbackModel = 'gemini';
      } else if (systemSettings.enableLocal) {
        fallbackModel = 'local';
      }
    }

    // اگر مدل جایگزین پیدا شد، آن را تنظیم کن
    if (fallbackModel && fallbackModel !== currentModel) {
      setSettings(prev => ({
        ...prev,
        chatbot_type: fallbackModel
      }));
      setError(`مدل ${currentModel} غیرفعال شده است. مدل ${fallbackModel} به عنوان جایگزین انتخاب شد.`);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      await api.put(`/api/${website.id}/rag-settings`, settings);
      setSuccess('تنظیمات RAG با موفقیت ذخیره شد');
      setError(null);
    } catch (err) {
      setError('خطا در ذخیره تنظیمات RAG');
      console.error('Save RAG settings error:', err);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (!website) {
    return <Typography>لطفاً یک وب‌سایت انتخاب کنید</Typography>;
  }

  if (website.status !== 'ready') {
    return (
      <Alert severity="warning">
        وب‌سایت باید آماده باشد تا بتوانید تنظیمات RAG را تغییر دهید
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        تنظیمات RAG - {website.name || website.domain}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" p={3}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* تنظیمات اصلی */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                تنظیمات اصلی
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>مدل چت‌بات</InputLabel>
                <Select
                  value={settings.chatbot_type || 'openai'}
                  onChange={(e) => updateSetting('chatbot_type', e.target.value)}
                >
                  {systemSettings.enableOpenAI && (
                    <MenuItem value="openai">OpenAI GPT</MenuItem>
                  )}
                  {systemSettings.enableGemini && (
                    <MenuItem value="gemini">Google Gemini</MenuItem>
                  )}
                  {systemSettings.enableLocal && (
                    <MenuItem value="local">مدل محلی (Ollama)</MenuItem>
                  )}
                </Select>
              </FormControl>

              <TextField
                fullWidth
                label="تعداد منابع (k)"
                type="number"
                value={settings.k || 5}
                onChange={(e) => updateSetting('k', parseInt(e.target.value))}
                sx={{ mb: 2 }}
                helperText="تعداد منابعی که برای پاسخ استفاده می‌شود"
              />

              <TextField
                fullWidth
                label="حداکثر طول پاسخ"
                type="number"
                value={settings.max_response_length || 500}
                onChange={(e) => updateSetting('max_response_length', parseInt(e.target.value))}
                sx={{ mb: 2 }}
                helperText="حداکثر تعداد کاراکترهای پاسخ"
              />

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>زبان پاسخ</InputLabel>
                <Select
                  value={settings.language || 'persian'}
                  onChange={(e) => updateSetting('language', e.target.value)}
                >
                  <MenuItem value="persian">فارسی</MenuItem>
                  <MenuItem value="english">انگلیسی</MenuItem>
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>تن صدای پاسخ</InputLabel>
                <Select
                  value={settings.tone || 'professional'}
                  onChange={(e) => updateSetting('tone', e.target.value)}
                >
                  <MenuItem value="professional">حرفه‌ای</MenuItem>
                  <MenuItem value="friendly">دوستانه</MenuItem>
                  <MenuItem value="formal">رسمی</MenuItem>
                  <MenuItem value="casual">غیررسمی</MenuItem>
                </Select>
              </FormControl>
            </Paper>
          </Grid>

          {/* تنظیمات پیشرفته */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                تنظیمات پیشرفته
              </Typography>

              <Typography gutterBottom>Temperature (خلاقیت)</Typography>
              <Slider
                value={settings.temperature || 0.7}
                onChange={(e, value) => updateSetting('temperature', value)}
                min={0}
                max={1}
                step={0.1}
                marks={[
                  { value: 0, label: '0' },
                  { value: 0.5, label: '0.5' },
                  { value: 1, label: '1' }
                ]}
                sx={{ mb: 3 }}
              />

              <TextField
                fullWidth
                label="حداکثر طول context"
                type="number"
                value={settings.max_context_length || 2000}
                onChange={(e) => updateSetting('max_context_length', parseInt(e.target.value))}
                sx={{ mb: 2 }}
                helperText="حداکثر تعداد کاراکترهای context"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={settings.include_sources !== false}
                    onChange={(e) => updateSetting('include_sources', e.target.checked)}
                  />
                }
                label="نمایش منابع در پاسخ"
                sx={{ mb: 2 }}
              />
            </Paper>
          </Grid>

          {/* دکمه‌های عملیات */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" gap={2} flexWrap="wrap">
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveSettings}
                  disabled={saving}
                >
                  {saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات'}
                </Button>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default RAGSettings;
