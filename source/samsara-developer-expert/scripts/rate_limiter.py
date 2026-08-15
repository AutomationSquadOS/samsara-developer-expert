#!/usr/bin/env python3
"""
Samsara API Rate Limiter

Production-ready rate limiting for Samsara API requests.
Enforces per-second and per-minute limits with exponential backoff.
"""

import time
from collections import deque
from typing import Optional


class SamsaraRateLimiter:
    """
    Rate limiter for Samsara API requests.
    
    Enforces:
    - Per-second limit (default: 5 req/sec)
    - Per-minute limit (default: 300 req/min)
    """
    
    def __init__(
        self,
        per_second_limit: int = 5,
        per_minute_limit: int = 300
    ):
        self.per_second_limit = per_second_limit
        self.per_minute_limit = per_minute_limit
        self.request_times = deque()
    
    def throttle(self) -> None:
        """
        Block if necessary to respect rate limits.
        Call this before making each API request.
        """
        now = time.time()
        
        # Remove requests older than 1 minute
        while self.request_times and now - self.request_times[0] > 60:
            self.request_times.popleft()
        
        # Check per-second limit
        recent_requests = sum(
            1 for t in self.request_times 
            if now - t < 1.0
        )
        
        if recent_requests >= self.per_second_limit:
            # Find oldest request in last second
            for t in self.request_times:
                if now - t < 1.0:
                    wait_time = 1.0 - (now - t) + 0.05  # Add 50ms buffer
                    time.sleep(wait_time)
                    break
        
        # Check per-minute limit
        if len(self.request_times) >= self.per_minute_limit:
            oldest = self.request_times[0]
            wait_time = 60.0 - (now - oldest) + 0.1  # Add 100ms buffer
            time.sleep(wait_time)
        
        # Record this request
        self.request_times.append(time.time())
    
    def reset(self) -> None:
        """Reset the rate limiter state."""
        self.request_times.clear()


class ExponentialBackoff:
    """
    Exponential backoff for retrying failed requests.
    """
    
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 30.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def wait(self, attempt: int, retry_after: Optional[float] = None) -> None:
        """
        Wait for the appropriate backoff time.
        
        Args:
            attempt: Current retry attempt (0-indexed)
            retry_after: Optional Retry-After header value in seconds
        """
        if retry_after:
            time.sleep(retry_after)
            return
        
        # Exponential backoff: base_delay * 2^attempt
        delay = min(
            self.base_delay * (2 ** attempt),
            self.max_delay
        )
        
        # Add jitter (0-1000ms) to prevent thundering herd
        import random
        jitter = random.random()
        
        time.sleep(delay + jitter)


# Example usage
if __name__ == "__main__":
    import requests
    
    # Initialize rate limiter
    limiter = SamsaraRateLimiter(per_second_limit=5, per_minute_limit=300)
    backoff = ExponentialBackoff(max_retries=5)
    
    # Example: Fetch routes with rate limiting
    api_token = "YOUR_API_TOKEN"
    base_url = "https://api.samsara.com"
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    for attempt in range(backoff.max_retries):
        try:
            # Wait for rate limit
            limiter.throttle()
            
            # Make request
            response = requests.get(
                f"{base_url}/fleet/routes",
                headers=headers
            )
            
            # Check for rate limit
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                print(f"Rate limited, waiting {retry_after}s...")
                backoff.wait(attempt, retry_after)
                continue
            
            # Success
            response.raise_for_status()
            routes = response.json()
            print(f"Fetched {len(routes.get('data', []))} routes")
            break
            
        except requests.exceptions.RequestException as e:
            print(f"Request failed (attempt {attempt + 1}): {e}")
            if attempt < backoff.max_retries - 1:
                backoff.wait(attempt)
            else:
                raise
