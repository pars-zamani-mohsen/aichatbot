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
    Tooltip,
    Pagination,
    InputAdornment
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
    AdminPanelSettings,
    Search,
    Refresh
} from '@mui/icons-material';
import { dashboard } from '../../services/api';

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
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState('all');
    const [statusFilter, setStatusFilter] = useState('all');

    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError('');
            
            const response = await dashboard.getAdminUsers(
                page, 
                20, 
                searchTerm || null, 
                roleFilter !== 'all' ? roleFilter : null,
                statusFilter !== 'all' ? statusFilter : null
            );
            
            setUsers(response.users);
            setTotalPages(response.total_pages);
        } catch (err) {
            console.error('Error fetching users:', err);
            setError('خطا در دریافت لیست کاربران');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, [page, searchTerm, roleFilter, statusFilter]);

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
        setFormData({
            email: '',
            role: 'user',
            is_active: true,
            is_verified: true
        });
        setError('');
    };

    const handleSubmit = async () => {
        try {
            setError('');
            
            if (editingUser) {
                // به‌روزرسانی کاربر
                await dashboard.updateAdminUser(editingUser.id, {
                    role: formData.role,
                    is_active: formData.is_active,
                    is_verified: formData.is_verified
                });
                setSuccess('کاربر با موفقیت به‌روزرسانی شد');
            }
            
            handleCloseDialog();
            fetchUsers();
        } catch (err) {
            console.error('Error updating user:', err);
            setError('خطا در به‌روزرسانی کاربر');
        }
    };

    const handleDeleteUser = async (userId) => {
        if (window.confirm('آیا از حذف این کاربر اطمینان دارید؟')) {
            try {
                await dashboard.deleteAdminUser(userId);
                setSuccess('کاربر با موفقیت حذف شد');
                fetchUsers();
            } catch (err) {
                console.error('Error deleting user:', err);
                setError('خطا در حذف کاربر');
            }
        }
    };

    const handleSearch = (event) => {
        setSearchTerm(event.target.value);
        setPage(1);
    };

    const handleRoleFilterChange = (event) => {
        setRoleFilter(event.target.value);
        setPage(1);
    };

    const handleStatusFilterChange = (event) => {
        setStatusFilter(event.target.value);
        setPage(1);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('fa-IR');
    };

    const getRoleColor = (role) => {
        return role === 'admin' ? 'error' : 'default';
    };

    const getStatusColor = (isActive) => {
        return isActive ? 'success' : 'error';
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                    مدیریت کاربران
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    مدیریت و نظارت بر کاربران سیستم
                </Typography>
            </Box>

            {/* Alerts */}
            {error && (
                <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
                    {error}
                </Alert>
            )}
            {success && (
                <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
                    {success}
                </Alert>
            )}

            {/* Filters and Actions */}
            <Card sx={{ mb: 3 }}>
                <CardContent>
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
                        <TextField
                            placeholder="جستجو در کاربران..."
                            value={searchTerm}
                            onChange={handleSearch}
                            size="small"
                            sx={{ minWidth: 250 }}
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <Search />
                                    </InputAdornment>
                                ),
                            }}
                        />
                        
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>نقش</InputLabel>
                            <Select
                                value={roleFilter}
                                onChange={handleRoleFilterChange}
                                label="نقش"
                            >
                                <MenuItem value="all">همه</MenuItem>
                                <MenuItem value="admin">مدیر</MenuItem>
                                <MenuItem value="user">کاربر</MenuItem>
                            </Select>
                        </FormControl>
                        
                        <FormControl size="small" sx={{ minWidth: 120 }}>
                            <InputLabel>وضعیت</InputLabel>
                            <Select
                                value={statusFilter}
                                onChange={handleStatusFilterChange}
                                label="وضعیت"
                            >
                                <MenuItem value="all">همه</MenuItem>
                                <MenuItem value="active">فعال</MenuItem>
                                <MenuItem value="inactive">غیرفعال</MenuItem>
                            </Select>
                        </FormControl>
                        
                        <Button
                            variant="outlined"
                            startIcon={<Refresh />}
                            onClick={fetchUsers}
                            disabled={loading}
                        >
                            به‌روزرسانی
                        </Button>
                    </Box>
                </CardContent>
            </Card>

            {/* Users Table */}
            <Card>
                <CardContent>
                    {loading ? (
                        <LinearProgress />
                    ) : (
                        <>
                            <TableContainer>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>کاربر</TableCell>
                                            <TableCell>ایمیل</TableCell>
                                            <TableCell>نقش</TableCell>
                                            <TableCell>وضعیت</TableCell>
                                            <TableCell>تاریخ ثبت‌نام</TableCell>
                                            <TableCell>آخرین ورود</TableCell>
                                            <TableCell>وب‌سایت‌ها</TableCell>
                                            <TableCell>گفتگوها</TableCell>
                                            <TableCell>عملیات</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {users.map((user) => (
                                            <TableRow key={user.id}>
                                                <TableCell>
                                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                        <Avatar sx={{ mr: 2, bgcolor: user.role === 'admin' ? 'error.main' : 'primary.main' }}>
                                                            {user.role === 'admin' ? <AdminPanelSettings /> : <Person />}
                                                        </Avatar>
                                                        <Box>
                                                            <Typography variant="body2" fontWeight="bold">
                                                                {user.email.split('@')[0]}
                                                            </Typography>
                                                        </Box>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>{user.email}</TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={user.role === 'admin' ? 'مدیر' : 'کاربر'}
                                                        color={getRoleColor(user.role)}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={user.is_active ? 'فعال' : 'غیرفعال'}
                                                        color={getStatusColor(user.is_active)}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>{formatDate(user.created_at)}</TableCell>
                                                <TableCell>{formatDate(user.last_login)}</TableCell>
                                                <TableCell>
                                                    <Chip label={user.websites_count} size="small" />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip label={user.conversations_count} size="small" />
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
                            
                            {/* Pagination */}
                            {totalPages > 1 && (
                                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                                    <Pagination
                                        count={totalPages}
                                        page={page}
                                        onChange={(event, value) => setPage(value)}
                                        color="primary"
                                    />
                                </Box>
                            )}
                        </>
                    )}
                </CardContent>
            </Card>

            {/* Edit Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {editingUser ? 'ویرایش کاربر' : 'افزودن کاربر جدید'}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ pt: 1 }}>
                        <TextField
                            fullWidth
                            label="ایمیل"
                            value={formData.email}
                            disabled={!!editingUser}
                            sx={{ mb: 2 }}
                        />
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>نقش</InputLabel>
                            <Select
                                value={formData.role}
                                onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                label="نقش"
                            >
                                <MenuItem value="user">کاربر</MenuItem>
                                <MenuItem value="admin">مدیر</MenuItem>
                            </Select>
                        </FormControl>
                        <FormControl fullWidth sx={{ mb: 2 }}>
                            <InputLabel>وضعیت</InputLabel>
                            <Select
                                value={formData.is_active}
                                onChange={(e) => setFormData({ ...formData, is_active: e.target.value })}
                                label="وضعیت"
                            >
                                <MenuItem value={true}>فعال</MenuItem>
                                <MenuItem value={false}>غیرفعال</MenuItem>
                            </Select>
                        </FormControl>
                        <FormControl fullWidth>
                            <InputLabel>تأیید شده</InputLabel>
                            <Select
                                value={formData.is_verified}
                                onChange={(e) => setFormData({ ...formData, is_verified: e.target.value })}
                                label="تأیید شده"
                            >
                                <MenuItem value={true}>بله</MenuItem>
                                <MenuItem value={false}>خیر</MenuItem>
                            </Select>
                        </FormControl>
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>انصراف</Button>
                    <Button onClick={handleSubmit} variant="contained">
                        {editingUser ? 'به‌روزرسانی' : 'افزودن'}
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default UserManagement;
