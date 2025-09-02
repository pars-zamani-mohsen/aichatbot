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
    Tooltip,
    Snackbar,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions
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
import { auth } from '../../services/api';

const UserSettings = () => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [showPassword, setShowPassword] = useState(false);
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
    const [show2FADialog, setShow2FADialog] = useState(false);
    const [twoFACode, setTwoFACode] = useState('');
    const [twoFALoading, setTwoFALoading] = useState(false);
    const [twoFAEmail, setTwoFAEmail] = useState('');
    const [settings, setSettings] = useState({
        // اطلاعات شخصی
        firstName: '',
        lastName: '',
        email: '',
        phone: '',

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
        fetchUserSettings();
    }, []);

    const fetchUserSettings = async () => {
        try {
            setLoading(true);
            setError(null);

            const userSettings = await auth.getUserSettings();

            // تبدیل ساختار داده‌ها
            setSettings({
                // اطلاعات شخصی
                firstName: userSettings.personal?.firstName || '',
                lastName: userSettings.personal?.lastName || '',
                email: userSettings.personal?.email || '',
                phone: userSettings.personal?.phone || '',

                // تنظیمات امنیت
                currentPassword: '',
                newPassword: '',
                confirmPassword: '',
                twoFactorEnabled: userSettings.security?.twoFactorEnabled || false,

                // تنظیمات اعلان‌ها
                emailNotifications: userSettings.notifications?.emailNotifications ?? true,
                pushNotifications: userSettings.notifications?.pushNotifications ?? true,
                smsNotifications: userSettings.notifications?.smsNotifications ?? false,
                notifyOnNewConversation: userSettings.notifications?.notifyOnNewConversation ?? true,
                notifyOnWebsiteUpdate: userSettings.notifications?.notifyOnWebsiteUpdate ?? true,

                // تنظیمات ظاهری
                language: userSettings.appearance?.language || 'fa',
                theme: userSettings.appearance?.theme || 'light',
                timezone: userSettings.appearance?.timezone || 'Asia/Tehran',

                // تنظیمات RAG
                defaultK: userSettings.rag?.defaultK || 5,
                maxResponseLength: userSettings.rag?.maxResponseLength || 500,
                defaultTemperature: userSettings.rag?.defaultTemperature || 0.7,
                defaultLanguage: userSettings.rag?.defaultLanguage || 'fa'
            });
        } catch (err) {
            setError('خطا در دریافت تنظیمات کاربر');
            console.error('Error fetching user settings:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleSettingChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setError(null);

            // تبدیل ساختار داده‌ها برای ارسال به API
            const userSettings = {
                personal: {
                    firstName: settings.firstName,
                    lastName: settings.lastName,
                    email: settings.email,
                    phone: settings.phone
                },
                security: {
                    twoFactorEnabled: settings.twoFactorEnabled
                },
                notifications: {
                    emailNotifications: settings.emailNotifications,
                    pushNotifications: settings.pushNotifications,
                    smsNotifications: settings.smsNotifications,
                    notifyOnNewConversation: settings.notifyOnNewConversation,
                    notifyOnWebsiteUpdate: settings.notifyOnWebsiteUpdate
                },
                appearance: {
                    language: settings.language,
                    theme: settings.theme,
                    timezone: settings.timezone
                },
                rag: {
                    defaultK: settings.defaultK,
                    maxResponseLength: settings.maxResponseLength,
                    defaultTemperature: settings.defaultTemperature,
                    defaultLanguage: settings.defaultLanguage
                }
            };

            await auth.updateUserSettings(userSettings);

            setSnackbar({
                open: true,
                message: 'تنظیمات با موفقیت ذخیره شد',
                severity: 'success'
            });
        } catch (err) {
            setError('خطا در ذخیره تنظیمات');
            console.error('Error saving settings:', err);
        } finally {
            setSaving(false);
        }
    };

    const handleChangePassword = async () => {
        try {
            if (settings.newPassword !== settings.confirmPassword) {
                setSnackbar({
                    open: true,
                    message: 'رمز عبور جدید و تأیید آن مطابقت ندارند',
                    severity: 'error'
                });
                return;
            }

            if (settings.newPassword.length < 6) {
                setSnackbar({
                    open: true,
                    message: 'رمز عبور باید حداقل 6 کاراکتر باشد',
                    severity: 'error'
                });
                return;
            }

            await auth.changePassword({
                currentPassword: settings.currentPassword,
                newPassword: settings.newPassword,
                confirmPassword: settings.confirmPassword
            });

            // پاک کردن فیلدهای رمز عبور
            setSettings(prev => ({
                ...prev,
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            }));

            setSnackbar({
                open: true,
                message: 'رمز عبور با موفقیت تغییر کرد',
                severity: 'success'
            });
        } catch (err) {
            setSnackbar({
                open: true,
                message: err.response?.data?.detail || 'خطا در تغییر رمز عبور',
                severity: 'error'
            });
        }
    };

    const handleReset = () => {
        fetchUserSettings();
    };

    const handleEnable2FA = async () => {
        try {
            setTwoFALoading(true);
            setError(null);

            const response = await auth.enable2FA();
            setTwoFAEmail(response.email);
            setShow2FADialog(true);

            setSnackbar({
                open: true,
                message: 'کد احراز هویت به ایمیل شما ارسال شد',
                severity: 'info'
            });
        } catch (err) {
            setError(err.response?.data?.detail || 'خطا در فعال‌سازی احراز هویت دو مرحله‌ای');
        } finally {
            setTwoFALoading(false);
        }
    };

    const handleVerify2FA = async () => {
        if (!twoFACode.trim()) {
            setError('لطفاً کد احراز هویت را وارد کنید');
            return;
        }

        try {
            setTwoFALoading(true);
            setError(null);

            await auth.verify2FA(twoFACode);

            // به‌روزرسانی وضعیت 2FA
            setSettings(prev => ({
                ...prev,
                twoFactorEnabled: true
            }));

            setShow2FADialog(false);
            setTwoFACode('');

            setSnackbar({
                open: true,
                message: 'احراز هویت دو مرحله‌ای با موفقیت فعال شد',
                severity: 'success'
            });
        } catch (err) {
            setError(err.response?.data?.detail || 'کد احراز هویت اشتباه است');
        } finally {
            setTwoFALoading(false);
        }
    };

    const handleDisable2FA = async () => {
        try {
            setSaving(true);
            setError(null);

            await auth.disable2FA();

            // به‌روزرسانی وضعیت 2FA
            setSettings(prev => ({
                ...prev,
                twoFactorEnabled: false
            }));

            setSnackbar({
                open: true,
                message: 'احراز هویت دو مرحله‌ای غیرفعال شد',
                severity: 'success'
            });
        } catch (err) {
            setError(err.response?.data?.detail || 'خطا در غیرفعال‌سازی احراز هویت دو مرحله‌ای');
        } finally {
            setSaving(false);
        }
    };

    const handle2FAClose = () => {
        setShow2FADialog(false);
        setTwoFACode('');
        setError(null);
    };

    if (loading) {
        return (
            <Box sx={{ p: 3 }}>
                <LinearProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box sx={{ p: 3 }}>
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
                <Button variant="outlined" onClick={fetchUserSettings}>
                    تلاش مجدد
                </Button>
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

                            <Box sx={{ mb: 2 }}>
                                <Typography variant="subtitle1" sx={{ mb: 1 }}>
                                    احراز هویت دو مرحله‌ای
                                </Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                    برای امنیت بیشتر، کد تأیید به ایمیل شما ارسال می‌شود
                                </Typography>

                                {settings.twoFactorEnabled ? (
                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                        <Chip
                                            label="فعال"
                                            color="success"
                                            size="small"
                                        />
                                        <Button
                                            variant="outlined"
                                            color="error"
                                            size="small"
                                            onClick={handleDisable2FA}
                                            disabled={saving}
                                        >
                                            غیرفعال‌سازی
                                        </Button>
                                    </Box>
                                ) : (
                                    <Button
                                        variant="outlined"
                                        color="primary"
                                        size="small"
                                        onClick={handleEnable2FA}
                                        disabled={twoFALoading}
                                    >
                                        {twoFALoading ? 'در حال ارسال...' : 'فعال‌سازی'}
                                    </Button>
                                )}
                            </Box>

                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleChangePassword}
                                disabled={!settings.currentPassword || !settings.newPassword || !settings.confirmPassword}
                                fullWidth
                            >
                                تغییر رمز عبور
                            </Button>
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

            {/* Snackbar */}
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

            {/* Dialog برای 2FA */}
            <Dialog open={show2FADialog} onClose={handle2FAClose} maxWidth="sm" fullWidth>
                <DialogTitle>
                    احراز هویت دو مرحله‌ای
                </DialogTitle>
                <DialogContent>
                    <Typography variant="body1" sx={{ mb: 2 }}>
                        کد احراز هویت به ایمیل {twoFAEmail} ارسال شد. لطفاً کد را وارد کنید:
                    </Typography>

                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    <TextField
                        fullWidth
                        label="کد احراز هویت"
                        value={twoFACode}
                        onChange={(e) => setTwoFACode(e.target.value)}
                        placeholder="000000"
                        inputProps={{ maxLength: 6 }}
                        dir="rtl"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={handle2FAClose} disabled={twoFALoading}>
                        انصراف
                    </Button>
                    <Button
                        onClick={handleVerify2FA}
                        variant="contained"
                        disabled={twoFALoading || !twoFACode.trim()}
                    >
                        {twoFALoading ? 'در حال تأیید...' : 'تأیید'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UserSettings;
