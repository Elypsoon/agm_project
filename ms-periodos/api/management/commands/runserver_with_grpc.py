"""
Management command to run gRPC server alongside Django
"""
import threading
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from src.grpc.server import serve
import asyncio

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run gRPC server alongside Django development server'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only-grpc',
            action='store_true',
            help='Run only the gRPC server without Django'
        )

    def handle(self, *args, **options):
        if options.get('only_grpc'):
            self.stdout.write(self.style.SUCCESS('Starting gRPC server only...'))
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(serve())
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('gRPC server stopped.'))
        else:
            # Start gRPC server in a background thread
            self.stdout.write(self.style.SUCCESS('Starting gRPC server in background...'))
            
            def run_grpc():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(serve())
                except Exception as e:
                    logger.error(f"Error in gRPC server: {e}")

            grpc_thread = threading.Thread(target=run_grpc, daemon=True)
            grpc_thread.start()
            self.stdout.write(self.style.SUCCESS('gRPC server started in background'))

            # Run Django development server
            self.stdout.write(self.style.SUCCESS('Starting Django development server...'))
            call_command('runserver', '0.0.0.0:3002')
