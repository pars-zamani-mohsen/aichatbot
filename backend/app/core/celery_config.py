from app.core.config import settings

broker_url = f"redis://localhost:6380/0"
result_backend = f"redis://localhost:6380/0"

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "Asia/Tehran"
enable_utc = True 