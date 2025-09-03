import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const userInfoStr = localStorage.getItem('userInfo');
                if (userInfoStr) {
                    const userInfo = JSON.parse(userInfoStr);
                    setUser(userInfo);
                }
            } catch (error) {
                console.error('Error parsing userInfo from localStorage:', error);
                // پاک کردن داده‌های خراب
                localStorage.removeItem('userInfo');
                localStorage.removeItem('token');
                localStorage.removeItem('refresh_token');
            }
        }
        setLoading(false);
    }, []);

    // اضافه کردن event listener برای logout خودکار
    useEffect(() => {
        const handleForceLogout = (event) => {
            console.log('Force logout triggered:', event.detail);
            logout();
            // redirect به صفحه login
            window.location.href = '/login';
        };

        window.addEventListener('forceLogout', handleForceLogout);

        return () => {
            window.removeEventListener('forceLogout', handleForceLogout);
        };
    }, []);

    const login = (userData) => {
        setUser(userData);
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('userInfo');
    };

    const value = {
        user,
        loading,
        login,
        logout,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};
