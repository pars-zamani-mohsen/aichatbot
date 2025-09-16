import { useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

/**
 * Hook برای مدیریت خطاهای API و logout خودکار
 */
export const useApiError = () => {
    const { logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const handleForceLogout = (event) => {
            console.log('Force logout triggered from useApiError:', event.detail);

            // logout کردن کاربر
            logout();

            // نمایش پیام به کاربر
            if (event.detail?.reason === 'token_expired') {
                alert('جلسه شما منقضی شده است. لطفاً دوباره وارد شوید.');
            } else {
                alert('خطا در احراز هویت. لطفاً دوباره وارد شوید.');
            }

            // redirect به صفحه login
            navigate('/login');
        };

        // اضافه کردن event listener
        window.addEventListener('forceLogout', handleForceLogout);

        // cleanup
        return () => {
            window.removeEventListener('forceLogout', handleForceLogout);
        };
    }, [logout, navigate]);

    /**
     * تابع برای handle کردن خطاهای API
     */
    const handleApiError = (error) => {
        if (error.response?.status === 401) {
            // خطای 401 - کاربر را logout کن
            logout();
            alert('جلسه شما منقضی شده است. لطفاً دوباره وارد شوید.');
            navigate('/login');
            return true; // خطا handle شده
        }

        if (error.response?.status === 429 || error.status === 429) {
            // خطای 429 - Rate Limit
            alert('تعداد درخواست‌ها بیش از حد مجاز است. لطفاً چند دقیقه صبر کنید و دوباره تلاش کنید.');
            return true; // خطا handle شده
        }

        // خطاهای دیگر
        console.error('API Error:', error);
        return false; // خطا handle نشده
    };

    return { handleApiError };
};
