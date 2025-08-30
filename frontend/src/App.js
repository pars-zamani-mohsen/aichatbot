import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { createTheme as createRtlTheme } from '@mui/material/styles';
import rtlPlugin from 'stylis-plugin-rtl';
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';
import { prefixer } from 'stylis';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import PrivateRoute from './components/Auth/PrivateRoute';
import AdminLayout from './components/Layout/AdminLayout';
import UserLayout from './components/Layout/UserLayout';
import AdminDashboard from './components/Dashboard/AdminDashboard';
import UserDashboard from './components/Dashboard/UserDashboard';
import UserManagement from './components/Admin/UserManagement';
import WebsiteManagement from './components/Admin/WebsiteManagement';
import ConversationManagement from './components/Admin/ConversationManagement';
import Reports from './components/Admin/Reports';
import SystemSettings from './components/Admin/SystemSettings';
import UserConversations from './components/User/UserConversations';
import UserReports from './components/User/UserReports';
import UserHistory from './components/User/UserHistory';
import UserSettings from './components/User/UserSettings';
import NotificationCenter from './components/Notifications/NotificationCenter';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// ایجاد تم با پشتیبانی از RTL
const theme = createTheme({
  direction: 'rtl',
  typography: {
    fontFamily: 'Vazirmatn, Arial',
  },
  palette: {
    primary: {
      main: '#667eea',
    },
    secondary: {
      main: '#ec4899',
    },
    success: {
      main: '#10b981',
    },
    warning: {
      main: '#f59e0b',
    },
    error: {
      main: '#ef4444',
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 600,
        },
      },
    },
  },
});

// تنظیمات کش برای RTL
const cacheRtl = createCache({
  key: 'muirtl',
  stylisPlugins: [prefixer, rtlPlugin],
});

function AppContent() {
  const { user, loading } = useAuth();

  const renderLayout = () => {
    if (!user) return null;

    // اگر کاربر admin است
    if (user.role === 'admin') {
      return (
        <AdminLayout>
          <Routes>
            <Route path="/admin/dashboard" element={<AdminDashboard />} />
            <Route path="/admin/websites" element={<WebsiteManagement />} />
            <Route path="/admin/conversations" element={<ConversationManagement />} />
            <Route path="/admin/users" element={<UserManagement />} />
            <Route path="/admin/reports" element={<Reports />} />
            <Route path="/admin/settings" element={<SystemSettings />} />
            <Route path="*" element={<Navigate to="/admin/dashboard" replace />} />
          </Routes>
        </AdminLayout>
      );
    }

    // اگر کاربر عادی است
    return (
      <UserLayout>
        <Routes>
          <Route path="/dashboard" element={<UserDashboard />} />
          <Route path="/websites" element={<Home />} />
          <Route path="/conversations" element={<UserConversations />} />
          <Route path="/reports" element={<UserReports />} />
          <Route path="/history" element={<UserHistory />} />
          <Route path="/settings" element={<UserSettings />} />
          <Route path="/notifications" element={<NotificationCenter />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </UserLayout>
    );
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}>
        <div style={{ color: 'white', fontSize: '24px' }}>در حال بارگذاری...</div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          path="/*"
          element={
            <PrivateRoute>
              {renderLayout()}
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

function App() {
  return (
    <CacheProvider value={cacheRtl}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <AppContent />
        </AuthProvider>
      </ThemeProvider>
    </CacheProvider>
  );
}

export default App; 