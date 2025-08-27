import React, { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    Button,
    IconButton,
    Chip,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Alert,
    LinearProgress,
    Avatar,
    Tooltip
} from '@mui/material';
import {
    Add,
    Edit,
    Delete,
    Block,
    CheckCircle,
    Person,
    Email,
    CalendarToday,
    AdminPanelSettings
} from '@mui/icons-material';

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [openDialog, setOpenDialog] = useState(false);
    const [editingUser, setEditingUser] = useState(null);
    const [formData, setFormData] = useState({
        email: '',
        role: 'user',
        is_active: true,
        is_verified: true
    });

    // داده‌های نمونه
    const sampleUsers = [
        {
            id: 1,
            email: 'admin@example.com',
            role: 'admin',
            is_active: true,
            is_verified: true,
            created_at: '2024-01-15T10:30:00Z'
        },
        {
            id: 2,
            email: 'user1@example.com',
            role: 'user',
            is_active: true,
            is_verified: true,
            created_at: '2024-01-20T14:20:00Z'
        },
        {
            id: 3,
            email: 'user2@example.com',
            role: 'user',
            is_active: false,
            is_verified: false,
            created_at: '2024-01-25T09:15:00Z'
        }
    ];

    useEffect(() => {
        // شبیه‌سازی دریافت داده‌ها
        setTimeout(() => {
            setUsers(sampleUsers);
            setLoading(false);
        }, 1000);
    }, []);

    const handleOpenDialog = (user = null) => {
        if (user) {
            setEditingUser(user);
            setFormData({
                email: user.email,
                role: user.role,
                is_active: user.is_active,
                is_verified: user.is_verified
            });
        } else {
            setEditingUser(null);
            setFormData({
                email: '',
                role: 'user',
                is_active: true,
                is_verified: true
            });
        }
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setEditingUser(null);
    };

    const handleSubmit = () => {
        if (editingUser) {
            // ویرایش کاربر
            setUsers(users.map(user =>
                user.id === editingUser.id
                    ? { ...user, ...formData }
                    : user
            ));
        } else {
            // افزودن کاربر جدید
            const newUser = {
                id: Date.now(),
                ...formData,
                created_at: new Date().toISOString()
            };
            setUsers([...users, newUser]);
        }
        handleCloseDialog();
    };

    const handleDeleteUser = (userId) => {
        setUsers(users.filter(user => user.id !== userId));
    };

    const handleToggleStatus = (userId) => {
        setUsers(users.map(user =>
            user.id === userId
                ? { ...user, is_active: !user.is_active }
                : user
        ));
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('fa-IR');
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
                        مدیریت کاربران
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        مدیریت حساب‌های کاربری و دسترسی‌ها
                    </Typography>
                </Box>
                <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => handleOpenDialog()}
                >
                    افزودن کاربر
                </Button>
            </Box>

            {/* Stats */}
            <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', gap: 2 }}>
                    <Chip
                        label={`کل کاربران: ${users.length}`}
                        color="primary"
                        variant="outlined"
                    />
                    <Chip
                        label={`کاربران فعال: ${users.filter(u => u.is_active).length}`}
                        color="success"
                        variant="outlined"
                    />
                    <Chip
                        label={`مدیران: ${users.filter(u => u.role === 'admin').length}`}
                        color="warning"
                        variant="outlined"
                    />
                </Box>
            </Box>

            {/* Users Table */}
            <Card>
                <CardContent>
                    <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>کاربر</TableCell>
                                    <TableCell>ایمیل</TableCell>
                                    <TableCell>نقش</TableCell>
                                    <TableCell>وضعیت</TableCell>
                                    <TableCell>تاریخ عضویت</TableCell>
                                    <TableCell>عملیات</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {users.map((user) => (
                                    <TableRow key={user.id}>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Avatar sx={{ width: 32, height: 32 }}>
                                                    {user.role === 'admin' ? <AdminPanelSettings /> : <Person />}
                                                </Avatar>
                                                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                                    {user.email.split('@')[0]}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Email sx={{ fontSize: 16, color: 'text.secondary' }} />
                                                {user.email}
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={user.role === 'admin' ? 'مدیر' : 'کاربر'}
                                                size="small"
                                                color={user.role === 'admin' ? 'warning' : 'default'}
                                                icon={user.role === 'admin' ? <AdminPanelSettings /> : <Person />}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', gap: 1 }}>
                                                <Chip
                                                    label={user.is_active ? 'فعال' : 'غیرفعال'}
                                                    size="small"
                                                    color={user.is_active ? 'success' : 'error'}
                                                    icon={user.is_active ? <CheckCircle /> : <Block />}
                                                />
                                                {!user.is_verified && (
                                                    <Chip
                                                        label="تأیید نشده"
                                                        size="small"
                                                        color="warning"
                                                        variant="outlined"
                                                    />
                                                )}
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <CalendarToday sx={{ fontSize: 16, color: 'text.secondary' }} />
                                                {formatDate(user.created_at)}
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', gap: 1 }}>
                                                <Tooltip title="ویرایش">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleOpenDialog(user)}
                                                    >
                                                        <Edit />
                                                    </IconButton>
                                                </Tooltip>
                                                <Tooltip title={user.is_active ? 'غیرفعال کردن' : 'فعال کردن'}>
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleToggleStatus(user.id)}
                                                        color={user.is_active ? 'warning' : 'success'}
                                                    >
                                                        {user.is_active ? <Block /> : <CheckCircle />}
                                                    </IconButton>
                                                </Tooltip>
                                                <Tooltip title="حذف">
                                                    <IconButton
                                                        size="small"
                                                        color="error"
                                                        onClick={() => handleDeleteUser(user.id)}
                                                    >
                                                        <Delete />
                                                    </IconButton>
                                                </Tooltip>
                                            </Box>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                </CardContent>
            </Card>

            {/* Add/Edit User Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {editingUser ? 'ویرایش کاربر' : 'افزودن کاربر جدید'}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 2 }}>
                        <TextField
                            fullWidth
                            label="ایمیل"
                            type="email"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            sx={{ mb: 2 }}
                        />
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>نقش</InputLabel>
                            <Select
                                value={formData.role}
                                label="نقش"
                                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                            >
                                <MenuItem value="user">کاربر</MenuItem>
                                <MenuItem value="admin">مدیر</MenuItem>
                            </Select>
                        </FormControl>
                        <Box sx={{ display: 'flex', gap: 2 }}>
                            <FormControl fullWidth>
                                <InputLabel>وضعیت فعال</InputLabel>
                                <Select
                                    value={formData.is_active}
                                    label="وضعیت فعال"
                                    onChange={(e) => setFormData({ ...formData, is_active: e.target.value })}
                                >
                                    <MenuItem value={true}>فعال</MenuItem>
                                    <MenuItem value={false}>غیرفعال</MenuItem>
                                </Select>
                            </FormControl>
                            <FormControl fullWidth>
                                <InputLabel>وضعیت تأیید</InputLabel>
                                <Select
                                    value={formData.is_verified}
                                    label="وضعیت تأیید"
                                    onChange={(e) => setFormData({ ...formData, is_verified: e.target.value })}
                                >
                                    <MenuItem value={true}>تأیید شده</MenuItem>
                                    <MenuItem value={false}>تأیید نشده</MenuItem>
                                </Select>
                            </FormControl>
                        </Box>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>انصراف</Button>
                    <Button onClick={handleSubmit} variant="contained">
                        {editingUser ? 'ویرایش' : 'افزودن'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UserManagement;
