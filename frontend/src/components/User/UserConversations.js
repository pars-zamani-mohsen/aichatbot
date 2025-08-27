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
  Badge,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Visibility,
  Delete,
  Chat,
  Language,
  Person,
  CalendarToday,
  FilterList,
  Search,
  Download
} from '@mui/icons-material';
import { chats } from '../../services/api';

const UserConversations = () => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(0);

  useEffect(() => {
    fetchConversations();
  }, [page, filter]);

  const fetchConversations = async (search = null, statusFilter = null, pageNum = null) => {
    try {
      setLoading(true);
      setError(null);

      const currentSearch = search !== null ? search : searchTerm;
      const currentStatus = statusFilter !== null ? statusFilter : (filter === 'all' ? null : filter);
      const currentPage = pageNum !== null ? pageNum : page;

      const response = await chats.getUserConversations(currentPage, 20, currentStatus, currentSearch || null);

      setConversations(response.conversations);
      setTotal(response.total);
      setTotalPages(response.total_pages);
    } catch (err) {
      setError('خطا در دریافت گفتگوها');
      console.error('Error fetching conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewConversation = async (conversation) => {
    try {
      const detail = await chats.getUserConversationDetail(conversation.id);
      setSelectedConversation(detail);
      setOpenDialog(true);
    } catch (err) {
      setSnackbar({
        open: true,
        message: 'خطا در دریافت جزئیات گفتگو',
        severity: 'error'
      });
    }
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setSelectedConversation(null);
  };

  const handleDeleteConversation = async (conversationId) => {
    try {
      await chats.deleteUserConversation(conversationId);
      setConversations(conversations.filter(conv => conv.id !== conversationId));
      setSnackbar({
        open: true,
        message: 'گفتگو با موفقیت حذف شد',
        severity: 'success'
      });
    } catch (err) {
      setSnackbar({
        open: true,
        message: 'خطا در حذف گفتگو',
        severity: 'error'
      });
    }
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

  const handleSearchChange = (e) => {
    setSearchTerm(e.target.value);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchConversations(searchTerm, filter === 'all' ? null : filter, 1);
  };

  const handleDownload = async () => {
    try {
      setSnackbar({
        open: true,
        message: 'در حال آماده‌سازی فایل...',
        severity: 'info'
      });

      // ایجاد داده‌های CSV
      const csvData = [
        ['شناسه', 'وب‌سایت', 'تعداد پیام', 'وضعیت', 'تاریخ ایجاد', 'آخرین پیام']
      ];

      conversations.forEach(conv => {
        csvData.push([
          conv.id,
          conv.website,
          conv.message_count,
          getStatusText(conv.status),
          formatDate(conv.created_at),
          conv.last_message
        ]);
      });

      // تبدیل به CSV
      const csvContent = csvData.map(row => row.join(',')).join('\n');

      // ایجاد فایل و دانلود
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `conversations_page_${page}_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSnackbar({
        open: true,
        message: 'فایل با موفقیت دانلود شد',
        severity: 'success'
      });
    } catch (err) {
      console.error('Error downloading file:', err);
      setSnackbar({
        open: true,
        message: 'خطا در دانلود فایل',
        severity: 'error'
      });
    }
  };

  const handleDownloadAll = async () => {
    try {
      setSnackbar({
        open: true,
        message: 'در حال دریافت همه گفتگوها...',
        severity: 'info'
      });

      // دریافت همه گفتگوها بدون pagination
      const response = await chats.getUserConversations(1, 1000, filter === 'all' ? null : filter, searchTerm || null);

      if (response.conversations.length === 0) {
        setSnackbar({
          open: true,
          message: 'هیچ گفتگویی برای دانلود وجود ندارد',
          severity: 'warning'
        });
        return;
      }

      // ایجاد داده‌های CSV
      const csvData = [
        ['شناسه', 'وب‌سایت', 'تعداد پیام', 'وضعیت', 'تاریخ ایجاد', 'آخرین پیام']
      ];

      response.conversations.forEach(conv => {
        csvData.push([
          conv.id,
          conv.website,
          conv.message_count,
          getStatusText(conv.status),
          formatDate(conv.created_at),
          conv.last_message
        ]);
      });

      // تبدیل به CSV
      const csvContent = csvData.map(row => row.join(',')).join('\n');

      // ایجاد فایل و دانلود
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', `all_conversations_${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      setSnackbar({
        open: true,
        message: `${response.conversations.length} گفتگو با موفقیت دانلود شد`,
        severity: 'success'
      });
    } catch (err) {
      console.error('Error downloading all conversations:', err);
      setSnackbar({
        open: true,
        message: 'خطا در دانلود همه گفتگوها',
        severity: 'error'
      });
    }
  };

  const handleFilterChange = (e) => {
    setFilter(e.target.value);
    setPage(1); // بازگشت به صفحه اول هنگام تغییر فیلتر
  };

  // تابع برای پاک کردن فیلترها
  const clearFilters = () => {
    setSearchTerm('');
    setFilter('all');
    setPage(1);
    // فوراً جستجو را انجام ده با فیلترهای پاک شده
    fetchConversations('', null, 1);
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
        <Button variant="outlined" onClick={fetchConversations}>
          تلاش مجدد
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 1 }}>
          گفتگوهای من
        </Typography>
        <Typography variant="body1" color="text.secondary">
          مشاهده و مدیریت گفتگوهای خود
        </Typography>
      </Box>

      {/* Stats */}
      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Chip
            label={`کل گفتگوها: ${total}`}
            color="primary"
            variant="outlined"
          />
          <Chip
            label={`نمایش شده: ${conversations.length}`}
            color="secondary"
            variant="outlined"
          />
          {(searchTerm || filter !== 'all') && (
            <Chip
              label="فیلتر فعال"
              color="warning"
              variant="outlined"
            />
          )}
        </Box>

        {/* Search and Filter */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <Box component="form" onSubmit={handleSearchSubmit} sx={{ display: 'flex', gap: 1 }}>
            <TextField
              size="small"
              placeholder="جستجو در گفتگوها..."
              value={searchTerm}
              onChange={handleSearchChange}
              sx={{ minWidth: 250 }}
              InputProps={{
                startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
            <Button
              type="submit"
              variant="contained"
              size="small"
              disabled={!searchTerm.trim()}
            >
              جستجو
            </Button>
            {searchTerm && (
              <Button
                type="button"
                variant="outlined"
                size="small"
                onClick={() => {
                  setSearchTerm('');
                  setPage(1);
                  // فوراً جستجو را انجام ده با جستجوی خالی
                  fetchConversations('', filter === 'all' ? null : filter, 1);
                }}
              >
                پاک کردن
              </Button>
            )}
          </Box>
          <FilterList sx={{ color: 'text.secondary' }} />
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>وضعیت</InputLabel>
            <Select
              value={filter}
              label="وضعیت"
              onChange={handleFilterChange}
            >
              <MenuItem value="all">همه گفتگوها</MenuItem>
              <MenuItem value="active">فعال</MenuItem>
              <MenuItem value="completed">تکمیل شده</MenuItem>
            </Select>
          </FormControl>

          {/* نمایش فیلترهای فعال */}
          {(searchTerm || filter !== 'all') && (
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              {searchTerm && (
                <Chip
                  label={`جستجو: ${searchTerm}`}
                  size="small"
                  onDelete={() => setSearchTerm('')}
                  color="primary"
                  variant="outlined"
                />
              )}
              {filter !== 'all' && (
                <Chip
                  label={`وضعیت: ${filter === 'active' ? 'فعال' : 'تکمیل شده'}`}
                  size="small"
                  onDelete={() => setFilter('all')}
                  color="secondary"
                  variant="outlined"
                />
              )}
              <Button
                size="small"
                variant="text"
                onClick={clearFilters}
                sx={{ fontSize: '0.75rem' }}
              >
                پاک کردن همه
              </Button>
            </Box>
          )}

          <Button
            variant="outlined"
            startIcon={<Download />}
            size="small"
            onClick={handleDownload}
            disabled={conversations.length === 0}
          >
            دانلود صفحه فعلی
          </Button>
          <Button
            variant="outlined"
            startIcon={<Download />}
            size="small"
            onClick={handleDownloadAll}
          >
            دانلود همه
          </Button>
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
                  <TableCell>آخرین پیام</TableCell>
                  <TableCell>تعداد پیام</TableCell>
                  <TableCell>وضعیت</TableCell>
                  <TableCell>تاریخ</TableCell>
                  <TableCell>عملیات</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {conversations.length > 0 ? (
                  conversations.map((conversation) => (
                    <TableRow key={conversation.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Language sx={{ fontSize: 16, color: 'text.secondary' }} />
                          {conversation.website}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {conversation.last_message}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Badge badgeContent={conversation.message_count} color="primary">
                          <Chat sx={{ fontSize: 20 }} />
                        </Badge>
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
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center" sx={{ py: 4 }}>
                      <Box sx={{ textAlign: 'center' }}>
                        <Chat sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" sx={{ mb: 1 }}>
                          {searchTerm || filter !== 'all' ? 'نتیجه‌ای یافت نشد' : 'هیچ گفتگویی یافت نشد'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {searchTerm || filter !== 'all'
                            ? 'فیلترهای خود را تغییر دهید یا جستجوی خود را اصلاح کنید'
                            : 'هنوز هیچ گفتگویی در سیستم ثبت نشده است'
                          }
                        </Typography>
                        {(searchTerm || filter !== 'all') && (
                          <Button variant="outlined" onClick={clearFilters}>
                            پاک کردن فیلترها
                          </Button>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2, gap: 1 }}>
              <Button
                variant="outlined"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                قبلی
              </Button>
              <Typography sx={{ display: 'flex', alignItems: 'center', px: 2 }}>
                صفحه {page} از {totalPages}
              </Typography>
              <Button
                variant="outlined"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                بعدی
              </Button>
            </Box>
          )}
        </CardContent>
      </Card>

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

      {/* Conversation Detail Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          جزئیات گفتگو
          {selectedConversation && (
            <Typography variant="body2" color="text.secondary">
              {selectedConversation.website}
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
                  <Box>
                    <Typography variant="body2" color="text.secondary">تاریخ:</Typography>
                    <Typography variant="body1">{formatDate(selectedConversation.created_at)}</Typography>
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
                        label={message.role === 'user' ? 'شما' : 'چت‌بات'}
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

export default UserConversations;
