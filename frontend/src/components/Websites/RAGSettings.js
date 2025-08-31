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
  Divider,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import {
  Settings as SettingsIcon,
  PlayArrow as TestIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import api from '../../services/api';

const RAGSettings = ({ website }) => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [testQuery, setTestQuery] = useState('');
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    if (website) {
      fetchRAGSettings();
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

  const handleTestQuery = async () => {
    if (!testQuery.trim()) {
      setError('لطفاً پرسش خود را وارد کنید');
      return;
    }

    try {
      setTesting(true);
      const response = await api.post(`/api/${website.id}/test-rag`, {
        query: testQuery
      });
      setTestResult(response.data);
      setError(null);
    } catch (err) {
      setError('خطا در تست پرسش');
      console.error('Test RAG error:', err);
    } finally {
      setTesting(false);
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
                  <MenuItem value="openai">OpenAI GPT</MenuItem>
                  <MenuItem value="gemini">Google Gemini</MenuItem>
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

          {/* تست RAG */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                تست RAG
              </Typography>

              <Box display="flex" gap={2} sx={{ mb: 2 }}>
                <TextField
                  fullWidth
                  label="پرسش تست"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="پرسش خود را اینجا بنویسید..."
                />
                <Button
                  variant="contained"
                  startIcon={testing ? <CircularProgress size={20} /> : <TestIcon />}
                  onClick={handleTestQuery}
                  disabled={testing || !testQuery.trim()}
                >
                  تست
                </Button>
              </Box>

              {testResult && (
                <Card sx={{ mt: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      پاسخ:
                    </Typography>
                    <Typography paragraph>
                      {testResult.response}
                    </Typography>

                    {testResult.sources && testResult.sources.length > 0 && (
                      <>
                        <Divider sx={{ my: 2 }} />
                        <Typography variant="h6" gutterBottom>
                          منابع:
                        </Typography>
                        {testResult.sources.map((source, index) => (
                          <Typography key={index} variant="body2" color="text.secondary">
                            {index + 1}. {source}
                          </Typography>
                        ))}
                      </>
                    )}
                  </CardContent>
                </Card>
              )}
            </Paper>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default RAGSettings;
