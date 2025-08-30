import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box
} from '@mui/material';
import { auth } from '../services/api';
import NotificationBell from './Notifications/NotificationBell';

const Navbar = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const handleLogout = () => {
    auth.logout();
    navigate('/login');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Box sx={{
            width: 40,
            height: 40,
            mr: 2,
            borderRadius: '50%',
            overflow: 'hidden',
            border: '2px solid rgba(255,255,255,0.3)'
          }}>
            <img
              src="/logo.png"
              alt="لوگو"
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />
          </Box>
          <Typography variant="h6" component="div">
            چت‌بات هوشمند
          </Typography>
        </Box>
        {token && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <NotificationBell />
            <Button color="inherit" onClick={handleLogout}>
              خروج
            </Button>
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 