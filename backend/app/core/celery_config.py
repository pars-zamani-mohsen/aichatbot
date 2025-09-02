from app.config import settings

broker_url = settings.REDIS_URL
result_backend = settings.REDIS_URL

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "Asia/Tehran"
enable_utc = True 