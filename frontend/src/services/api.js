import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000, // 15 ثانیه timeout
});

// اضافه کردن توکن به درخواست‌ها
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // اضافه کردن Content-Type برای درخواست‌های GET
    if (config.method === 'get') {
      config.headers['Content-Type'] = 'application/json';
    }


    return config;
  },
  (error) => {
    console.error('Request Error:', error);
    return Promise.reject(error);
  }
);

// مدیریت خطاهای 401
api.interceptors.response.use(
  (response) => {

    return response;
  },
  (error) => {
    console.error('Response Error Details:', {
      url: error.config?.url,
      fullURL: error.config ? `${error.config.baseURL}${error.config.url}` : null,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      params: error.config?.params,
      message: error.message,
      code: error.code
    });

    // اگر درخواست abort شده یا timeout، خطا را نادیده بگیریم
    if (error.code === 'ECONNABORTED' || error.message === 'Request aborted' || error.message.includes('timeout')) {
      // برگرداندن داده‌های خالی با ساختار صحیح
      return Promise.resolve({
        data: {
          websites: { total: 0, ready: 0, trend: 0 },
          users: { total: 0, active: 0, trend: 0 },
          chats: { total: 0, trend: 0 },
          messages: { total: 0, trend: 0 }
        }
      });
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('userInfo');
      // به جای redirect، خطا را reject کنیم تا component بتواند آن را handle کند
    }
    return Promise.reject(error);
  }
);

