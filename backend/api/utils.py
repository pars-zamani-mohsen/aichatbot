from typing import Set

def get_allowed_extensions() -> Set[str]:
    """Return set of allowed file extensions"""
    return {
        '.jpg', '.jpeg', '.png', '.gif',
        '.webp', '.svg', '.ico', '.bmp', '.tiff'
    }

def is_allowed_file(filename: str) -> bool:
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in get_allowed_extensions()