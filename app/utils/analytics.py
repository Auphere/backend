"""
PostHog Analytics for Auphere Backend (FastAPI)

Handles server-side analytics tracking:
- API request tracking
- Plan creation/update events
- Search execution events
- Error tracking

Environment modes:
- Development (ENVIRONMENT=development): Console logging only (no PostHog)
- Production (ENVIRONMENT=production): PostHog Cloud tracking

Usage:
    from app.utils.analytics import analytics, track_event
    
    # Track a custom event
    track_event('plan_created', user_id='123', properties={'city': 'Madrid'})
    
    # Use middleware for automatic API tracking
    app.add_middleware(AnalyticsMiddleware)
"""

import logging
import time
from typing import Any, Dict, Optional
from functools import wraps

from app.config import get_settings

# Setup simple logger for development mode
logger = logging.getLogger("analytics")

# PostHog Python SDK (optional in development)
try:
    from posthog import Posthog
    POSTHOG_AVAILABLE = True
except ImportError:
    POSTHOG_AVAILABLE = False
    Posthog = None


# Initialize PostHog client
_posthog_client: Optional["Posthog"] = None
_is_production: bool = False


def _init_analytics() -> None:
    """Initialize analytics based on environment."""
    global _posthog_client, _is_production
    
    settings = get_settings()
    _is_production = settings.environment.lower() == "production"
    
    if not _is_production:
        logger.info("[Analytics] Development mode - console logging enabled")
        return
    
    if not POSTHOG_AVAILABLE:
        logger.warning("[Analytics] PostHog SDK not installed in production")
        return
    
    if not settings.posthog_enabled:
        logger.info("[Analytics] PostHog disabled by configuration")
        return
    
    api_key = settings.posthog_api_key
    if not api_key:
        logger.warning("[Analytics] POSTHOG_API_KEY not set in production")
        return
    
    host = settings.posthog_host
    
    _posthog_client = Posthog(
        api_key=api_key,
        host=host,
        debug=False,
    )
    
    logger.info(f"[Analytics] PostHog initialized: {host}")


def get_posthog_client() -> Optional["Posthog"]:
    """Get or initialize the PostHog client singleton."""
    global _posthog_client
    
    if _posthog_client is None and _is_production:
        _init_analytics()
    
    return _posthog_client


def is_analytics_enabled() -> bool:
    """Check if analytics is configured and enabled."""
    return _is_production and get_posthog_client() is not None


def _log_event_local(event_name: str, user_id: Optional[str], properties: Dict[str, Any]) -> None:
    """Log event to console in development mode."""
    logger.info(f"📊 [Analytics Event] {event_name} | user={user_id or 'anonymous'} | props={properties}")


# =============================================================================
# Core Tracking Functions
# =============================================================================

