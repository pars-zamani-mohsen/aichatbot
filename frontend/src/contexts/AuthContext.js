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

    // تابع کمکی برای پاک کردن localStorage
    const clearCorruptedData = (reason = 'corrupted_data') => {
        console.warn(`Clearing localStorage due to: ${reason}`);
        localStorage.removeItem('userInfo');
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        setUser(null);
    };

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const userInfoStr = localStorage.getItem('userInfo');
                if (userInfoStr && userInfoStr.trim() !== '') {
                    // بررسی اینکه آیا رشته خالی یا null نیست
                    if (userInfoStr === 'null' || userInfoStr === 'undefined') {
                        clearCorruptedData('null_or_undefined_userInfo');
                    } else {
                        const userInfo = JSON.parse(userInfoStr);
                        // بررسی اینکه آیا userInfo یک object معتبر است
                        if (userInfo && typeof userInfo === 'object') {
                            setUser(userInfo);
                        } else {
                            clearCorruptedData('invalid_userInfo_object');
                        }
                    }
                } else {
                    // اگر userInfo وجود ندارد، token را هم پاک کن
                    clearCorruptedData('missing_userInfo');
                }
            } catch (error) {
                console.error('Error parsing userInfo from localStorage:', error);
                console.log('Corrupted userInfo string:', localStorage.getItem('userInfo'));
                clearCorruptedData('json_parse_error');
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
        clearCorruptedData('manual_logout');
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
