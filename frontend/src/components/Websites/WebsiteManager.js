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
  LinearProgress,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import WarningIcon from '@mui/icons-material/Warning';
import CancelIcon from '@mui/icons-material/Cancel';
import { websites } from '../../services/api';
import SourcesManager from './SourcesManager';

const WebsiteManager = ({ onSelectWebsite, selectedWebsite, activeTab, onTabChange }) => {
  const [websiteList, setWebsiteList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [newWebsite, setNewWebsite] = useState({
    url: '',
    name: '',
    max_pages: 50,
    max_depth: 3
  });
  const [crawlingStatus, setCrawlingStatus] = useState({});
  const [crawlingStartTime, setCrawlingStartTime] = useState({});
  const [crawlingProgress, setCrawlingProgress] = useState({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [websiteToDelete, setWebsiteToDelete] = useState(null);

  const getErrorMessage = (err) => {

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
      const data = await websites.getAll();
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
      const data = await websites.create(newWebsite);
      setWebsiteList(prev => [...prev, data]);
      setOpenDialog(false);
      setNewWebsite({ url: '', name: '', max_pages: 50, max_depth: 3 });

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

  const handleDeleteWebsite = (website) => {
    setWebsiteToDelete(website);
    setDeleteDialogOpen(true);
  };

  const confirmDeleteWebsite = async () => {
    if (!websiteToDelete) return;

    setLoading(true);
    setError('');
    setSuccess('');
    setDeleteDialogOpen(false);

    try {
      await websites.delete(websiteToDelete.id);
      setWebsiteList(prev => prev.filter(website => website.id !== websiteToDelete.id));
      setSuccess(`وب‌سایت "${websiteToDelete.name || websiteToDelete.url}" با موفقیت حذف شد`);

      // پاک کردن پیام موفقیت بعد از 3 ثانیه
      setTimeout(() => {
        setSuccess('');
      }, 3000);
    } catch (err) {
      console.error('Error deleting website:', err.response || err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
      setWebsiteToDelete(null);
    }
  };

  const cancelDeleteWebsite = () => {
    setDeleteDialogOpen(false);
    setWebsiteToDelete(null);
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

      {selectedWebsite && (
        <Tabs value={activeTab} onChange={(e, newValue) => onTabChange(newValue)}>
          <Tab label="مدیریت ویجت" />
          <Tab label="مدیریت منابع" />
          <Tab label="تنظیمات RAG" />
          <Tab label="لاگ مکالمات" />
          <Tab label="چت" />
        </Tabs>
      )}

      {error && (
        <Alert severity="error" sx={{ m: 2, whiteSpace: 'pre-line' }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ m: 2 }}>
          {success}
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
                  onClick={() => handleDeleteWebsite(website)}
                >
                  <DeleteIcon />
                </IconButton>
              }
              disablePadding
            >
              <ListItemButton
                onClick={() => onSelectWebsite(website)}
                selected={selectedWebsite && selectedWebsite.id === website.id}
              >
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
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
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
                placeholder="https://example.com"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                margin="dense"
                label="نام وب‌سایت (اختیاری)"
                type="text"
                fullWidth
                variant="outlined"
                value={newWebsite.name}
                onChange={(e) => setNewWebsite(prev => ({ ...prev, name: e.target.value }))}
                dir="rtl"
                placeholder="نام دلخواه برای وب‌سایت"
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth margin="dense">
                <InputLabel>حداکثر صفحات</InputLabel>
                <Select
                  value={newWebsite.max_pages}
                  onChange={(e) => setNewWebsite(prev => ({ ...prev, max_pages: e.target.value }))}
                  label="حداکثر صفحات"
                >
                  <MenuItem value={10}>10 صفحه</MenuItem>
                  <MenuItem value={25}>25 صفحه</MenuItem>
                  <MenuItem value={50}>50 صفحه</MenuItem>
                  <MenuItem value={100}>100 صفحه</MenuItem>
                  <MenuItem value={200}>200 صفحه</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth margin="dense">
                <InputLabel>حداکثر عمق</InputLabel>
                <Select
                  value={newWebsite.max_depth}
                  onChange={(e) => setNewWebsite(prev => ({ ...prev, max_depth: e.target.value }))}
                  label="حداکثر عمق"
                >
                  <MenuItem value={1}>1 سطح (فقط صفحه اصلی)</MenuItem>
                  <MenuItem value={2}>2 سطح</MenuItem>
                  <MenuItem value={3}>3 سطح</MenuItem>
                  <MenuItem value={4}>4 سطح</MenuItem>
                  <MenuItem value={5}>5 سطح</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
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

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={cancelDeleteWebsite}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          color: 'error.main',
          pb: 1
        }}>
          <WarningIcon sx={{ fontSize: 28 }} />
          <Typography variant="h6" component="div">
            حذف وب‌سایت
          </Typography>
        </DialogTitle>

        <DialogContent sx={{ pt: 2 }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="body1" sx={{ mb: 2, fontWeight: 'medium' }}>
              آیا از حذف وب‌سایت <strong>"{websiteToDelete?.name || websiteToDelete?.url}"</strong> اطمینان دارید؟
            </Typography>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                ⚠️ این عمل غیرقابل بازگشت است!
              </Typography>
            </Alert>

            <Box sx={{
              bgcolor: 'grey.50',
              p: 2,
              borderRadius: 1,
              border: '1px solid',
              borderColor: 'grey.200'
            }}>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 'medium' }}>
                موارد زیر به طور کامل حذف خواهند شد:
              </Typography>
              <Box component="ul" sx={{ m: 0, pl: 2, color: 'text.secondary' }}>
                <li>تمام صفحات کراول شده و داده‌های CSV</li>
                <li>تمام امبدینگ‌ها و اطلاعات ChromaDB</li>
                <li>تمام چت‌ها و تاریخچه مکالمات</li>
                <li>تمام پیام‌های ذخیره شده</li>
                <li>تنظیمات RAG و پیکربندی‌های شخصی</li>
                <li>فایل‌های آپلود شده و منابع متنی</li>
              </Box>
            </Box>
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button
            onClick={cancelDeleteWebsite}
            startIcon={<CancelIcon />}
            variant="outlined"
            sx={{ minWidth: 120 }}
          >
            انصراف
          </Button>
          <Button
            onClick={confirmDeleteWebsite}
            startIcon={<DeleteIcon />}
            variant="contained"
            color="error"
            sx={{ minWidth: 120 }}
            disabled={loading}
          >
            {loading ? 'در حال حذف...' : 'حذف قطعی'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WebsiteManager; 