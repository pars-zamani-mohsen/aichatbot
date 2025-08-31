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
    Alert,
    LinearProgress,
    Avatar,
    Tooltip,
    Pagination,
    InputAdornment,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField
} from '@mui/material';
import {
    Delete,
    Visibility,
    Chat,
    Language,
    Person,
    CalendarToday,
    Search,
    Refresh,
    Message
} from '@mui/icons-material';
import { dashboard } from '../../services/api';

const ConversationManagement = () => {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [openDialog, setOpenDialog] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [searchTerm, setSearchTerm] = useState('');
    const [websiteFilter, setWebsiteFilter] = useState('all');
    const [userFilter, setUserFilter] = useState('all');

    const fetchConversations = async () => {
        try {
            setLoading(true);
            setError('');
            
            const response = await dashboard.getAdminConversations(
                page, 
                20, 
                searchTerm || null, 
                websiteFilter !== 'all' ? parseInt(websiteFilter) : null,
                userFilter !== 'all' ? parseInt(userFilter) : null
            );
            
            setConversations(response.conversations || []);
            setTotalPages(response.total_pages || 1);
        } catch (err) {
            console.error('Error fetching conversations:', err);
            setError('خطا در دریافت لیست گفتگوها');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchConversations();
    }, [page, searchTerm, websiteFilter, userFilter]);

    const handleViewConversation = async (conversationId) => {
        try {
            const response = await dashboard.getAdminConversationMessages(conversationId);
            setSelectedConversation(response);
            setOpenDialog(true);
        } catch (err) {
            console.error('Error fetching conversation messages:', err);
            setError('خطا در دریافت پیام‌های گفتگو');
        }
    };

    const handleDeleteConversation = async (conversationId) => {
        if (window.confirm('آیا از حذف این گفتگو اطمینان دارید؟')) {
            try {
                await dashboard.deleteAdminConversation(conversationId);
                setSuccess('گفتگو با موفقیت حذف شد');
                fetchConversations();
            } catch (err) {
                console.error('Error deleting conversation:', err);
                setError('خطا در حذف گفتگو');
            }
        }
    };

    const handleSearch = (event) => {
        setSearchTerm(event.target.value);
        setPage(1);
    };

    const handleWebsiteFilterChange = (event) => {
        setWebsiteFilter(event.target.value);
        setPage(1);
    };

    const handleUserFilterChange = (event) => {
        setUserFilter(event.target.value);
        setPage(1);
    };

    const formatDate = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleDateString('fa-IR');
    };

    const formatTime = (dateString) => {
        if (!dateString) return '-';
        return new Date(dateString).toLocaleTimeString('fa-IR');
    };

    const getStatusColor = (messageCount) => {
        return messageCount > 0 ? 'success' : 'warning';
    };

    return (
        <Box sx={{ p: 3 }}>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                    مدیریت گفتگوها
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    نظارت و مدیریت بر گفتگوهای کاربران
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
                            placeholder="جستجو در گفتگوها..."
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
                        
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                            <InputLabel>وب‌سایت</InputLabel>
                            <Select
                                value={websiteFilter}
                                onChange={handleWebsiteFilterChange}
                                label="وب‌سایت"
                            >
                                <MenuItem value="all">همه وب‌سایت‌ها</MenuItem>
                                {/* اینجا می‌توان لیست وب‌سایت‌ها را اضافه کرد */}
                            </Select>
                        </FormControl>
                        
                        <FormControl size="small" sx={{ minWidth: 150 }}>
                            <InputLabel>کاربر</InputLabel>
                            <Select
                                value={userFilter}
                                onChange={handleUserFilterChange}
                                label="کاربر"
                            >
                                <MenuItem value="all">همه کاربران</MenuItem>
                                {/* اینجا می‌توان لیست کاربران را اضافه کرد */}
                            </Select>
                        </FormControl>
                        
                        <Button
                            variant="outlined"
                            startIcon={<Refresh />}
                            onClick={fetchConversations}
                            disabled={loading}
                        >
                            به‌روزرسانی
                        </Button>
                    </Box>
                </CardContent>
            </Card>

            {/* Conversations Table */}
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
                                            <TableCell>شناسه</TableCell>
                                            <TableCell>وب‌سایت</TableCell>
                                            <TableCell>کاربر</TableCell>
                                            <TableCell>وضعیت</TableCell>
                                            <TableCell>تعداد پیام</TableCell>
                                            <TableCell>تاریخ شروع</TableCell>
                                            <TableCell>آخرین فعالیت</TableCell>
                                            <TableCell>عملیات</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {(conversations || []).map((conversation) => (
                                            <TableRow key={conversation.id}>
                                                <TableCell>
                                                    <Typography variant="body2" fontWeight="bold">
                                                        #{conversation.id}
                                                    </Typography>
                                                </TableCell>
                                                <TableCell>
                                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                        <Avatar sx={{ mr: 2, bgcolor: 'primary.main' }}>
                                                            <Language />
                                                        </Avatar>
                                                        <Box>
                                                            <Typography variant="body2" fontWeight="bold">
                                                                {conversation.website_name}
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary">
                                                                ID: {conversation.website_id}
                                                            </Typography>
                                                        </Box>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                                        <Avatar sx={{ mr: 2, bgcolor: 'secondary.main' }}>
                                                            <Person />
                                                        </Avatar>
                                                        <Box>
                                                            <Typography variant="body2" fontWeight="bold">
                                                                {conversation.owner_email}
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary">
                                                                ID: {conversation.owner_id}
                                                            </Typography>
                                                        </Box>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Chip
                                                        label={conversation.messages_count > 0 ? 'فعال' : 'در انتظار'}
                                                        color={getStatusColor(conversation.messages_count)}
                                                        size="small"
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Chip 
                                                        label={conversation.messages_count} 
                                                        size="small" 
                                                        icon={<Message />}
                                                    />
                                                </TableCell>
                                                <TableCell>
                                                    <Box>
                                                        <Typography variant="body2">
                                                            {formatDate(conversation.created_at)}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {formatTime(conversation.created_at)}
                                                        </Typography>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Box>
                                                        <Typography variant="body2">
                                                            {formatDate(conversation.updated_at)}
                                                        </Typography>
                                                        <Typography variant="caption" color="text.secondary">
                                                            {formatTime(conversation.updated_at)}
                                                        </Typography>
                                                    </Box>
                                                </TableCell>
                                                <TableCell>
                                                    <Box sx={{ display: 'flex', gap: 1 }}>
                                                        <Tooltip title="مشاهده گفتگو">
                                                            <IconButton
                                                                size="small"
                                                                onClick={() => handleViewConversation(conversation.id)}
                                                            >
                                                                <Visibility />
                                                            </IconButton>
                                                        </Tooltip>
                                                        <Tooltip title="حذف گفتگو">
                                                            <IconButton
                                                                size="small"
                                                                color="error"
                                                                onClick={() => handleDeleteConversation(conversation.id)}
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

            {/* Conversation Details Dialog */}
            <Dialog 
                open={openDialog} 
                onClose={() => setOpenDialog(false)} 
                maxWidth="md" 
                fullWidth
            >
                <DialogTitle>
                    جزئیات گفتگو
                    {selectedConversation && (
                        <Typography variant="body2" color="text.secondary">
                            وب‌سایت: {selectedConversation.conversation.website_name} | 
                            کاربر: {selectedConversation.conversation.owner_email}
                        </Typography>
                    )}
                </DialogTitle>
                <DialogContent>
                    {selectedConversation && (
                        <Box sx={{ mt: 2 }}>
                            <Typography variant="h6" sx={{ mb: 2 }}>
                                پیام‌ها ({selectedConversation.messages.length})
                            </Typography>
                            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                                {selectedConversation.messages.map((message, index) => (
                                    <Box
                                        key={message.id}
                                        sx={{
                                            mb: 2,
                                            p: 2,
                                            borderRadius: 2,
                                            bgcolor: message.role === 'user' ? 'grey.100' : 'primary.50',
                                            border: '1px solid',
                                            borderColor: message.role === 'user' ? 'grey.300' : 'primary.200'
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                            <Chip
                                                label={message.role === 'user' ? 'کاربر' : 'ربات'}
                                                color={message.role === 'user' ? 'primary' : 'secondary'}
                                                size="small"
                                            />
                                            <Typography variant="caption" color="text.secondary">
                                                {formatDate(message.created_at)} - {formatTime(message.created_at)}
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2">
                                            {message.content}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setOpenDialog(false)}>
                        بستن
                    </Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ConversationManagement;
