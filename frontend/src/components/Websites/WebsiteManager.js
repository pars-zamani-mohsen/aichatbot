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
  IconButton,
  LinearProgress
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
  const [crawlingStatus, setCrawlingStatus] = useState({});
  const [crawlingStartTime, setCrawlingStartTime] = useState({});
  const [crawlingProgress, setCrawlingProgress] = useState({});

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

  // تابع برای محاسبه زمان گذشته
  const getElapsedTime = (startTime) => {
    if (!startTime) return '';
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    return `${minutes} دقیقه و ${seconds} ثانیه`;
  };

  // تابع برای محاسبه زمان تقریبی باقی‌مانده
  const getEstimatedTime = (status, startTime) => {
    if (!startTime) return '';
    
    const elapsed = (Date.now() - startTime) / 1000;
    let estimatedTotal;
    
    switch (status) {
      case 'crawling':
        estimatedTotal = elapsed * 2; // تخمین: زمان کراولینگ 2 برابر زمان گذشته
        break;
      case 'processing':
        estimatedTotal = elapsed * 1.5; // تخمین: زمان پردازش 1.5 برابر زمان گذشته
        break;
      default:
        return '';
    }
    
    const remaining = Math.max(0, estimatedTotal - elapsed);
    const minutes = Math.floor(remaining / 60);
    const seconds = Math.floor(remaining % 60);
    
    return `${minutes} دقیقه و ${seconds} ثانیه`;
  };

  // تابع برای محاسبه درصد پیشرفت
  const getProgressPercentage = (status, startTime) => {
    if (!startTime) return 0;
    
    const elapsed = (Date.now() - startTime) / 1000;
    let estimatedTotal;
    
    switch (status) {
      case 'crawling':
        estimatedTotal = elapsed * 2;
        break;
      case 'processing':
        estimatedTotal = elapsed * 1.5;
        break;
      default:
        return 0;
    }
    
    return Math.min(95, Math.floor((elapsed / estimatedTotal) * 100));
  };

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
      
      // شروع بررسی وضعیت کراولینگ
      const startTime = Date.now();
      setCrawlingStartTime(prev => ({
        ...prev,
        [data.id]: startTime
      }));
      setCrawlingStatus(prev => ({
        ...prev,
        [data.id]: 'pending'
      }));
      checkCrawlingStatus(data.id);
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

  // تابع برای بررسی وضعیت کراولینگ
  const checkCrawlingStatus = async (websiteId) => {
    try {
      const website = await websites.getById(websiteId);
      setCrawlingStatus(prev => ({
        ...prev,
        [websiteId]: website.status
      }));

      // محاسبه درصد پیشرفت
      const progress = getProgressPercentage(website.status, crawlingStartTime[websiteId]);
      setCrawlingProgress(prev => ({
        ...prev,
        [websiteId]: progress
      }));

      // اگر هنوز در حال کراولینگ است، دوباره بررسی کن
      if (website.status === 'pending' || website.status === 'crawling' || website.status === 'processing') {
        setTimeout(() => checkCrawlingStatus(websiteId), 5000);
      } else {
        // اگر تمام شد، درصد را 100 کن
        setCrawlingProgress(prev => ({
          ...prev,
          [websiteId]: 100
        }));
      }
    } catch (error) {
      console.error('Error checking crawling status:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'info';
      case 'crawling':
      case 'processing':
        return 'warning';
      case 'ready':
        return 'success';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  const getStatusText = (status, websiteId) => {
    const baseText = (() => {
      switch (status) {
        case 'pending':
          return 'در انتظار شروع';
        case 'crawling':
          return 'در حال کراولینگ';
        case 'processing':
          return 'در حال پردازش';
        case 'ready':
          return 'آماده';
        case 'error':
          return 'خطا';
        default:
          return 'نامشخص';
      }
    })();

    if (status === 'ready' || status === 'error') {
      return baseText;
    }

    const elapsedTime = getElapsedTime(crawlingStartTime[websiteId]);
    return `${baseText} (${elapsedTime})`;
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
                <Box sx={{ width: '100%' }}>
                  <ListItemText
                    primary={website.name || website.url}
                    secondary={website.url}
                  />
                  {crawlingStatus[website.id] && (
                    <Box sx={{ mt: 1 }}>
                      <LinearProgress 
                        variant={crawlingStatus[website.id] === 'ready' ? 'determinate' : 'indeterminate'}
                        value={crawlingProgress[website.id] || 0}
                        color={getStatusColor(crawlingStatus[website.id])}
                        sx={{ mb: 0.5 }}
                      />
                      <Typography variant="caption" color="text.secondary">
                        {getStatusText(crawlingStatus[website.id], website.id)}
                      </Typography>
                    </Box>
                  )}
                </Box>
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