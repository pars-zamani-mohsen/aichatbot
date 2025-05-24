import React, { useState } from 'react';
import { Box, Container, Grid, Paper, Typography } from '@mui/material';
import WebsiteManager from '../components/Websites/WebsiteManager';
import ChatWindow from '../components/Chat/ChatWindow';

const Home = () => {
  const [selectedWebsite, setSelectedWebsite] = useState(null);

  return (
    <Container maxWidth="xl" sx={{ height: '100vh', py: 3 }}>
      <Grid container spacing={3} sx={{ height: '100%' }}>
        <Grid item xs={12} md={4}>
          <Paper sx={{ height: '100%', overflow: 'auto' }}>
            <WebsiteManager onSelectWebsite={setSelectedWebsite} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ height: '100%' }}>
            {selectedWebsite ? (
              <ChatWindow websiteId={selectedWebsite.id} />
            ) : (
              <Box
                sx={{
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <Typography variant="h6" color="text.secondary">
                  لطفاً یک وب‌سایت را برای شروع چت انتخاب کنید
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Home; 