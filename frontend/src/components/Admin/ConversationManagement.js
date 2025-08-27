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
    LinearProgress,
    Avatar,
    Tooltip,
    Accordion,
    AccordionSummary,
    AccordionDetails
} from '@mui/material';
import {
    Visibility,
    Delete,
    Chat,
    Language,
    Person,
    CalendarToday,
    ExpandMore,
    Search,
    FilterList
} from '@mui/icons-material';

const ConversationManagement = () => {
    const [conversations, setConversations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [openDialog, setOpenDialog] = useState(false);
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [filter, setFilter] = useState('all');

    // داده‌های نمونه
    const sampleConversations = [
        {
            id: 1,
            website: 'example.com',
            user_email: 'user1@example.com',
            session_id: 'sess_123',
            message_count: 5,
            status: 'active',
            created_at: '2024-01-15T10:30:00Z',
            last_message: 'سلام، سوالی در مورد محصولات شما دارم',
            messages: [
                { role: 'user', content: 'سلام، سوالی در مورد محصولات شما دارم', time: '10:30' },
                { role: 'assistant', content: 'سلام! خوشحالم که به شما کمک کنم. چه سوالی دارید؟', time: '10:31' },
                { role: 'user', content: 'آیا محصولات شما گارانتی دارند؟', time: '10:32' },
                { role: 'assistant', content: 'بله، تمام محصولات ما 2 سال گارانتی دارند.', time: '10:33' },
                { role: 'user', content: 'ممنون از اطلاعات شما', time: '10:34' }
            ]
        },
        {
            id: 2,
            website: 'test.com',
            user_email: 'user2@example.com',
            session_id: 'sess_456',
            message_count: 3,
            status: 'completed',
            created_at: '2024-01-14T15:20:00Z',
            last_message: 'قیمت محصولات چقدر است؟',
            messages: [
                { role: 'user', content: 'قیمت محصولات چقدر است؟', time: '15:20' },
                { role: 'assistant', content: 'قیمت‌ها در صفحه محصولات ذکر شده است.', time: '15:21' },
                { role: 'user', content: 'متوجه شدم، ممنون', time: '15:22' }
            ]
        },
        {
            id: 3,
            website: 'demo.com',
            user_email: 'user3@example.com',
            session_id: 'sess_789',
            message_count: 8,
            status: 'active',
            created_at: '2024-01-13T09:15:00Z',
            last_message: 'آیا امکان ارسال رایگان دارید؟',
            messages: [
                { role: 'user', content: 'آیا امکان ارسال رایگان دارید؟', time: '09:15' },
                { role: 'assistant', content: 'بله، برای خریدهای بالای 500 هزار تومان ارسال رایگان است.', time: '09:16' }
            ]
        }
    ];

    useEffect(() => {
        // شبیه‌سازی دریافت داده‌ها
        setTimeout(() => {
            setConversations(sampleConversations);
            setLoading(false);
        }, 1000);
    }, []);

    const handleViewConversation = (conversation) => {
        setSelectedConversation(conversation);
        setOpenDialog(true);
    };

    const handleCloseDialog = () => {
        setOpenDialog(false);
        setSelectedConversation(null);
    };

    const handleDeleteConversation = (conversationId) => {
        setConversations(conversations.filter(conv => conv.id !== conversationId));
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('fa-IR');
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'active': return 'success';
            case 'completed': return 'info';
            case 'pending': return 'warning';
            default: return 'default';
        }
    };

    const getStatusText = (status) => {
        switch (status) {
            case 'active': return 'فعال';
            case 'completed': return 'تکمیل شده';
            case 'pending': return 'در انتظار';
            default: return 'نامشخص';
        }
    };

    const filteredConversations = conversations.filter(conv => {
        if (filter === 'all') return true;
        return conv.status === filter;
    });

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
            <Box sx={{ mb: 4 }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
                    مدیریت گفتگوها
                </Typography>
                <Typography variant="body1" color="text.secondary">
                    مشاهده و مدیریت تمام گفتگوهای سیستم
                </Typography>
            </Box>

            {/* Stats */}
            <Box sx={{ mb: 3 }}>
                <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                    <Chip
                        label={`کل گفتگوها: ${conversations.length}`}
                        color="primary"
                        variant="outlined"
                    />
                    <Chip
                        label={`گفتگوهای فعال: ${conversations.filter(c => c.status === 'active').length}`}
                        color="success"
                        variant="outlined"
                    />
                    <Chip
                        label={`تکمیل شده: ${conversations.filter(c => c.status === 'completed').length}`}
                        color="info"
                        variant="outlined"
                    />
                </Box>

                {/* Filter */}
                <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                    <FilterList sx={{ color: 'text.secondary' }} />
                    <FormControl size="small" sx={{ minWidth: 120 }}>
                        <InputLabel>فیلتر</InputLabel>
                        <Select
                            value={filter}
                            label="فیلتر"
                            onChange={(e) => setFilter(e.target.value)}
                        >
                            <MenuItem value="all">همه</MenuItem>
                            <MenuItem value="active">فعال</MenuItem>
                            <MenuItem value="completed">تکمیل شده</MenuItem>
                            <MenuItem value="pending">در انتظار</MenuItem>
                        </Select>
                    </FormControl>
                </Box>
            </Box>

            {/* Conversations Table */}
            <Card>
                <CardContent>
                    <TableContainer component={Paper} sx={{ boxShadow: 'none' }}>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>وب‌سایت</TableCell>
                                    <TableCell>کاربر</TableCell>
                                    <TableCell>آخرین پیام</TableCell>
                                    <TableCell>تعداد پیام</TableCell>
                                    <TableCell>وضعیت</TableCell>
                                    <TableCell>تاریخ</TableCell>
                                    <TableCell>عملیات</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {filteredConversations.map((conversation) => (
                                    <TableRow key={conversation.id}>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Language sx={{ fontSize: 16, color: 'text.secondary' }} />
                                                {conversation.website}
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <Avatar sx={{ width: 24, height: 24 }}>
                                                    <Person />
                                                </Avatar>
                                                <Typography variant="body2">
                                                    {conversation.user_email}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                                {conversation.last_message}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={conversation.message_count}
                                                size="small"
                                                color="primary"
                                                variant="outlined"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={getStatusText(conversation.status)}
                                                size="small"
                                                color={getStatusColor(conversation.status)}
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <CalendarToday sx={{ fontSize: 16, color: 'text.secondary' }} />
                                                {formatDate(conversation.created_at)}
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Box sx={{ display: 'flex', gap: 1 }}>
                                                <Tooltip title="مشاهده گفتگو">
                                                    <IconButton
                                                        size="small"
                                                        onClick={() => handleViewConversation(conversation)}
                                                    >
                                                        <Visibility />
                                                    </IconButton>
                                                </Tooltip>
                                                <Tooltip title="حذف">
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
                </CardContent>
            </Card>

            {/* Conversation Detail Dialog */}
            <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
                <DialogTitle>
                    جزئیات گفتگو
                    {selectedConversation && (
                        <Typography variant="body2" color="text.secondary">
                            {selectedConversation.website} - {selectedConversation.user_email}
                        </Typography>
                    )}
                </DialogTitle>
                <DialogContent>
                    {selectedConversation && (
                        <Box sx={{ pt: 2 }}>
                            {/* Conversation Info */}
                            <Box sx={{ mb: 3, p: 2, bgcolor: 'grey.50', borderRadius: 2 }}>
                                <Typography variant="h6" sx={{ mb: 1 }}>
                                    اطلاعات گفتگو
                                </Typography>
                                <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">وب‌سایت:</Typography>
                                        <Typography variant="body1">{selectedConversation.website}</Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">کاربر:</Typography>
                                        <Typography variant="body1">{selectedConversation.user_email}</Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">Session ID:</Typography>
                                        <Typography variant="body1">{selectedConversation.session_id}</Typography>
                                    </Box>
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">وضعیت:</Typography>
                                        <Chip
                                            label={getStatusText(selectedConversation.status)}
                                            size="small"
                                            color={getStatusColor(selectedConversation.status)}
                                        />
                                    </Box>
                                </Box>
                            </Box>

                            {/* Messages */}
                            <Typography variant="h6" sx={{ mb: 2 }}>
                                پیام‌ها ({selectedConversation.messages.length})
                            </Typography>
                            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                                {selectedConversation.messages.map((message, index) => (
                                    <Box
                                        key={index}
                                        sx={{
                                            mb: 2,
                                            p: 2,
                                            bgcolor: message.role === 'user' ? 'primary.50' : 'grey.50',
                                            borderRadius: 2,
                                            border: `1px solid ${message.role === 'user' ? 'primary.200' : 'grey.200'}`
                                        }}
                                    >
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                            <Chip
                                                label={message.role === 'user' ? 'کاربر' : 'چت‌بات'}
                                                size="small"
                                                color={message.role === 'user' ? 'primary' : 'secondary'}
                                            />
                                            <Typography variant="caption" color="text.secondary">
                                                {message.time}
                                            </Typography>
                                        </Box>
                                        <Typography variant="body1">
                                            {message.content}
                                        </Typography>
                                    </Box>
                                ))}
                            </Box>
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleCloseDialog}>بستن</Button>
                </DialogActions>
            </Dialog>
        </Box>
    );
};

export default ConversationManagement;
