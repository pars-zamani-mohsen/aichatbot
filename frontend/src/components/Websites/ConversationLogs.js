import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Button,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Download as DownloadIcon,
  Visibility as ViewIcon,
  FilterList as FilterIcon
} from '@mui/icons-material';
import api from '../../services/api';

const ConversationLogs = ({ website }) => {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [total, setTotal] = useState(0);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [exportLoading, setExportLoading] = useState(false);
  const [filterFormat, setFilterFormat] = useState('csv');
  const [filterStartDate, setFilterStartDate] = useState('');
  const [filterEndDate, setFilterEndDate] = useState('');

  useEffect(() => {
    if (website) {
      fetchConversations();
    }
  }, [website, page, rowsPerPage]);

  const fetchConversations = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/chats/websites/${website.id}/conversations`, {
        params: {
          page: page + 1,
          limit: rowsPerPage
        }
      });
      
      setConversations(response.data.conversations);
      setTotal(response.data.total);
    } catch (err) {
      setError('خطا در دریافت مکالمات');
      console.error('Fetch conversations error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setExportLoading(true);
      const params = new URLSearchParams({
        format: filterFormat
      });
      
      if (filterStartDate) params.append('start_date', filterStartDate);
      if (filterEndDate) params.append('end_date', filterEndDate);
      
      const response = await api.get(`/api/chats/websites/${website.id}/export?${params}`, {
        responseType: 'blob'
      });
      
      // ایجاد لینک دانلود
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `conversations_${website.domain}_${new Date().toISOString().split('T')[0]}.${filterFormat}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
    } catch (err) {
      setError('خطا در export مکالمات');
      console.error('Export error:', err);
    } finally {
      setExportLoading(false);
    }
  };

  const handleViewConversation = async (conversation) => {
    try {
      const response = await api.get(`/api/chats/${conversation.chat_id}/messages`);
      setSelectedConversation({
        ...conversation,
        messages: response.data
      });
      setViewDialogOpen(true);
    } catch (err) {
      setError('خطا در دریافت پیام‌های مکالمه');
      console.error('View conversation error:', err);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('fa-IR');
  };

  if (!website) {
    return <Typography>لطفاً یک وب‌سایت انتخاب کنید</Typography>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">
          لاگ مکالمات - {website.name || website.domain}
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>فرمت</InputLabel>
            <Select
              value={filterFormat}
              onChange={(e) => setFilterFormat(e.target.value)}
            >
              <MenuItem value="csv">CSV</MenuItem>
              <MenuItem value="json">JSON</MenuItem>
            </Select>
          </FormControl>
          <TextField
            size="small"
            label="از تاریخ"
            type="date"
            value={filterStartDate}
            onChange={(e) => setFilterStartDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <TextField
            size="small"
            label="تا تاریخ"
            type="date"
            value={filterEndDate}
            onChange={(e) => setFilterEndDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <Button
            variant="contained"
            startIcon={exportLoading ? <CircularProgress size={20} /> : <DownloadIcon />}
            onClick={handleExport}
            disabled={exportLoading}
          >
            Export
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>شناسه جلسه</TableCell>
                <TableCell>تاریخ ایجاد</TableCell>
                <TableCell>تعداد پیام‌ها</TableCell>
                <TableCell>آخرین فعالیت</TableCell>
                <TableCell>عملیات</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : conversations.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    مکالمه‌ای یافت نشد
                  </TableCell>
                </TableRow>
              ) : (
                conversations.map((conversation) => (
                  <TableRow key={conversation.chat_id}>
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {conversation.session_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {formatDate(conversation.created_at)}
                    </TableCell>
                    <TableCell>
                      <Chip label={conversation.message_count} size="small" />
                    </TableCell>
                    <TableCell>
                      {formatDate(conversation.last_activity)}
                    </TableCell>
                    <TableCell>
                      <Tooltip title="مشاهده مکالمه">
                        <IconButton
                          size="small"
                          onClick={() => handleViewConversation(conversation)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="ردیف در صفحه:"
          labelDisplayedRows={({ from, to, count }) => `${from}-${to} از ${count}`}
        />
      </Paper>

      {/* Dialog مشاهده مکالمه */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          مشاهده مکالمه - {selectedConversation?.session_id}
        </DialogTitle>
        <DialogContent>
          {selectedConversation?.messages?.map((message, index) => (
            <Box key={index} sx={{ mb: 2, p: 2, bgcolor: message.role === 'user' ? 'grey.100' : 'primary.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" color="primary" gutterBottom>
                {message.role === 'user' ? 'کاربر' : 'دستیار'}
              </Typography>
              <Typography variant="body2">
                {message.content}
              </Typography>
              {message.sources && message.sources.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    منابع: {message.sources.join(', ')}
                  </Typography>
                </Box>
              )}
              <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                {formatDate(message.created_at)}
              </Typography>
            </Box>
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>بستن</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ConversationLogs;
