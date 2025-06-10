import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// اضافه کردن توکن به درخواست‌ها
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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
      message: error.message
    });
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

export default api; 