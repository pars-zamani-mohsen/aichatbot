"""optimize database indexes

Revision ID: optimize_indexes_001
Revises: 3012d17
Create Date: 2025-01-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'optimize_indexes_001'
down_revision = '3012d17'
branch_labels = None
depends_on = None


def upgrade():
    """اضافه کردن index های بهینه برای بهبود عملکرد"""
    
    # Index های جدول users
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_last_login', 'users', ['last_login'])
    
    # Index های جدول websites
    op.create_index('idx_websites_owner_id', 'websites', ['owner_id'])
    op.create_index('idx_websites_status', 'websites', ['status'])
    op.create_index('idx_websites_url', 'websites', ['url'])
    op.create_index('idx_websites_collection_name', 'websites', ['collection_name'])
    op.create_index('idx_websites_created_at', 'websites', ['created_at'])
    op.create_index('idx_websites_updated_at', 'websites', ['updated_at'])
    
    # Composite index برای جستجوی وب‌سایت‌ها
    op.create_index('idx_websites_owner_status', 'websites', ['owner_id', 'status'])
    op.create_index('idx_websites_status_created', 'websites', ['status', 'created_at'])
    
    # Index های جدول chats
    op.create_index('idx_chats_website_id', 'chats', ['website_id'])
    op.create_index('idx_chats_session_id', 'chats', ['session_id'])
    op.create_index('idx_chats_created_at', 'chats', ['created_at'])
    op.create_index('idx_chats_updated_at', 'chats', ['updated_at'])
    
    # Composite index برای جستجوی چت‌ها
    op.create_index('idx_chats_website_created', 'chats', ['website_id', 'created_at'])
    op.create_index('idx_chats_session_created', 'chats', ['session_id', 'created_at'])
    
    # Index های جدول messages
    op.create_index('idx_messages_chat_id', 'messages', ['chat_id'])
    op.create_index('idx_messages_role', 'messages', ['role'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    
    # Composite index برای جستجوی پیام‌ها
    op.create_index('idx_messages_chat_created', 'messages', ['chat_id', 'created_at'])
    op.create_index('idx_messages_role_created', 'messages', ['role', 'created_at'])
    
    # Index های جدول user_settings
    op.create_index('idx_user_settings_user_id', 'user_settings', ['user_id'])
    op.create_index('idx_user_settings_created_at', 'user_settings', ['created_at'])
    
    # Index های جدول system_settings
    op.create_index('idx_system_settings_key', 'system_settings', ['key'], unique=True)
    op.create_index('idx_system_settings_updated_at', 'system_settings', ['updated_at'])
    
    # Index های جدول notifications
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_type', 'notifications', ['type'])
    op.create_index('idx_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('idx_notifications_created_at', 'notifications', ['created_at'])
    
    # Composite index برای جستجوی اعلان‌ها
    op.create_index('idx_notifications_user_read', 'notifications', ['user_id', 'is_read'])
    op.create_index('idx_notifications_user_created', 'notifications', ['user_id', 'created_at'])
    
    # Index های جدول email_archive
    op.create_index('idx_email_archive_user_id', 'email_archive', ['user_id'])
    op.create_index('idx_email_archive_type', 'email_archive', ['type'])
    op.create_index('idx_email_archive_created_at', 'email_archive', ['created_at'])
    
    # Partial index برای اعلان‌های خوانده نشده (PostgreSQL specific)
    op.execute("""
        CREATE INDEX idx_notifications_unread 
        ON notifications (user_id, created_at) 
        WHERE is_read = false
    """)
    
    # Partial index برای وب‌سایت‌های آماده
    op.execute("""
        CREATE INDEX idx_websites_ready 
        ON websites (owner_id, created_at) 
        WHERE status = 'ready'
    """)
    
    # Partial index برای چت‌های فعال
    op.execute("""
        CREATE INDEX idx_chats_active 
        ON chats (website_id, created_at) 
        WHERE updated_at > created_at
    """)


def downgrade():
    """حذف index های اضافه شده"""
    
    # حذف partial indexes
    op.execute("DROP INDEX IF EXISTS idx_notifications_unread")
    op.execute("DROP INDEX IF EXISTS idx_websites_ready")
    op.execute("DROP INDEX IF EXISTS idx_chats_active")
    
    # حذف composite indexes
    op.drop_index('idx_websites_owner_status', 'websites')
    op.drop_index('idx_websites_status_created', 'websites')
    op.drop_index('idx_chats_website_created', 'chats')
    op.drop_index('idx_chats_session_created', 'chats')
    op.drop_index('idx_messages_chat_created', 'messages')
    op.drop_index('idx_messages_role_created', 'messages')
    op.drop_index('idx_notifications_user_read', 'notifications')
    op.drop_index('idx_notifications_user_created', 'notifications')
    
    # حذف single indexes
    op.drop_index('idx_users_email', 'users')
    op.drop_index('idx_users_role', 'users')
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_last_login', 'users')
    
    op.drop_index('idx_websites_owner_id', 'websites')
    op.drop_index('idx_websites_status', 'websites')
    op.drop_index('idx_websites_url', 'websites')
    op.drop_index('idx_websites_collection_name', 'websites')
    op.drop_index('idx_websites_created_at', 'websites')
    op.drop_index('idx_websites_updated_at', 'websites')
    
    op.drop_index('idx_chats_website_id', 'chats')
    op.drop_index('idx_chats_session_id', 'chats')
    op.drop_index('idx_chats_created_at', 'chats')
    op.drop_index('idx_chats_updated_at', 'chats')
    
    op.drop_index('idx_messages_chat_id', 'messages')
    op.drop_index('idx_messages_role', 'messages')
    op.drop_index('idx_messages_created_at', 'messages')
    
    op.drop_index('idx_user_settings_user_id', 'user_settings')
    op.drop_index('idx_user_settings_created_at', 'user_settings')
    
    op.drop_index('idx_system_settings_key', 'system_settings')
    op.drop_index('idx_system_settings_updated_at', 'system_settings')
    
    op.drop_index('idx_notifications_user_id', 'notifications')
    op.drop_index('idx_notifications_type', 'notifications')
    op.drop_index('idx_notifications_is_read', 'notifications')
    op.drop_index('idx_notifications_created_at', 'notifications')
    
    op.drop_index('idx_email_archive_user_id', 'email_archive')
    op.drop_index('idx_email_archive_type', 'email_archive')
    op.drop_index('idx_email_archive_created_at', 'email_archive')
