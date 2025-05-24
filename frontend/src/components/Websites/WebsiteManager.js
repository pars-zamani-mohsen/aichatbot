import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  Typography,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  CircularProgress,
  Alert,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';

const WebsiteManager = () => {
  const [websites, setWebsites] = useState([]);
  const [open, setOpen] = useState(false);
  const [newUrl, setNewUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchWebsites = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/websites/');
      setWebsites(response.data);
    } catch (err) {
      setError('خطا در دریافت لیست وب‌سایت‌ها');
      console.error(err);
    }
  };

  useEffect(() => {
    fetchWebsites();
  }, []);

  const handleAddWebsite = async () => {
    if (!newUrl.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      await axios.post('http://localhost:8000/api/websites/', {
        url: newUrl
      });
      
      setNewUrl('');
      setOpen(false);
      fetchWebsites();
    } catch (err) {
      setError('خطا در افزودن وب‌سایت');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWebsite = async (id) => {
    try {
      await axios.delete(`http://localhost:8000/api/websites/${id}`);
      fetchWebsites();
    } catch (err) {
      setError('خطا در حذف وب‌سایت');
      console.error(err);
    }
  };

  const handleRetryWebsite = async (id) => {
    try {
      await axios.post(`http://localhost:8000/api/websites/${id}/retry`);
      fetchWebsites();
    } catch (err) {
      setError('خطا در تلاش مجدد برای پردازش وب‌سایت');
      console.error(err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ready':
        return 'success.main';
      case 'processing':
        return 'info.main';
      case 'failed':
        return 'error.main';
      default:
        return 'grey.500';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'ready':
        return 'آماده';
      case 'processing':
        return 'در حال پردازش';
      case 'failed':
        return 'خطا';
      default:
        return status;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h5">مدیریت وب‌سایت‌ها</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpen(true)}
        >
          افزودن وب‌سایت
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 2 }}>
        {websites.map((website) => (
          <Card key={website.id}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                {website.domain}
              </Typography>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {website.url}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography variant="body2">وضعیت:</Typography>
                <Typography
                  variant="body2"
                  sx={{ color: getStatusColor(website.status) }}
                >
                  {getStatusText(website.status)}
                </Typography>
              </Box>
            </CardContent>
            <CardActions>
              {website.status === 'failed' && (
                <IconButton
                  color="primary"
                  onClick={() => handleRetryWebsite(website.id)}
                >
                  <RefreshIcon />
                </IconButton>
              )}
              <IconButton
                color="error"
                onClick={() => handleDeleteWebsite(website.id)}
              >
                <DeleteIcon />
              </IconButton>
            </CardActions>
          </Card>
        ))}
      </Box>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>افزودن وب‌سایت جدید</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="آدرس وب‌سایت"
            type="url"
            fullWidth
            value={newUrl}
            onChange={(e) => setNewUrl(e.target.value)}
            disabled={loading}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={loading}>
            انصراف
          </Button>
          <Button
            onClick={handleAddWebsite}
            variant="contained"
            disabled={loading || !newUrl.trim()}
          >
            {loading ? <CircularProgress size={24} /> : 'افزودن'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WebsiteManager; 