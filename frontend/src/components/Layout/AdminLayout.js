import React, { useState } from 'react';
import {
    Box,
    Drawer,
    AppBar,
    Toolbar,
    List,
    Typography,
    Divider,
    IconButton,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Avatar,
    Menu,
    MenuItem,
    Badge,
    Chip,
    useTheme,
    useMediaQuery
} from '@mui/material';
import {
    Menu as MenuIcon,
    Dashboard,
    Language,
    Chat,
    Settings,
    People,
    Assessment,
    Notifications,
    AccountCircle,
    AdminPanelSettings,
    Logout,
    Search,
    DarkMode,
    LightMode
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import NotificationBell from '../Notifications/NotificationBell';

const drawerWidth = 280;

const AdminLayout = ({ children }) => {
    const [mobileOpen, setMobileOpen] = useState(false);
    const [anchorEl, setAnchorEl] = useState(null);
    const [darkMode, setDarkMode] = useState(false);
    const theme = useTheme();
    const isMobile = useMediaQuery(theme.breakpoints.down('md'));
    const navigate = useNavigate();
    const { logout } = useAuth();

    const handleDrawerToggle = () => {
        setMobileOpen(!mobileOpen);
    };

    const handleProfileMenuOpen = (event) => {
        setAnchorEl(event.currentTarget);
    };

    const handleProfileMenuClose = () => {
        setAnchorEl(null);
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const menuItems = [
        { text: 'داشبورد', icon: <Dashboard />, path: '/admin/dashboard' },
        { text: 'مدیریت وب‌سایت‌ها', icon: <Language />, path: '/admin/websites' },
        { text: 'گفتگوها', icon: <Chat />, path: '/admin/conversations' },
        { text: 'مدیریت کاربران', icon: <People />, path: '/admin/users' },
        { text: 'گزارشات', icon: <Assessment />, path: '/admin/reports' },
        { text: 'مدیریت اعلان‌ها', icon: <Notifications />, path: '/admin/notifications' },
        { text: 'تنظیمات سیستم', icon: <Settings />, path: '/admin/settings' },
    ];

    const drawer = (
        <Box>
            <Box sx={{ p: 2, textAlign: 'center', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                <Box sx={{
                    width: 80,
                    height: 80,
                    mx: 'auto',
                    mb: 1,
                    borderRadius: '50%',
                    overflow: 'hidden',
                    border: '3px solid rgba(255,255,255,0.2)',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
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
                <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                    پنل مدیریت
                </Typography>
                <Chip
                    label="مدیر سیستم"
                    size="small"
                    color="success"
                    sx={{ mt: 1 }}
                />
            </Box>
            <List sx={{ mt: 2 }}>
                {menuItems.map((item) => (
                    <ListItem key={item.text} disablePadding>
                        <ListItemButton
                            sx={{
                                mx: 1,
                                borderRadius: 2,
                                mb: 0.5,
                                '&:hover': {
                                    backgroundColor: 'rgba(255,255,255,0.1)',
                                }
                            }}
                            onClick={() => navigate(item.path)}
                        >
                            <ListItemIcon sx={{ color: 'white', minWidth: 40 }}>
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText
                                primary={item.text}
                                sx={{
                                    '& .MuiListItemText-primary': {
                                        color: 'white',
                                        fontWeight: 500
                                    }
                                }}
                            />
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>
        </Box>
    );

    return (
        <Box sx={{ display: 'flex' }}>
            <AppBar
                position="fixed"
                sx={{
                    width: { md: `calc(100% - ${drawerWidth}px)` },
                    ml: { md: `${drawerWidth}px` },
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.1)'
                }}
            >
                <Toolbar>
                    <IconButton
                        color="inherit"
                        aria-label="open drawer"
                        edge="start"
                        onClick={handleDrawerToggle}
                        sx={{ mr: 2, display: { md: 'none' } }}
                    >
                        <MenuIcon />
                    </IconButton>

                    <Box sx={{ flexGrow: 1, display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ position: 'relative', mr: 2 }}>
                            <Search sx={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'rgba(255,255,255,0.7)' }} />
                            <input
                                placeholder="جستجو..."
                                style={{
                                    padding: '8px 12px 8px 40px',
                                    border: 'none',
                                    borderRadius: '20px',
                                    backgroundColor: 'rgba(255,255,255,0.2)',
                                    color: 'white',
                                    width: '300px',
                                    outline: 'none'
                                }}
                            />
                        </Box>
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <IconButton color="inherit" onClick={() => setDarkMode(!darkMode)}>
                            {darkMode ? <LightMode /> : <DarkMode />}
                        </IconButton>

                        <NotificationBell />

                        <IconButton
                            color="inherit"
                            onClick={handleProfileMenuOpen}
                        >
                            <AccountCircle />
                        </IconButton>
                    </Box>
                </Toolbar>
            </AppBar>

            <Box
                component="nav"
                sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
            >
                <Drawer
                    variant="temporary"
                    open={mobileOpen}
                    onClose={handleDrawerToggle}
                    ModalProps={{ keepMounted: true }}
                    sx={{
                        display: { xs: 'block', md: 'none' },
                        '& .MuiDrawer-paper': {
                            boxSizing: 'border-box',
                            width: drawerWidth,
                            background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                            color: 'white'
                        },
                    }}
                >
                    {drawer}
                </Drawer>
                <Drawer
                    variant="permanent"
                    sx={{
                        display: { xs: 'none', md: 'block' },
                        '& .MuiDrawer-paper': {
                            boxSizing: 'border-box',
                            width: drawerWidth,
                            background: 'linear-gradient(180deg, #1e293b 0%, #334155 100%)',
                            color: 'white',
                            border: 'none'
                        },
                    }}
                    open
                >
                    {drawer}
                </Drawer>
            </Box>

            <Box
                component="main"
                sx={{
                    flexGrow: 1,
                    p: 3,
                    width: { md: `calc(100% - ${drawerWidth}px)` },
                    mt: 8,
                    background: '#f8fafc',
                    minHeight: '100vh'
                }}
            >
                {children}
            </Box>

            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleProfileMenuClose}
                PaperProps={{
                    sx: {
                        mt: 1,
                        minWidth: 200,
                        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
                        borderRadius: 2
                    }
                }}
            >
                <MenuItem onClick={() => {
                    handleProfileMenuClose();
                    navigate('/admin/settings');
                }}>
                    <Settings sx={{ mr: 1 }} />
                    تنظیمات
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
                    <Logout sx={{ mr: 1 }} />
                    خروج
                </MenuItem>
            </Menu>
        </Box>
    );
};

export default AdminLayout;
