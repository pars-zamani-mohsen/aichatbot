import React, { useState } from 'react';
import { Box, Grid, Paper, Typography } from '@mui/material';
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

  const handleSelectWebsite = (website) => {
    setSelectedWebsite(website);
    setActiveTab(0); // Reset to first tab when selecting a new website
  };

  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
  };

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
    <Box sx={{ flexGrow: 1, height: '100vh', p: 2 }}>
      <Grid container spacing={2} sx={{ height: '100%' }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ height: '100%', overflow: 'auto' }}>
            <WebsiteManager
              onSelectWebsite={handleSelectWebsite}
              selectedWebsite={selectedWebsite}
              activeTab={activeTab}
              onTabChange={handleTabChange}
            />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ height: '100%' }}>
            {renderTabContent()}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home; 