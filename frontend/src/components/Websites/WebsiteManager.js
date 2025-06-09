import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  IconButton
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { websites } from '../../services/api';

const WebsiteManager = ({ onSelectWebsite }) => {
  const [websiteList, setWebsiteList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [newWebsite, setNewWebsite] = useState({
    url: '',
    name: ''
  });

  const getErrorMessage = (err) => {
    console.log('Error object:', err);
    console.log('Error response data:', err.response?.data);
    
    // اگر خطا یک رشته است، مستقیماً برگردانده شود
    if (typeof err === 'string') return err;
    
    // اگر خطا در response.data.detail است
    if (err.response?.data?.detail) {
      // اگر detail یک آرایه است (خطای اعتبارسنجی)
      if (Array.isArray(err.response.data.detail)) {
        return err.response.data.detail.map(error => {
          if (typeof error === 'object') {
            return `${error.loc?.join('.')}: ${error.msg}`;
          }
          return error;
        }).join('\n');
      }
      return err.response.data.detail;
    }
    
    // اگر response.data یک رشته است
    if (typeof err.response?.data === 'string') return err.response.data;
    
    // اگر response.data یک شیء است
    if (err.response?.data) {
      // اگر msg وجود دارد
      if (err.response.data.msg) return err.response.data.msg;
      
      // اگر type و msg وجود دارد (خطای اعتبارسنجی)
      if (err.response.data.type && err.response.data.msg) {
        return err.response.data.msg;
      }
      
      // اگر loc و msg وجود دارد (خطای اعتبارسنجی)
      if (err.response.data.loc && err.response.data.msg) {
        return err.response.data.msg;
      }
      
      // اگر هیچ کدام از موارد بالا نبود، کل شیء را به رشته تبدیل کن
      return JSON.stringify(err.response.data, null, 2);
    }
    
    // اگر هیچ کدام از موارد بالا نبود، پیام خطای پیش‌فرض
    return 'خطا در ارتباط با سرور';
  };

  const fetchWebsites = async () => {
    setLoading(true);
    setError('');
    try {
      console.log('Fetching websites...');
      const data = await websites.getAll();
      console.log('Received data:', data);
      setWebsiteList(data);
    } catch (err) {
      console.error('Error details:', err.response || err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWebsites();
  }, []);

  const handleAddWebsite = async () => {
    if (!newWebsite.url) return;

    setLoading(true);
    setError('');
    try {
      console.log('Adding website:', newWebsite);
      const data = await websites.create(newWebsite);
      console.log('Added website:', data);
      setWebsiteList(prev => [...prev, data]);
      setOpenDialog(false);
      setNewWebsite({ url: '', name: '' });
    } catch (err) {
      console.error('Error adding website:', err.response || err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWebsite = async (id) => {
    if (!window.confirm('آیا از حذف این وب‌سایت اطمینان دارید؟')) return;

    setLoading(true);
    setError('');
    try {
      console.log('Deleting website:', id);
      await websites.delete(id);
      console.log('Website deleted successfully');
      setWebsiteList(prev => prev.filter(website => website.id !== id));
    } catch (err) {
      console.error('Error deleting website:', err.response || err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6">وب‌سایت‌ها</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          افزودن
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ m: 2, whiteSpace: 'pre-line' }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress />
        </Box>
      ) : (
        <List sx={{ flex: 1, overflow: 'auto' }}>
          {websiteList.map((website) => (
            <ListItem
              key={website.id}
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={() => handleDeleteWebsite(website.id)}
                >
                  <DeleteIcon />
                </IconButton>
              }
              disablePadding
            >
              <ListItemButton onClick={() => onSelectWebsite(website)}>
                <ListItemText
                  primary={website.name || website.url}
                  secondary={website.url}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
        <DialogTitle>افزودن وب‌سایت جدید</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="آدرس وب‌سایت"
            type="url"
            fullWidth
            variant="outlined"
            value={newWebsite.url}
            onChange={(e) => setNewWebsite(prev => ({ ...prev, url: e.target.value }))}
            dir="rtl"
          />
          <TextField
            margin="dense"
            label="نام وب‌سایت (اختیاری)"
            type="text"
            fullWidth
            variant="outlined"
            value={newWebsite.name}
            onChange={(e) => setNewWebsite(prev => ({ ...prev, name: e.target.value }))}
            dir="rtl"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>انصراف</Button>
          <Button
            onClick={handleAddWebsite}
            variant="contained"
            disabled={!newWebsite.url || loading}
          >
            {loading ? 'در حال افزودن...' : 'افزودن'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WebsiteManager; 