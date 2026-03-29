import warnings

# ------------------------------
# Erase Warnings from urllib3 about OpenSSL when using requests in collectors
# ------------------------------
"""
/Users/nobuyuki/Documents/app/backend/django_api/.venv/lib/python3.9/site-packages/urllib3/__init__.py:35:
 NotOpenSSLWarning: urllib3 v2 only supports OpenSSL 1.1.1+, currently the 'ssl' module is compiled with 
 'LibreSSL 2.8.3'. See: https://github.com/urllib3/urllib3/issues/3020
  warnings.warn(
"""

def setup_warnings() -> None:
    try:
        warnings.filterwarnings(
            "ignore",
            message=r".*urllib3 v2 only supports OpenSSL 1\.1\.1\+.*",
            category=Warning,
        )
    except Exception:
        pass
