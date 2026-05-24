#!/usr/bin/env python
"""
Startup script that runs both Django and gRPC server.
For production use with gunicorn + separate gRPC process.
"""
import os
import sys
import threading
import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

def run_grpc_server():
    """Run gRPC server in a background thread."""
    try:
        from src.grpc.server import serve
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(serve())
    except Exception as e:
        logger.error(f"Error running gRPC server: {e}", exc_info=True)

def run_django_server():
    """Run Django development server."""
    from django.core.management import call_command
    try:
        call_command('runserver', '0.0.0.0:3002')
    except Exception as e:
        logger.error(f"Error running Django server: {e}", exc_info=True)

if __name__ == '__main__':
    # Start gRPC server in background thread
    logger.info("Starting gRPC server in background...")
    grpc_thread = threading.Thread(target=run_grpc_server, daemon=True)
    grpc_thread.start()
    
    # Give gRPC server a moment to start
    time.sleep(1)
    
    # Run Django server in main thread
    logger.info("Starting Django development server...")
    run_django_server()
