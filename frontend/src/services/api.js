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

    console.log('Request Details:', {
      url: config.url,
      method: config.method,
      baseURL: config.baseURL,
      fullURL: `${config.baseURL}${config.url}`,
      headers: {
        ...config.headers,
        Authorization: config.headers.Authorization ? 'Bearer [REDACTED]' : undefined
      },
      data: config.data,
      params: config.params
    });
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
    console.log('Response Details:', {
      url: response.config.url,
      fullURL: `${response.config.baseURL}${response.config.url}`,
      status: response.status,
      statusText: response.statusText,
      data: response.data,
      headers: response.headers
    });
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
      console.log('Request was aborted or timed out, ignoring error');
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
      window.location.href = '/login';
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
};

export const websites = {
  getAll: async () => {
    try {
      console.log('Getting all websites...');
      const token = localStorage.getItem('token');
      console.log('Current token:', token);

      const response = await api.get('/api/');
      console.log('Websites response:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error in getAll:', error);

      // اگر درخواست abort شده، دوباره تلاش کنیم
      if (error.code === 'ECONNABORTED' || error.message === 'Request aborted') {
        console.log('Request aborted, retrying...');
        try {
          const retryResponse = await api.get('/api/');
          console.log('Retry successful:', retryResponse.data);
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
        console.log('Request aborted or timed out, retrying user stats...');
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
        console.log('Request aborted or timed out, retrying weekly stats...');
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
  }
};

export default api; 