export const auth = {
  login: async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/api/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // بررسی status code
    if (response.status === 202) {
      // نیاز به 2FA
      const error = new Error('2FA required');
      error.response = response;
      throw error;
    }

    // ذخیره توکن و اطلاعات کاربر
    const { access_token, refresh_token, user } = response.data;
    localStorage.setItem('token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('userInfo', JSON.stringify(user));

    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/api/register', userData);
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
  },

  // تنظیمات کاربر
  getUserSettings: async () => {
    try {
      const response = await api.get('/api/settings');
      return response.data;
    } catch (error) {
      console.error('Error getting user settings:', error);
      // در صورت خطا، تنظیمات پیش‌فرض برگردانیم
      return {
        personal: {
          firstName: '',
          lastName: '',
          email: '',
          phone: ''
        },
        security: {
          twoFactorEnabled: false
        },
        notifications: {
          emailNotifications: true,
          pushNotifications: true,
          smsNotifications: false,
          notifyOnNewConversation: true,
          notifyOnWebsiteUpdate: true
        },
        appearance: {
          language: 'fa',
          theme: 'light',
          timezone: 'Asia/Tehran'
        },
        rag: {
          defaultK: 5,
          maxResponseLength: 500,
          defaultTemperature: 0.7,
          defaultLanguage: 'fa'
        }
      };
    }
  },

  updateUserSettings: async (settings) => {
    try {
      const response = await api.put('/api/settings', settings);
      return response.data;
    } catch (error) {
      console.error('Error updating user settings:', error);
      throw error;
    }
  },

  changePassword: async (passwordData) => {
    try {
      const response = await api.post('/api/change-password', passwordData);
      return response.data;
    } catch (error) {
      console.error('Error changing password:', error);
      throw error;
    }
  },

  verifyEmail: async (token) => {
    try {
      const response = await api.get(`/api/verify-email?token=${token}`);
      return response.data;
    } catch (error) {
      console.error('Error verifying email:', error);
      throw error;
    }
  },

  // احراز هویت دو مرحله‌ای
  enable2FA: async () => {
    try {
      const response = await api.post('/api/enable-2fa');
      return response.data;
    } catch (error) {
      console.error('Error enabling 2FA:', error);
      throw error;
    }
  },

  verify2FA: async (code) => {
    try {
      const response = await api.post('/api/verify-2fa', { code });
      return response.data;
    } catch (error) {
      console.error('Error verifying 2FA:', error);
      throw error;
    }
  },

  disable2FA: async () => {
    try {
      const response = await api.post('/api/disable-2fa');
      return response.data;
    } catch (error) {
      console.error('Error disabling 2FA:', error);
      throw error;
    }
  },

  // بازیابی کلمه عبور
  forgotPassword: async (email) => {
    try {
      const response = await api.post('/api/forgot-password', { email });
      return response.data;
    } catch (error) {
      console.error('Error requesting password reset:', error);
      throw error;
    }
  },

  resetPassword: async (token, newPassword) => {
    try {
      const response = await api.post('/api/reset-password', {
        token,
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      console.error('Error resetting password:', error);
      throw error;
    }
  },

  loginWith2FA: async (code, email) => {
    try {
      const response = await api.post('/api/login-2fa', { code, email });

      // ذخیره توکن و اطلاعات کاربر
      const { access_token, refresh_token, user } = response.data;
      localStorage.setItem('token', access_token);
      localStorage.setItem('refresh_token', refresh_token);
      localStorage.setItem('userInfo', JSON.stringify(user));

      return response.data;
    } catch (error) {
      console.error('Error logging in with 2FA:', error);
      throw error;
    }
  }
};

export const websites = {
  getAll: async () => {
    try {
      const token = localStorage.getItem('token');

      const response = await api.get('/api/');
      return response.data;
    } catch (error) {
      console.error('Error in getAll:', error);

      // اگر درخواست abort شده، دوباره تلاش کنیم
      if (error.code === 'ECONNABORTED' || error.message === 'Request aborted') {
        try {
          const retryResponse = await api.get('/api/');
          return retryResponse.data;
        } catch (retryError) {
          console.error('Retry failed:', retryError);
          throw retryError;
        }
      }

      if (error.response?.status === 422) {
        console.error('Validation Error Details:', {
          status: error.response.status,
          data: error.response.data,
          detail: error.response.data.detail,
          headers: error.response.headers
        });
      }
      console.error('Error response:', error.response?.data);
      throw error;
    }
  },

  getById: async (id) => {
    try {
      const numericId = parseInt(id, 10);
      if (isNaN(numericId)) {
        throw new Error('شناسه وب‌سایت نامعتبر است');
      }
      const response = await api.get(`/api/${numericId}`);
      return response.data;
    } catch (error) {
      console.error('Error in getById:', error);
      throw error;
    }
  },

  create: async (websiteData) => {
    try {
      const response = await api.post('/api/websites/crawl', websiteData);
      return response.data;
    } catch (error) {
      console.error('Error in create:', error);
      throw error;
    }
  },

  update: async (id, data) => {
    try {
      const numericId = parseInt(id, 10);
      if (isNaN(numericId)) {
        throw new Error('شناسه وب‌سایت نامعتبر است');
      }
      const response = await api.put(`/api/${numericId}`, data);
      return response.data;
    } catch (error) {
      console.error('Error in update:', error);
      throw error;
    }
  },

  delete: async (id) => {
    try {
      const numericId = parseInt(id, 10);
      if (isNaN(numericId)) {
        throw new Error('شناسه وب‌سایت نامعتبر است');
      }
      const response = await api.delete(`/api/${numericId}`);
      return response.data;
    } catch (error) {
      console.error('Error in delete:', error);
      throw error;
    }
  },
};

export const chats = {
  create: async (websiteId, message, chatId = null) => {
    try {
      const numericId = parseInt(websiteId);
      if (isNaN(numericId)) {
        throw new Error('شناسه وب‌سایت نامعتبر است');
      }
      const response = await api.post('/api/chats/', {
        website_id: numericId,
        message,
        session_id: localStorage.getItem('session_id') || undefined,
        chat_id: chatId
      });
      return response.data;
    } catch (error) {
      console.error('Error creating chat:', error);
      throw error;
    }
  },

  getWebsiteChats: async (websiteId) => {
    try {
      const numericId = parseInt(websiteId);
      if (isNaN(numericId)) {
        throw new Error('شناسه وب‌سایت باید یک عدد معتبر باشد');
      }
      const response = await api.get('/api/chats/list', {
        params: { website_id: numericId }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting website chats:', error);
      throw error;
    }
  },

  getHistory: async (chatId) => {
    try {
      const numericId = parseInt(chatId);
      if (isNaN(numericId)) {
        throw new Error('شناسه چت نامعتبر است');
      }
      const response = await api.get(`/api/chats/${numericId}/messages`);
      return response.data;
    } catch (error) {
      console.error('Error getting chat history:', error);
      throw error;
    }
  },

  // API های جدید برای conversations کاربر
  getUserConversations: async (page = 1, limit = 20, status = null, search = null) => {
    try {
      const params = { page, limit };
      if (status) params.status = status;
      if (search) params.search = search;

      const response = await api.get('/api/chats/user/conversations', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting user conversations:', error);
      throw error;
    }
  },

  getUserConversationDetail: async (conversationId) => {
    try {
      const numericId = parseInt(conversationId);
      if (isNaN(numericId)) {
        throw new Error('شناسه مکالمه نامعتبر است');
      }
      const response = await api.get(`/api/chats/user/conversations/${numericId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting conversation detail:', error);
      throw error;
    }
  },

  deleteUserConversation: async (conversationId) => {
    try {
      const numericId = parseInt(conversationId);
      if (isNaN(numericId)) {
        throw new Error('شناسه مکالمه نامعتبر است');
      }
      const response = await api.delete(`/api/chats/user/conversations/${numericId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting conversation:', error);
      throw error;
    }
  },
};

export const dashboard = {
  // آمار داشبورد کاربر
  getUserStats: async () => {
    try {
      const response = await api.get('/api/dashboard/stats');
      return response.data;
    } catch (error) {
      console.error('Error getting user stats:', error);

      // اگر درخواست abort شده یا timeout، دوباره تلاش کنیم
      if (error.code === 'ECONNABORTED' || error.message === 'Request aborted' || error.message.includes('timeout')) {
        try {
          const retryResponse = await api.get('/api/dashboard/stats');
          return retryResponse.data;
        } catch (retryError) {
          console.error('Retry failed:', retryError);
        }
      }

      // در صورت خطا، داده‌های خالی برگردانیم
      return {
        websites: { total: 0, ready: 0 },
        chats: { total: 0, trend: 0 },
        messages: { total: 0, trend: 0 }
      };
    }
  },

  getUserRecentActivity: async (limit = 10) => {
    try {
      const response = await api.get('/api/dashboard/recent-activity', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting user recent activity:', error);

      // اگر درخواست abort شده یا timeout، دوباره تلاش کنیم
      if (error.code === 'ECONNABORTED' || error.message === 'Request aborted' || error.message.includes('timeout')) {
        console.log('Request aborted or timed out, retrying recent activity...');
        try {
          const retryResponse = await api.get('/api/dashboard/recent-activity', {
            params: { limit }
          });
          return retryResponse.data;
        } catch (retryError) {
          console.error('Retry failed:', retryError);
        }
      }

      // در صورت خطا، داده‌های خالی برگردانیم
      return {
        recent_websites: [],
        recent_chats: [],
        recent_messages: []
      };
    }
  },

  getWebsiteDetailedStats: async (websiteId) => {
    try {
      const response = await api.get(`/api/dashboard/websites/${websiteId}/detailed-stats`);
      return response.data;
    } catch (error) {
      console.error('Error getting website detailed stats:', error);
      throw error;
    }
  },

  // آمار داشبورد ادمین
  getAdminStats: async () => {
    try {
      const response = await api.get('/api/dashboard/admin/stats');
      return response.data;
    } catch (error) {
      console.error('Error getting admin stats:', error);
      // در صورت خطا، داده‌های خالی برگردانیم
      return {
        websites: { total: 0, trend: 0 },
        users: { total: 0, active: 0, trend: 0 },
        chats: { total: 0, trend: 0 },
        messages: { total: 0, trend: 0 }
      };
    }
  },

  getAdminRecentActivity: async (limit = 10) => {
    try {
      const response = await api.get('/api/dashboard/admin/recent-activity', {
        params: { limit }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting admin recent activity:', error);
      // در صورت خطا، داده‌های خالی برگردانیم
      return {
        recent_users: [],
        recent_websites: [],
        recent_chats: []
      };
    }
  },

  // آمار هفتگی
  getWeeklyStats: async () => {
    try {
      const response = await api.get('/api/dashboard/weekly-stats');
      return response.data;
    } catch (error) {
      console.error('Error getting weekly stats:', error);

      // اگر درخواست abort شده یا timeout، دوباره تلاش کنیم
      if (error.code === 'ECONNABORTED' || error.message === 'Request aborted' || error.message.includes('timeout')) {
        try {
          const retryResponse = await api.get('/api/dashboard/weekly-stats');
          return retryResponse.data;
        } catch (retryError) {
          console.error('Retry failed:', retryError);
        }
      }

      // در صورت خطا، داده‌های خالی برگردانیم
      return [
        { day: 'شنبه', conversations: 0, messages: 0 },
        { day: 'یکشنبه', conversations: 0, messages: 0 },
        { day: 'دوشنبه', conversations: 0, messages: 0 },
        { day: 'سه‌شنبه', conversations: 0, messages: 0 },
        { day: 'چهارشنبه', conversations: 0, messages: 0 },
        { day: 'پنج‌شنبه', conversations: 0, messages: 0 },
        { day: 'جمعه', conversations: 0, messages: 0 },
      ];
    }
  },

  getAdminWeeklyStats: async () => {
    try {
      const response = await api.get('/api/dashboard/admin/weekly-stats');
      return response.data;
    } catch (error) {
      console.error('Error getting admin weekly stats:', error);
      // در صورت خطا، داده‌های خالی برگردانیم
      return [
        { day: 'شنبه', conversations: 0, users: 0 },
        { day: 'یکشنبه', conversations: 0, users: 0 },
        { day: 'دوشنبه', conversations: 0, users: 0 },
        { day: 'سه‌شنبه', conversations: 0, users: 0 },
        { day: 'چهارشنبه', conversations: 0, users: 0 },
        { day: 'پنج‌شنبه', conversations: 0, users: 0 },
        { day: 'جمعه', conversations: 0, users: 0 },
      ];
    }
  },

  // ==================== مدیریت کاربران ====================
  getAdminUsers: async (page = 1, limit = 20, search = null, role = null, status = null) => {
    try {
      const params = { page, limit };
      if (search) params.search = search;
      if (role) params.role = role;
      if (status) params.status = status;

      const response = await api.get('/api/dashboard/admin/users', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting admin users:', error);
      return {
        users: [],
        total: 0,
        page: 1,
        limit: 20,
        total_pages: 0
      };
    }
  },

  updateAdminUser: async (userId, userData) => {
    try {
      const response = await api.put(`/api/dashboard/admin/users/${userId}`, userData);
      return response.data;
    } catch (error) {
      console.error('Error updating admin user:', error);
      throw error;
    }
  },

  deleteAdminUser: async (userId) => {
    try {
      const response = await api.delete(`/api/dashboard/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting admin user:', error);
      throw error;
    }
  },

  changeUserPassword: async (userId, newPassword) => {
    try {
      const response = await api.put(`/api/dashboard/admin/users/${userId}/password`, {
        new_password: newPassword
      });
      return response.data;
    } catch (error) {
      console.error('Error changing user password:', error);
      throw error;
    }
  },

  // ==================== مدیریت وب‌سایت‌ها ====================
  getAdminWebsites: async (page = 1, limit = 20, search = null, status = null, ownerId = null) => {
    try {
      const params = { page, limit };
      if (search) params.search = search;
      if (status) params.status = status;
      if (ownerId) params.owner_id = ownerId;

      const response = await api.get('/api/dashboard/admin/websites', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting admin websites:', error);
      return {
        websites: [],
        total: 0,
        page: 1,
        limit: 20,
        total_pages: 0
      };
    }
  },

  updateAdminWebsite: async (websiteId, websiteData) => {
    try {
      const response = await api.put(`/api/dashboard/admin/websites/${websiteId}`, websiteData);
      return response.data;
    } catch (error) {
      console.error('Error updating admin website:', error);
      throw error;
    }
  },

  deleteAdminWebsite: async (websiteId) => {
    try {
      const response = await api.delete(`/api/dashboard/admin/websites/${websiteId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting admin website:', error);
      throw error;
    }
  },

  // ==================== مدیریت گفتگوها ====================
  getAdminConversations: async (page = 1, limit = 20, search = null, websiteId = null, userId = null) => {
    try {
      const params = { page, limit };
      if (search) params.search = search;
      if (websiteId) params.website_id = websiteId;
      if (userId) params.user_id = userId;

      const response = await api.get('/api/dashboard/admin/conversations', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting admin conversations:', error);
      return {
        conversations: [],
        total: 0,
        page: 1,
        limit: 20,
        total_pages: 0
      };
    }
  },

  getAdminConversationMessages: async (conversationId) => {
    try {
      const response = await api.get(`/api/dashboard/admin/conversations/${conversationId}/messages`);
      return response.data;
    } catch (error) {
      console.error('Error getting admin conversation messages:', error);
      throw error;
    }
  },

  deleteAdminConversation: async (conversationId) => {
    try {
      const response = await api.delete(`/api/dashboard/admin/conversations/${conversationId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting admin conversation:', error);
      throw error;
    }
  },

  getAdminSystemSettings: async () => {
    try {
      const response = await api.get('/api/dashboard/admin/system-settings');
      return response.data;
    } catch (error) {
      console.error('Error getting admin system settings:', error);
      throw error;
    }
  },

  updateAdminSystemSettings: async (settings) => {
    try {
      const response = await api.put('/api/dashboard/admin/system-settings', settings);
      return response.data;
    } catch (error) {
      console.error('Error updating admin system settings:', error);
      throw error;
    }
  },

  // گزارشات کاربر
  getUserReports: async (timeRange = '7d') => {
    try {
      const response = await api.get('/api/dashboard/user/reports', {
        params: { time_range: timeRange }
      });
      return response.data;
    } catch (error) {
      console.error('Error getting user reports:', error);
      // در صورت خطا، داده‌های خالی برگردانیم
      return {
        summary: {
          total_conversations: 0,
          total_messages: 0,
          active_websites: 0,
          satisfaction_rate: 0,
          period_conversations: 0,
          period_messages: 0
        },
        websites_stats: [],
        conversation_status: []
      };
    }
  },

  // تاریخچه کاربر
  getUserHistory: async (page = 1, limit = 20, activityType = null, search = null) => {
    try {
      const params = { page, limit };
      if (activityType && activityType !== 'all') {
        params.activity_type = activityType;
      }
      if (search) {
        params.search = search;
      }

      const response = await api.get('/api/dashboard/user/history', { params });
      return response.data;
    } catch (error) {
      console.error('Error getting user history:', error);
      // در صورت خطا، داده‌های خالی برگردانیم
      return {
        activities: [],
        stats: {
          websites_added: 0,
          conversations: 0,
          crawls_completed: 0,
          settings_changed: 0
        },
        total: 0,
        page: 1,
        limit: 20
      };
    }
  }
};

export const notifications = {
  getNotifications: async (skip = 0, limit = 50, unreadOnly = false, category = null) => {
    try {
      const params = new URLSearchParams();
      if (skip) params.append('skip', skip);
      if (limit) params.append('limit', limit);
      if (unreadOnly) params.append('unread_only', unreadOnly);
      if (category) params.append('category', category);

      const response = await api.get(`/api/notifications/?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error getting notifications:', error);
      throw error;
    }
  },

  getUnreadCount: async (category = null) => {
    try {
      const params = new URLSearchParams();
      if (category) params.append('category', category);

      const response = await api.get(`/api/notifications/unread-count?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error getting unread count:', error);
      throw error;
    }
  },

  markAsRead: async (notificationId) => {
    try {
      const response = await api.put(`/api/notifications/${notificationId}/read`);
      return response.data;
    } catch (error) {
      console.error('Error marking notification as read:', error);
      throw error;
    }
  },

  markAllAsRead: async (category = null) => {
    try {
      const params = new URLSearchParams();
      if (category) params.append('category', category);

      const response = await api.put(`/api/notifications/mark-all-read?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      throw error;
    }
  },

  deleteNotification: async (notificationId) => {
    try {
      const response = await api.delete(`/api/notifications/${notificationId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting notification:', error);
      throw error;
    }
  },

  createTestNotification: async () => {
    try {
      const response = await api.post('/api/notifications/test');
      return response.data;
    } catch (error) {
      console.error('Error creating test notification:', error);
      throw error;
    }
  },

  // Admin notification management
  getAdminNotifications: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams();
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          queryParams.append(key, params[key]);
        }
      });

      const response = await api.get(`/api/notifications/admin/?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error getting admin notifications:', error);
      throw error;
    }
  },

  deleteAdminNotification: async (notificationId) => {
    try {
      const response = await api.delete(`/api/notifications/admin/${notificationId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting admin notification:', error);
      throw error;
    }
  },

  sendAdminNotification: async (notificationData) => {
    try {
      const response = await api.post('/api/notifications/admin/send', notificationData);
      return response.data;
    } catch (error) {
      console.error('Error sending admin notification:', error);
      throw error;
    }
  }
};

// ==================== آرشیو ایمیل‌ها ====================
export const emailArchive = {
  getAdminEmailArchive: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams();
      Object.keys(params).forEach(key => {
        if (params[key] !== undefined && params[key] !== null) {
          queryParams.append(key, params[key]);
        }
      });

      const response = await api.get(`/api/admin/email-archive?${queryParams.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error getting email archive:', error);
      throw error;
    }
  },

  getAdminEmailDetail: async (emailId) => {
    try {
      const response = await api.get(`/api/admin/email-archive/${emailId}`);
      return response.data;
    } catch (error) {
      console.error('Error getting email detail:', error);
      throw error;
    }
  },

  deleteAdminEmail: async (emailId) => {
    try {
      const response = await api.delete(`/api/admin/email-archive/${emailId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting email:', error);
      throw error;
    }
  },

  getAdminEmailStats: async () => {
    try {
      const response = await api.get('/api/admin/email-archive/stats');
      return response.data;
    } catch (error) {
      console.error('Error getting email stats:', error);
      throw error;
    }
  },

  retryFailedEmails: async (maxRetries = 3) => {
    try {
      const response = await api.post(`/api/admin/email-archive/retry-failed?max_retries=${maxRetries}`);
      return response.data;
    } catch (error) {
      console.error('Error retrying failed emails:', error);
      throw error;
    }
  }
};

export default api; 