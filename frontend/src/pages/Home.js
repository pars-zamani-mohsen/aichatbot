import React, { useState } from 'react';
import { Box, Grid, Paper, Typography } from '@mui/material';
import WebsiteManager from '../components/Websites/WebsiteManager';
import ChatWindow from '../components/Chat/ChatWindow';

const Home = () => {
  const [selectedWebsite, setSelectedWebsite] = useState(null);

  return (
    <Box sx={{ flexGrow: 1, height: '100vh', p: 2 }}>
      <Grid container spacing={2} sx={{ height: '100%' }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ height: '100%', overflow: 'auto' }}>
            <WebsiteManager onSelectWebsite={setSelectedWebsite} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ height: '100%' }}>
            {selectedWebsite ? (
              <ChatWindow 
                websiteId={selectedWebsite.id} 
                websiteName={selectedWebsite.name || selectedWebsite.url}
              />
            ) : (
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
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home; 