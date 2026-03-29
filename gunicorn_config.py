"""
Gunicorn configuration file for production deployment.
"""
import multiprocessing
import os

# Server socket
bind = f"{os.environ.get('HOST', '0.0.0.0')}:{os.environ.get('PORT', '5000')}"
backlog = 2048

# Worker processes
# Optimized for Render free tier (512MB RAM)
# For paid plans, you can increase workers
cpu_count = multiprocessing.cpu_count()
workers = max(2, min(cpu_count * 2 + 1, 4))  # Cap at 4 for free tier
worker_class = 'gevent'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'swasthya-sampark'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Preload app for better performance
preload_app = True

# Worker timeout
graceful_timeout = 30

# Max requests per worker (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

