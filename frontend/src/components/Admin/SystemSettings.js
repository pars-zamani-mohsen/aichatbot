import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    Button,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Switch,
    FormControlLabel,
    Divider,
    Alert,
    LinearProgress,
    Chip,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Save,
    // Refresh, // حذف شده - دکمه بازگردانی حذف شده
    Security,
    Email,
    Storage,
    Speed,
    Notifications,
    CloudUpload
} from '@mui/icons-material';
import { dashboard } from '../../services/api';

const SystemSettings = () => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });
    const [settings, setSettings] = useState({
        // تنظیمات عمومی
        siteName: 'RAG Chatbot System',
        siteDescription: 'سیستم چت‌بات هوشمند با قابلیت RAG',
        maintenanceMode: false,
        debugMode: false,

        // تنظیمات ایمیل
        smtpServer: 'smtp.gmail.com',
        smtpPort: 587,
        smtpUsername: 'noreply@example.com',
        smtpPassword: '',
        emailFrom: 'noreply@example.com',

        // تنظیمات امنیت
        sessionTimeout: 30,
        maxLoginAttempts: 5,
        passwordMinLength: 8,
        requireEmailVerification: true,
        enableTwoFactor: false,

        // تنظیمات RAG
        defaultK: 5,
        maxResponseLength: 500,
        defaultTemperature: 0.7,
        defaultLanguage: 'fa',

        // تنظیمات کراولر
        maxPagesPerSite: 100,
        crawlDelay: 1,
        respectRobotsTxt: true,
        userAgent: 'RAG-Chatbot-Crawler/1.0',

        // تنظیمات ذخیره‌سازی
        maxFileSize: 10,
        allowedFileTypes: ['jpg', 'png', 'pdf', 'txt'],

        // تنظیمات اعلان‌ها
        emailNotifications: true,
        slackNotifications: false,
        slackWebhook: '',
        notifyOnError: true,
        notifyOnNewUser: true,

        // تنظیمات مدل‌های چت‌بات
        enableOpenAI: true,
        enableGemini: true,
        enableLocal: false,

        // تنظیمات timezone
        systemTimezone: 'Asia/Tehran',

        // تنظیمات Rate Limiting
        rateLimitChatRequests: 20,
        rateLimitChatWindow: 60,
        rateLimitCrawlRequests: 5,
        rateLimitCrawlWindow: 300,
        rateLimitApiRequests: 100,
        rateLimitApiWindow: 60,
        rateLimitWidgetRequests: 50,
        rateLimitWidgetWindow: 60
    });

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                setLoading(true);
                const [systemData, rateLimitsData] = await Promise.all([
                    dashboard.getAdminSystemSettings(),
                    dashboard.getRateLimitsSettings()
                ]);

                // ترکیب تنظیمات سیستم و rate limiting
                const combinedSettings = {
                    ...systemData,
                    ...rateLimitsData.rate_limits.chat,
                    ...rateLimitsData.rate_limits.crawl,
                    ...rateLimitsData.rate_limits.api,
                    ...rateLimitsData.rate_limits.widget,
                    // تبدیل به فرمت مورد نیاز
                    rateLimitChatRequests: rateLimitsData.rate_limits.chat.requests,
                    rateLimitChatWindow: rateLimitsData.rate_limits.chat.window,
                    rateLimitCrawlRequests: rateLimitsData.rate_limits.crawl.requests,
                    rateLimitCrawlWindow: rateLimitsData.rate_limits.crawl.window,
                    rateLimitApiRequests: rateLimitsData.rate_limits.api.requests,
                    rateLimitApiWindow: rateLimitsData.rate_limits.api.window,
                    rateLimitWidgetRequests: rateLimitsData.rate_limits.widget.requests,
                    rateLimitWidgetWindow: rateLimitsData.rate_limits.widget.window
                };

                setSettings(combinedSettings);
            } catch (error) {
                console.error('Error fetching system settings:', error);
                setMessage({ type: 'error', text: 'خطا در دریافت تنظیمات سیستم' });
            } finally {
                setLoading(false);
            }
        };

        fetchSettings();
    }, []);

    const handleSettingChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setMessage({ type: '', text: '' });

            // جداسازی تنظیمات سیستم و rate limiting
            const {
                rateLimitChatRequests,
                rateLimitChatWindow,
                rateLimitCrawlRequests,
                rateLimitCrawlWindow,
                rateLimitApiRequests,
                rateLimitApiWindow,
                rateLimitWidgetRequests,
                rateLimitWidgetWindow,
                ...systemSettings
            } = settings;

            // ذخیره تنظیمات سیستم
            await dashboard.updateAdminSystemSettings(systemSettings);

            // ذخیره تنظیمات rate limiting
            const rateLimitsSettings = {
                chat: {
                    requests: rateLimitChatRequests,
                    window: rateLimitChatWindow
                },
                crawl: {
                    requests: rateLimitCrawlRequests,
                    window: rateLimitCrawlWindow
                },
                api: {
                    requests: rateLimitApiRequests,
                    window: rateLimitApiWindow
                },
                widget: {
                    requests: rateLimitWidgetRequests,
                    window: rateLimitWidgetWindow
                }
            };

            await dashboard.updateRateLimitsSettings(rateLimitsSettings);

            setMessage({ type: 'success', text: 'تنظیمات سیستم با موفقیت ذخیره شد' });
        } catch (error) {
            console.error('Error saving system settings:', error);
            setMessage({ type: 'error', text: 'خطا در ذخیره تنظیمات سیستم' });
        } finally {
            setSaving(false);
        }
    };

    const handleReset = async () => {
        try {
            setLoading(true);
            setMessage({ type: '', text: '' });
            const data = await dashboard.getAdminSystemSettings();
            setSettings(data);
            setMessage({ type: 'success', text: 'تنظیمات به حالت اولیه بازگردانده شد' });
        } catch (error) {
            console.error('Error resetting system settings:', error);
            setMessage({ type: 'error', text: 'خطا در بازگردانی تنظیمات' });
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Box sx={{ p: 3 }}>
                <LinearProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box>
                    <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                        تنظیمات سیستم
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        مدیریت تنظیمات کلی سیستم و پیکربندی‌ها
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    {/* دکمه بازگردانی حذف شده */}
                    {/* <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={handleReset}
                    >
                        بازگردانی
                    </Button> */}
                    <Button
                        variant="contained"
                        startIcon={<Save />}
                        onClick={handleSave}
                        disabled={saving}
                    >
                        {saving ? 'در حال ذخیره...' : 'ذخیره تنظیمات'}
                    </Button>
                </Box>
            </Box>

            {message.text && (
                <Alert severity={message.type} sx={{ mb: 3 }}>
                    {message.text}
                </Alert>
            )}

            <Grid container spacing={3}>
                {/* تنظیمات عمومی */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Speed sx={{ mr: 1, color: 'primary.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات عمومی
                                </Typography>
                            </Box>

                            <TextField
                                fullWidth
                                label="نام سایت"
                                value={settings.siteName}
                                onChange={(e) => handleSettingChange('siteName', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="توضیحات سایت"
                                value={settings.siteDescription}
                                onChange={(e) => handleSettingChange('siteDescription', e.target.value)}
                                multiline
                                rows={2}
                                sx={{ mb: 2 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.maintenanceMode}
                                        onChange={(e) => handleSettingChange('maintenanceMode', e.target.checked)}
                                    />
                                }
                                label="حالت نگهداری"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.debugMode}
                                        onChange={(e) => handleSettingChange('debugMode', e.target.checked)}
                                    />
                                }
                                label="حالت دیباگ"
                            />
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات ایمیل */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Email sx={{ mr: 1, color: 'primary.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات ایمیل
                                </Typography>
                            </Box>

                            <TextField
                                fullWidth
                                label="SMTP Server"
                                value={settings.smtpServer}
                                onChange={(e) => handleSettingChange('smtpServer', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="SMTP Port"
                                type="number"
                                value={settings.smtpPort}
                                onChange={(e) => handleSettingChange('smtpPort', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="نام کاربری SMTP"
                                value={settings.smtpUsername}
                                onChange={(e) => handleSettingChange('smtpUsername', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="رمز عبور SMTP"
                                type="password"
                                value={settings.smtpPassword}
                                onChange={(e) => handleSettingChange('smtpPassword', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="ایمیل فرستنده"
                                value={settings.emailFrom}
                                onChange={(e) => handleSettingChange('emailFrom', e.target.value)}
                            />
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات امنیت */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Security sx={{ mr: 1, color: 'error.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات امنیت
                                </Typography>
                            </Box>

                            <TextField
                                fullWidth
                                label="مدت زمان نشست (دقیقه)"
                                type="number"
                                value={settings.sessionTimeout}
                                onChange={(e) => handleSettingChange('sessionTimeout', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="حداکثر تلاش ورود"
                                type="number"
                                value={settings.maxLoginAttempts}
                                onChange={(e) => handleSettingChange('maxLoginAttempts', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="حداقل طول رمز عبور"
                                type="number"
                                value={settings.passwordMinLength}
                                onChange={(e) => handleSettingChange('passwordMinLength', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.requireEmailVerification}
                                        onChange={(e) => handleSettingChange('requireEmailVerification', e.target.checked)}
                                    />
                                }
                                label="نیاز به تأیید ایمیل"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.enableTwoFactor}
                                        onChange={(e) => handleSettingChange('enableTwoFactor', e.target.checked)}
                                    />
                                }
                                label="احراز هویت دو مرحله‌ای"
                            />
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات RAG */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Storage sx={{ mr: 1, color: 'success.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات RAG
                                </Typography>
                            </Box>

                            <TextField
                                fullWidth
                                label="تعداد نتایج پیش‌فرض (K)"
                                type="number"
                                value={settings.defaultK}
                                onChange={(e) => handleSettingChange('defaultK', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="حداکثر طول پاسخ"
                                type="number"
                                value={settings.maxResponseLength}
                                onChange={(e) => handleSettingChange('maxResponseLength', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="دمای پیش‌فرض"
                                type="number"
                                step="0.1"
                                value={settings.defaultTemperature}
                                onChange={(e) => handleSettingChange('defaultTemperature', parseFloat(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>زبان پیش‌فرض</InputLabel>
                                <Select
                                    value={settings.defaultLanguage}
                                    label="زبان پیش‌فرض"
                                    onChange={(e) => handleSettingChange('defaultLanguage', e.target.value)}
                                >
                                    <MenuItem value="fa">فارسی</MenuItem>
                                    <MenuItem value="en">انگلیسی</MenuItem>
                                    <MenuItem value="ar">عربی</MenuItem>
                                </Select>
                            </FormControl>

                            <Divider sx={{ my: 2 }} />

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                                تنظیمات مدل‌های چت‌بات
                            </Typography>

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.enableOpenAI}
                                        onChange={(e) => handleSettingChange('enableOpenAI', e.target.checked)}
                                    />
                                }
                                label="فعال‌سازی OpenAI GPT"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.enableGemini}
                                        onChange={(e) => handleSettingChange('enableGemini', e.target.checked)}
                                    />
                                }
                                label="فعال‌سازی Google Gemini"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.enableLocal}
                                        onChange={(e) => handleSettingChange('enableLocal', e.target.checked)}
                                    />
                                }
                                label="فعال‌سازی مدل محلی (Ollama)"
                            />

                            <Divider sx={{ my: 2 }} />

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold' }}>
                                تنظیمات زمان
                            </Typography>

                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>منطقه زمانی سیستم</InputLabel>
                                <Select
                                    value={settings.systemTimezone}
                                    label="منطقه زمانی سیستم"
                                    onChange={(e) => handleSettingChange('systemTimezone', e.target.value)}
                                >
                                    <MenuItem value="Asia/Tehran">تهران (UTC+3:30)</MenuItem>
                                    <MenuItem value="UTC">UTC (UTC+0:00)</MenuItem>
                                    <MenuItem value="Europe/London">لندن (GMT)</MenuItem>
                                    <MenuItem value="America/New_York">نیویورک (EST)</MenuItem>
                                    <MenuItem value="Asia/Dubai">دبی (UTC+4:00)</MenuItem>
                                    <MenuItem value="Asia/Kolkata">کلکته (UTC+5:30)</MenuItem>
                                    <MenuItem value="Asia/Shanghai">شانگهای (UTC+8:00)</MenuItem>
                                    <MenuItem value="Asia/Tokyo">توکیو (UTC+9:00)</MenuItem>
                                    <MenuItem value="Europe/Paris">پاریس (CET)</MenuItem>
                                    <MenuItem value="Europe/Berlin">برلین (CET)</MenuItem>
                                    <MenuItem value="America/Los_Angeles">لس آنجلس (PST)</MenuItem>
                                    <MenuItem value="Australia/Sydney">سیدنی (AEST)</MenuItem>
                                </Select>
                            </FormControl>
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات کراولر */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <CloudUpload sx={{ mr: 1, color: 'warning.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات کراولر
                                </Typography>
                            </Box>

                            <TextField
                                fullWidth
                                label="حداکثر صفحات در هر سایت"
                                type="number"
                                value={settings.maxPagesPerSite}
                                onChange={(e) => handleSettingChange('maxPagesPerSite', parseInt(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="تأخیر کراول (ثانیه)"
                                type="number"
                                step="0.1"
                                value={settings.crawlDelay}
                                onChange={(e) => handleSettingChange('crawlDelay', parseFloat(e.target.value))}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="User Agent"
                                value={settings.userAgent}
                                onChange={(e) => handleSettingChange('userAgent', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.respectRobotsTxt}
                                        onChange={(e) => handleSettingChange('respectRobotsTxt', e.target.checked)}
                                    />
                                }
                                label="احترام به robots.txt"
                            />
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات اعلان‌ها */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Notifications sx={{ mr: 1, color: 'info.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات اعلان‌ها
                                </Typography>
                            </Box>

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.emailNotifications}
                                        onChange={(e) => handleSettingChange('emailNotifications', e.target.checked)}
                                    />
                                }
                                label="اعلان‌های ایمیل"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.slackNotifications}
                                        onChange={(e) => handleSettingChange('slackNotifications', e.target.checked)}
                                    />
                                }
                                label="اعلان‌های Slack"
                                sx={{ mb: 2 }}
                            />

                            {settings.slackNotifications && (
                                <TextField
                                    fullWidth
                                    label="Slack Webhook URL"
                                    value={settings.slackWebhook}
                                    onChange={(e) => handleSettingChange('slackWebhook', e.target.value)}
                                    sx={{ mb: 2 }}
                                />
                            )}

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.notifyOnError}
                                        onChange={(e) => handleSettingChange('notifyOnError', e.target.checked)}
                                    />
                                }
                                label="اعلان خطاها"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.notifyOnNewUser}
                                        onChange={(e) => handleSettingChange('notifyOnNewUser', e.target.checked)}
                                    />
                                }
                                label="اعلان کاربران جدید"
                            />
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات Rate Limiting */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Speed sx={{ mr: 1, color: 'info.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات Rate Limiting
                                </Typography>
                            </Box>

                            <Typography variant="subtitle2" sx={{ mb: 2, color: 'text.secondary' }}>
                                کنترل تعداد درخواست‌های مجاز برای جلوگیری از سوء استفاده
                            </Typography>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'primary.main' }}>
                                چت
                            </Typography>
                            <Grid container spacing={2} sx={{ mb: 3 }}>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="تعداد درخواست"
                                        type="number"
                                        value={settings.rateLimitChatRequests}
                                        onChange={(e) => handleSettingChange('rateLimitChatRequests', parseInt(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="بازه زمانی (ثانیه)"
                                        type="number"
                                        value={settings.rateLimitChatWindow}
                                        onChange={(e) => handleSettingChange('rateLimitChatWindow', parseInt(e.target.value))}
                                    />
                                </Grid>
                            </Grid>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'warning.main' }}>
                                کراول
                            </Typography>
                            <Grid container spacing={2} sx={{ mb: 3 }}>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="تعداد درخواست"
                                        type="number"
                                        value={settings.rateLimitCrawlRequests}
                                        onChange={(e) => handleSettingChange('rateLimitCrawlRequests', parseInt(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="بازه زمانی (ثانیه)"
                                        type="number"
                                        value={settings.rateLimitCrawlWindow}
                                        onChange={(e) => handleSettingChange('rateLimitCrawlWindow', parseInt(e.target.value))}
                                    />
                                </Grid>
                            </Grid>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'success.main' }}>
                                API عمومی
                            </Typography>
                            <Grid container spacing={2} sx={{ mb: 3 }}>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="تعداد درخواست"
                                        type="number"
                                        value={settings.rateLimitApiRequests}
                                        onChange={(e) => handleSettingChange('rateLimitApiRequests', parseInt(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="بازه زمانی (ثانیه)"
                                        type="number"
                                        value={settings.rateLimitApiWindow}
                                        onChange={(e) => handleSettingChange('rateLimitApiWindow', parseInt(e.target.value))}
                                    />
                                </Grid>
                            </Grid>

                            <Typography variant="h6" sx={{ mb: 2, fontWeight: 'bold', color: 'secondary.main' }}>
                                Widget
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="تعداد درخواست"
                                        type="number"
                                        value={settings.rateLimitWidgetRequests}
                                        onChange={(e) => handleSettingChange('rateLimitWidgetRequests', parseInt(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={6}>
                                    <TextField
                                        fullWidth
                                        label="بازه زمانی (ثانیه)"
                                        type="number"
                                        value={settings.rateLimitWidgetWindow}
                                        onChange={(e) => handleSettingChange('rateLimitWidgetWindow', parseInt(e.target.value))}
                                    />
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>


            </Grid>
        </Box>
    );
};

export default SystemSettings;