def identify_user(
    user_id: str,
    properties: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Identify a user with properties.
    
    Args:
        user_id: Unique user identifier (Auth0 sub)
        properties: User properties (email, name, etc.)
    """
    props = properties or {}
    
    # Development: console logging
    if not _is_production:
        logger.debug(f"[Analytics Identify] user={user_id} | props={props}")
        return
    
    # Production: PostHog Cloud
    client = get_posthog_client()
    if not client:
        return
    
    client.identify(
        distinct_id=user_id,
        properties=props,
    )


def track_event(
    event_name: str,
    user_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Track a custom event.
    
    In development: logs to console
    In production: sends to PostHog Cloud
    
    Args:
        event_name: Name of the event
        user_id: User identifier (optional for anonymous events)
        properties: Event properties
    """
    props = properties or {}
    
    # Development: console logging
    if not _is_production:
        _log_event_local(event_name, user_id, props)
        return
    
    # Production: PostHog Cloud
    client = get_posthog_client()
    if not client:
        return
    
    try:
        client.capture(
            distinct_id=user_id or 'anonymous',
            event=event_name,
            properties=props,
        )
    except Exception as e:
        logger.error(f"[Analytics] Failed to capture event: {e}")


def set_user_properties(
    user_id: str,
    properties: Dict[str, Any],
) -> None:
    """
    Set user properties (for profile enrichment).
    
    Args:
        user_id: User identifier
        properties: Properties to set
    """
    # Development: console logging
    if not _is_production:
        logger.debug(f"[Analytics Set Props] user={user_id} | props={properties}")
        return
    
    # Production: PostHog Cloud
    client = get_posthog_client()
    if not client:
        return
    
    client.identify(
        distinct_id=user_id,
        properties=properties,
    )


# =============================================================================
# Auphere-Specific Events
# =============================================================================

def track_api_request(
    endpoint: str,
    method: str,
    user_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
    status_code: int = 200,
    error: Optional[str] = None,
) -> None:
    """Track an API request."""
    track_event(
        'api_request',
        user_id=user_id,
        properties={
            'endpoint': endpoint,
            'method': method,
            'latency_ms': latency_ms,
            'status_code': status_code,
            'error': error,
            'success': error is None,
        },
    )


def track_plan_created(
    plan_id: str,
    user_id: str,
    city: str,
    stops_count: int,
    vibes: Optional[list] = None,
    budget: Optional[float] = None,
) -> None:
    """Track plan creation."""
    track_event(
        'plan_created',
        user_id=user_id,
        properties={
            'plan_id': plan_id,
            'city': city,
            'stops_count': stops_count,
            'vibes': vibes or [],
            'budget': budget,
        },
    )


def track_plan_updated(
    plan_id: str,
    user_id: str,
    edit_type: str,  # 'stop_added', 'stop_removed', 'timing_updated', etc.
    ai_assisted: bool = False,
) -> None:
    """Track plan update."""
    track_event(
        'plan_updated',
        user_id=user_id,
        properties={
            'plan_id': plan_id,
            'edit_type': edit_type,
            'ai_assisted': ai_assisted,
        },
    )


def track_search_executed(
    query: str,
    city: Optional[str] = None,
    results_count: int = 0,
    user_id: Optional[str] = None,
    latency_ms: Optional[float] = None,
) -> None:
    """Track search execution."""
    track_event(
        'search_executed',
        user_id=user_id,
        properties={
            'query': query,
            'city': city,
            'results_count': results_count,
            'latency_ms': latency_ms,
        },
    )


def track_error(
    error_type: str,
    error_message: str,
    user_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """Track an error event."""
    track_event(
        'error_occurred',
        user_id=user_id,
        properties={
            'error_type': error_type,
            'error_message': error_message,
            'context': context or {},
        },
    )


# =============================================================================
# FastAPI Middleware
# =============================================================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track API requests.
    
    Usage:
        from app.utils.analytics import AnalyticsMiddleware
        app.add_middleware(AnalyticsMiddleware)
    """
    
    # Endpoints to skip tracking (health checks, static files, etc.)
    SKIP_PATHS = {
        '/health',
        '/healthz',
        '/ready',
        '/metrics',
        '/favicon.ico',
    }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip certain paths
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)
        
        # Extract user ID from request (if authenticated)
        user_id = None
        if hasattr(request.state, 'user') and request.state.user:
            user_id = request.state.user.get('sub')
        
        # Track request timing
        start_time = time.time()
        error = None
        status_code = 500
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            error = str(e)
            raise
        finally:
            latency_ms = (time.time() - start_time) * 1000
            
            # Track the request (async-safe fire-and-forget)
            try:
                track_api_request(
                    endpoint=request.url.path,
                    method=request.method,
                    user_id=user_id,
                    latency_ms=latency_ms,
                    status_code=status_code,
                    error=error,
                )
            except Exception:
                pass  # Don't let analytics errors break the request


# =============================================================================
# Decorator for Function Tracking
# =============================================================================

def track_function(event_name: str):
    """
    Decorator to track function calls.
    
    Usage:
        @track_function('expensive_operation')
        async def my_function(user_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            result = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                user_id = kwargs.get('user_id')
                
                track_event(
                    event_name,
                    user_id=user_id,
                    properties={
                        'latency_ms': latency_ms,
                        'success': error is None,
                        'error': error,
                    },
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                user_id = kwargs.get('user_id')
                
                track_event(
                    event_name,
                    user_id=user_id,
                    properties={
                        'latency_ms': latency_ms,
                        'success': error is None,
                        'error': error,
                    },
                )
        
        if asyncio_iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def asyncio_iscoroutinefunction(func):
    """Check if function is a coroutine function."""
    import asyncio
    return asyncio.iscoroutinefunction(func)


# =============================================================================
# Shutdown Handler
# =============================================================================

def shutdown_analytics() -> None:
    """
    Flush and shutdown PostHog client.
    Call this on application shutdown.
    """
    global _posthog_client
    if _posthog_client:
        _posthog_client.shutdown()
        _posthog_client = None
        logger.info("[Analytics] PostHog shutdown")


# =============================================================================
# Analytics Object (convenient interface)
# =============================================================================

class Analytics:
    """Convenient interface for analytics tracking."""
    
    @staticmethod
    def is_enabled() -> bool:
        return is_analytics_enabled()
    
    @staticmethod
    def identify(user_id: str, properties: Optional[Dict[str, Any]] = None) -> None:
        identify_user(user_id, properties)
    
    @staticmethod
    def track(event_name: str, user_id: Optional[str] = None, properties: Optional[Dict[str, Any]] = None) -> None:
        track_event(event_name, user_id, properties)
    
    @staticmethod
    def set_properties(user_id: str, properties: Dict[str, Any]) -> None:
        set_user_properties(user_id, properties)
    
    # Auphere-specific
    track_api_request = staticmethod(track_api_request)
    track_plan_created = staticmethod(track_plan_created)
    track_plan_updated = staticmethod(track_plan_updated)
    track_search_executed = staticmethod(track_search_executed)
    track_error = staticmethod(track_error)
    
    @staticmethod
    def shutdown() -> None:
        shutdown_analytics()


analytics = Analytics()


# Initialize on module load
_init_analytics()
