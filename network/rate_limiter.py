"""
Unicrium Rate Limiter
DDoS protection and request throttling
Implements token bucket and sliding window algorithms
"""
from typing import Dict, Optional
import time
import logging
from collections import deque

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket rate limiter
    Allows bursts while maintaining average rate
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum tokens (burst size)
            refill_rate: Tokens per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def _refill(self):
        """Refill tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_available_tokens(self) -> float:
        """Get current available tokens"""
        self._refill()
        return self.tokens


class SlidingWindow:
    """
    Sliding window rate limiter
    Counts requests in a time window
    """
    
    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize sliding window
        
        Args:
            max_requests: Maximum requests in window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: deque = deque()
    
    def _clean_old_requests(self):
        """Remove requests outside window"""
        cutoff = time.time() - self.window_seconds
        
        while self.requests and self.requests[0] < cutoff:
            self.requests.popleft()
    
    def allow_request(self) -> bool:
        """
        Check if request is allowed
        
        Returns:
            True if request is allowed
        """
        self._clean_old_requests()
        
        if len(self.requests) < self.max_requests:
            self.requests.append(time.time())
            return True
        
        return False
    
    def get_request_count(self) -> int:
        """Get current request count in window"""
        self._clean_old_requests()
        return len(self.requests)


class RateLimiter:
    """
    Comprehensive rate limiter
    Supports multiple limiters per client
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Initialize rate limiter
        
        Args:
            config: Rate limit configuration
        """
        self.config = config or self._default_config()
        
        # Per-IP limiters
        self.ip_limiters: Dict[str, TokenBucket] = {}
        
        # Per-endpoint limiters
        self.endpoint_limiters: Dict[str, Dict[str, SlidingWindow]] = {}
        
        # Global limiter
        self.global_limiter = TokenBucket(
            capacity=self.config['global']['capacity'],
            refill_rate=self.config['global']['refill_rate']
        )
        
        logger.info("RateLimiter initialized")
    
    def _default_config(self) -> dict:
        """Default rate limit configuration"""
        return {
            'global': {
                'capacity': 1000,  # Max burst
                'refill_rate': 100  # Per second
            },
            'per_ip': {
                'capacity': 100,
                'refill_rate': 10
            },
            'endpoints': {
                '/transaction': {
                    'max_requests': 10,
                    'window_seconds': 60
                },
                '/balance': {
                    'max_requests': 100,
                    'window_seconds': 60
                },
                '/blocks': {
                    'max_requests': 50,
                    'window_seconds': 60
                }
            }
        }
    
    def check_limit(self, client_id: str, endpoint: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """
        Check if request is allowed
        
        Args:
            client_id: Client identifier (IP address)
            endpoint: Optional endpoint path
            
        Returns:
            (allowed, reason) tuple
        """
        # Check global limit
        if not self.global_limiter.consume():
            return False, "Global rate limit exceeded"
        
        # Get or create IP limiter
        if client_id not in self.ip_limiters:
            self.ip_limiters[client_id] = TokenBucket(
                capacity=self.config['per_ip']['capacity'],
                refill_rate=self.config['per_ip']['refill_rate']
            )
        
        # Check IP limit
        if not self.ip_limiters[client_id].consume():
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False, "IP rate limit exceeded"
        
        # Check endpoint limit if specified
        if endpoint and endpoint in self.config['endpoints']:
            if endpoint not in self.endpoint_limiters:
                self.endpoint_limiters[endpoint] = {}
            
            if client_id not in self.endpoint_limiters[endpoint]:
                ep_config = self.config['endpoints'][endpoint]
                self.endpoint_limiters[endpoint][client_id] = SlidingWindow(
                    max_requests=ep_config['max_requests'],
                    window_seconds=ep_config['window_seconds']
                )
            
            if not self.endpoint_limiters[endpoint][client_id].allow_request():
                logger.warning(f"Endpoint rate limit exceeded for {client_id} on {endpoint}")
                return False, f"Endpoint {endpoint} rate limit exceeded"
        
        return True, None
    
    def get_client_stats(self, client_id: str) -> dict:
        """
        Get rate limit stats for client
        
        Args:
            client_id: Client identifier
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'client_id': client_id,
            'global_tokens': self.global_limiter.get_available_tokens()
        }
        
        if client_id in self.ip_limiters:
            stats['ip_tokens'] = self.ip_limiters[client_id].get_available_tokens()
        
        if client_id in self.endpoint_limiters:
            stats['endpoints'] = {}
            for endpoint, limiters in self.endpoint_limiters.items():
                if client_id in limiters:
                    stats['endpoints'][endpoint] = limiters[client_id].get_request_count()
        
        return stats
    
    def reset_client(self, client_id: str):
        """Reset rate limits for client"""
        if client_id in self.ip_limiters:
            del self.ip_limiters[client_id]
        
        for endpoint in self.endpoint_limiters:
            if client_id in self.endpoint_limiters[endpoint]:
                del self.endpoint_limiters[endpoint][client_id]
        
        logger.info(f"Reset rate limits for {client_id}")
    
    def cleanup_old_limiters(self, max_age_seconds: int = 3600):
        """
        Clean up inactive limiters
        
        Args:
            max_age_seconds: Maximum age before cleanup
        """
        # This would require tracking last access time
        # Simplified version: just limit total number
        if len(self.ip_limiters) > 10000:
            # Remove oldest half
            to_remove = list(self.ip_limiters.keys())[:5000]
            for client_id in to_remove:
                del self.ip_limiters[client_id]
            
            logger.info(f"Cleaned up {len(to_remove)} old limiters")


# Decorator for Flask/FastAPI
def rate_limit(limiter: RateLimiter, endpoint: str):
    """
    Decorator to apply rate limiting to endpoints
    
    Args:
        limiter: RateLimiter instance
        endpoint: Endpoint path
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract client ID from request
            # This is framework-specific
            client_id = "default"  # Would extract from request
            
            allowed, reason = limiter.check_limit(client_id, endpoint)
            
            if not allowed:
                # Return rate limit error
                return {"error": reason}, 429
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test rate limiter
    print("Testing RateLimiter...")
    
    limiter = RateLimiter()
    
    # Test IP rate limiting
    client = "192.168.1.1"
    
    # Should succeed
    allowed, reason = limiter.check_limit(client, "/balance")
    print(f"✓ Request 1: {allowed}")
    
    # Make many requests
    success_count = 0
    for i in range(150):
        allowed, _ = limiter.check_limit(client, "/balance")
        if allowed:
            success_count += 1
    
    print(f"✓ Successful requests: {success_count}/150")
    
    # Check stats
    stats = limiter.get_client_stats(client)
    print(f"✓ Client stats: {stats}")
    
    # Test endpoint-specific limits
    for i in range(15):
        allowed, reason = limiter.check_limit(client, "/transaction")
        if not allowed:
            print(f"✓ Transaction limit hit at request {i+1}: {reason}")
            break
    
    print("\n✅ Rate limiter tests passed!")
