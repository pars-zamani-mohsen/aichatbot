import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  useTheme,
  useMediaQuery,
  AppBar,
  Toolbar,
  Breadcrumbs,
  Link
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import WebsiteManager from '../components/Websites/WebsiteManager';
import ChatWindow from '../components/Chat/ChatWindow';
import WidgetManager from '../components/Websites/WidgetManager';
import ResourceManager from '../components/Websites/ResourceManager';
import SourcesManager from '../components/Websites/SourcesManager';
import RAGSettings from '../components/Websites/RAGSettings';
import ConversationLogs from '../components/Websites/ConversationLogs';

const Home = () => {
  const [selectedWebsite, setSelectedWebsite] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));

  const handleSelectWebsite = (website) => {
    setSelectedWebsite(website);
    setActiveTab(0); // Reset to first tab when selecting a new website
  };

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
  };

  const tabNames = [
    'مدیریت ویجت',
    'مدیریت منابع',
    'تنظیمات RAG',
    'لاگ مکالمات',
    'چت'
  ];

  const renderTabContent = () => {
    if (!selectedWebsite) {
      return (
        <Box
          sx={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <Typography variant="h6" color="text.secondary">
            لطفاً یک وب‌سایت را انتخاب کنید
          </Typography>
        </Box>
      );
    }

    switch (activeTab) {
      case 0:
        return <WidgetManager website={selectedWebsite} />;
      case 1:
        return <SourcesManager website={selectedWebsite} />;
      case 2:
        return <RAGSettings website={selectedWebsite} />;
      case 3:
        return <ConversationLogs website={selectedWebsite} />;
      case 4:
        return (
          <ChatWindow
            websiteId={selectedWebsite.id}
            websiteName={selectedWebsite.name || selectedWebsite.url}
          />
        );
      default:
        return (
          <Box
            sx={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Typography variant="h6" color="text.secondary">
              محتوای زبانه در دسترس نیست
            </Typography>
          </Box>
        );
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <AppBar position="static" elevation={1} sx={{ backgroundColor: 'background.paper', color: 'text.primary' }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Breadcrumbs separator={<ChevronRightIcon fontSize="small" />} aria-label="breadcrumb">
            <Link
              underline="hover"
              color="inherit"
              href="#"
              sx={{ display: 'flex', alignItems: 'center' }}
            >
              <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
              داشبورد
            </Link>
            {selectedWebsite && (
              <Typography color="text.primary" sx={{ display: 'flex', alignItems: 'center' }}>
                {selectedWebsite.name || selectedWebsite.url}
              </Typography>
            )}
          </Breadcrumbs>
        </Toolbar>
      </AppBar>

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {/* Sidebar */}
        <Box
          sx={{
            width: isMobile ? '100%' : 320,
            minWidth: isMobile ? '100%' : 320,
            borderRight: 1,
            borderColor: 'divider',
            backgroundColor: 'background.paper',
            overflow: 'auto'
          }}
        >
          <WebsiteManager
            onSelectWebsite={handleSelectWebsite}
            selectedWebsite={selectedWebsite}
          />
        </Box>

        {/* Content Area */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {selectedWebsite ? (
            <>
              {/* Tabs */}
              <Box sx={{ borderBottom: 1, borderColor: 'divider', backgroundColor: 'background.paper' }}>
                <Tabs
                  value={activeTab}
                  onChange={(e, newValue) => handleTabChange(newValue)}
                  variant={isMobile ? 'scrollable' : 'standard'}
                  scrollButtons="auto"
                  sx={{
                    '& .MuiTab-root': {
                      minHeight: 48,
                      textTransform: 'none',
                      fontSize: '0.875rem',
                      fontWeight: 500,
                      color: 'text.secondary',
                      '&.Mui-selected': {
                        color: 'primary.main',
                        fontWeight: 600
                      }
                    },
                    '& .MuiTabs-indicator': {
                      backgroundColor: 'primary.main',
                      height: 3
                    }
                  }}
                >
                  {tabNames.map((name, index) => (
                    <Tab key={index} label={name} />
                  ))}
                </Tabs>
              </Box>

              {/* Tab Content */}
              <Box sx={{ flex: 1, overflow: 'auto', backgroundColor: 'background.default' }}>
                {renderTabContent()}
              </Box>
            </>
          ) : (
            <Box
              sx={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 'background.default'
              }}
            >
              <Box sx={{ textAlign: 'center', p: 4 }}>
                <Typography variant="h5" color="text.secondary" gutterBottom>
                  خوش آمدید
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  برای شروع، یک وب‌سایت از لیست سمت راست انتخاب کنید
                </Typography>
              </Box>
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
};

export default Home; 