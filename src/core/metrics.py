from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics Definitions
MESSAGES_PROCESSED_TOTAL = Counter(
    'messages_processed_total', 
    'Total number of messages processed',
    ['status', 'type']
)

MESSAGE_LATENCY_SECONDS = Histogram(
    'message_latency_seconds',
    'Time spent processing messages',
    ['operation']
)

ERRORS_TOTAL = Counter(
    'errors_total',
    'Total number of errors',
    ['type']
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections/requests'
)

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        ACTIVE_CONNECTIONS.inc()
        start_time = time.time()
        
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            ERRORS_TOTAL.labels(type=type(e).__name__).inc()
            raise e
        finally:
            ACTIVE_CONNECTIONS.dec()
            duration = time.time() - start_time
            MESSAGE_LATENCY_SECONDS.labels(operation=scope['path']).observe(duration)
