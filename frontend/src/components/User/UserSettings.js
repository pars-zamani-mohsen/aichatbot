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
    Avatar,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Save,
    Refresh,
    Security,
    Email,
    Notifications,
    Person,
    Language,
    Palette,
    Visibility,
    VisibilityOff
} from '@mui/icons-material';

const UserSettings = () => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [settings, setSettings] = useState({
        // اطلاعات شخصی
        firstName: 'علی',
        lastName: 'احمدی',
        email: 'user@example.com',
        phone: '+98 912 123 4567',

        // تنظیمات امنیت
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        twoFactorEnabled: false,

        // تنظیمات اعلان‌ها
        emailNotifications: true,
        pushNotifications: true,
        smsNotifications: false,
        notifyOnNewConversation: true,
        notifyOnWebsiteUpdate: true,

        // تنظیمات ظاهری
        language: 'fa',
        theme: 'light',
        timezone: 'Asia/Tehran',

        // تنظیمات RAG
        defaultK: 5,
        maxResponseLength: 500,
        defaultTemperature: 0.7,
        defaultLanguage: 'fa'
    });

    useEffect(() => {
        // شبیه‌سازی دریافت تنظیمات
        setTimeout(() => {
            setLoading(false);
        }, 1000);
    }, []);

    const handleSettingChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSave = async () => {
        setSaving(true);
        // شبیه‌سازی ذخیره تنظیمات
        setTimeout(() => {
            setSaving(false);
            // نمایش پیام موفقیت
        }, 2000);
    };

    const handleReset = () => {
        // بازگردانی تنظیمات پیش‌فرض
        setSettings({
            firstName: 'علی',
            lastName: 'احمدی',
            email: 'user@example.com',
            phone: '+98 912 123 4567',
            currentPassword: '',
            newPassword: '',
            confirmPassword: '',
            twoFactorEnabled: false,
            emailNotifications: true,
            pushNotifications: true,
            smsNotifications: false,
            notifyOnNewConversation: true,
            notifyOnWebsiteUpdate: true,
            language: 'fa',
            theme: 'light',
            timezone: 'Asia/Tehran',
            defaultK: 5,
            maxResponseLength: 500,
            defaultTemperature: 0.7,
            defaultLanguage: 'fa'
        });
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
                        تنظیمات حساب کاربری
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        مدیریت اطلاعات شخصی و تنظیمات حساب
                    </Typography>
                </Box>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                        variant="outlined"
                        startIcon={<Refresh />}
                        onClick={handleReset}
                    >
                        بازگردانی
                    </Button>
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

            <Grid container spacing={3}>
                {/* اطلاعات شخصی */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Person sx={{ mr: 1, color: 'primary.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    اطلاعات شخصی
                                </Typography>
                            </Box>

                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Avatar sx={{ width: 64, height: 64, mr: 2 }}>
                                    {settings.firstName.charAt(0)}
                                </Avatar>
                                <Box>
                                    <Typography variant="h6">{settings.firstName} {settings.lastName}</Typography>
                                    <Typography variant="body2" color="text.secondary">{settings.email}</Typography>
                                </Box>
                            </Box>

                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="نام"
                                        value={settings.firstName}
                                        onChange={(e) => handleSettingChange('firstName', e.target.value)}
                                        sx={{ mb: 2 }}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                    <TextField
                                        fullWidth
                                        label="نام خانوادگی"
                                        value={settings.lastName}
                                        onChange={(e) => handleSettingChange('lastName', e.target.value)}
                                        sx={{ mb: 2 }}
                                    />
                                </Grid>
                            </Grid>

                            <TextField
                                fullWidth
                                label="ایمیل"
                                type="email"
                                value={settings.email}
                                onChange={(e) => handleSettingChange('email', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="شماره تلفن"
                                value={settings.phone}
                                onChange={(e) => handleSettingChange('phone', e.target.value)}
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
                                label="رمز عبور فعلی"
                                type={showPassword ? 'text' : 'password'}
                                value={settings.currentPassword}
                                onChange={(e) => handleSettingChange('currentPassword', e.target.value)}
                                sx={{ mb: 2 }}
                                InputProps={{
                                    endAdornment: (
                                        <IconButton
                                            onClick={() => setShowPassword(!showPassword)}
                                            edge="end"
                                        >
                                            {showPassword ? <VisibilityOff /> : <Visibility />}
                                        </IconButton>
                                    )
                                }}
                            />

                            <TextField
                                fullWidth
                                label="رمز عبور جدید"
                                type={showPassword ? 'text' : 'password'}
                                value={settings.newPassword}
                                onChange={(e) => handleSettingChange('newPassword', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <TextField
                                fullWidth
                                label="تأیید رمز عبور جدید"
                                type={showPassword ? 'text' : 'password'}
                                value={settings.confirmPassword}
                                onChange={(e) => handleSettingChange('confirmPassword', e.target.value)}
                                sx={{ mb: 2 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.twoFactorEnabled}
                                        onChange={(e) => handleSettingChange('twoFactorEnabled', e.target.checked)}
                                    />
                                }
                                label="احراز هویت دو مرحله‌ای"
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
                                        checked={settings.pushNotifications}
                                        onChange={(e) => handleSettingChange('pushNotifications', e.target.checked)}
                                    />
                                }
                                label="اعلان‌های push"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.smsNotifications}
                                        onChange={(e) => handleSettingChange('smsNotifications', e.target.checked)}
                                    />
                                }
                                label="اعلان‌های پیامک"
                                sx={{ mb: 2 }}
                            />

                            <Divider sx={{ my: 2 }} />

                            <Typography variant="subtitle2" sx={{ mb: 2 }}>
                                انواع اعلان‌ها:
                            </Typography>

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.notifyOnNewConversation}
                                        onChange={(e) => handleSettingChange('notifyOnNewConversation', e.target.checked)}
                                    />
                                }
                                label="گفتگوی جدید"
                                sx={{ mb: 1 }}
                            />

                            <FormControlLabel
                                control={
                                    <Switch
                                        checked={settings.notifyOnWebsiteUpdate}
                                        onChange={(e) => handleSettingChange('notifyOnWebsiteUpdate', e.target.checked)}
                                    />
                                }
                                label="به‌روزرسانی وب‌سایت"
                            />
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات ظاهری */}
                <Grid item xs={12} md={6}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Palette sx={{ mr: 1, color: 'secondary.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات ظاهری
                                </Typography>
                            </Box>

                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>زبان</InputLabel>
                                <Select
                                    value={settings.language}
                                    label="زبان"
                                    onChange={(e) => handleSettingChange('language', e.target.value)}
                                >
                                    <MenuItem value="fa">فارسی</MenuItem>
                                    <MenuItem value="en">انگلیسی</MenuItem>
                                    <MenuItem value="ar">عربی</MenuItem>
                                </Select>
                            </FormControl>

                            <FormControl fullWidth sx={{ mb: 2 }}>
                                <InputLabel>تم</InputLabel>
                                <Select
                                    value={settings.theme}
                                    label="تم"
                                    onChange={(e) => handleSettingChange('theme', e.target.value)}
                                >
                                    <MenuItem value="light">روشن</MenuItem>
                                    <MenuItem value="dark">تیره</MenuItem>
                                    <MenuItem value="auto">خودکار</MenuItem>
                                </Select>
                            </FormControl>

                            <FormControl fullWidth>
                                <InputLabel>منطقه زمانی</InputLabel>
                                <Select
                                    value={settings.timezone}
                                    label="منطقه زمانی"
                                    onChange={(e) => handleSettingChange('timezone', e.target.value)}
                                >
                                    <MenuItem value="Asia/Tehran">تهران (UTC+3:30)</MenuItem>
                                    <MenuItem value="UTC">UTC</MenuItem>
                                    <MenuItem value="America/New_York">نیویورک (UTC-5)</MenuItem>
                                    <MenuItem value="Europe/London">لندن (UTC+0)</MenuItem>
                                </Select>
                            </FormControl>
                        </CardContent>
                    </Card>
                </Grid>

                {/* تنظیمات RAG */}
                <Grid item xs={12}>
                    <Card>
                        <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                                <Language sx={{ mr: 1, color: 'success.main' }} />
                                <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
                                    تنظیمات RAG
                                </Typography>
                            </Box>

                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6} md={3}>
                                    <TextField
                                        fullWidth
                                        label="تعداد نتایج پیش‌فرض (K)"
                                        type="number"
                                        value={settings.defaultK}
                                        onChange={(e) => handleSettingChange('defaultK', parseInt(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6} md={3}>
                                    <TextField
                                        fullWidth
                                        label="حداکثر طول پاسخ"
                                        type="number"
                                        value={settings.maxResponseLength}
                                        onChange={(e) => handleSettingChange('maxResponseLength', parseInt(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6} md={3}>
                                    <TextField
                                        fullWidth
                                        label="دمای پیش‌فرض"
                                        type="number"
                                        step="0.1"
                                        value={settings.defaultTemperature}
                                        onChange={(e) => handleSettingChange('defaultTemperature', parseFloat(e.target.value))}
                                    />
                                </Grid>
                                <Grid item xs={12} sm={6} md={3}>
                                    <FormControl fullWidth>
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
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
};

export default UserSettings;
