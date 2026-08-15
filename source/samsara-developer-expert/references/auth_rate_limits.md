# Authentication & Rate Limiting

Complete guide to Samsara API authentication and rate limit management.

## Authentication

### API Tokens (Recommended)

Create and manage API tokens in Samsara Dashboard:

1. Navigate to **Settings** → **API Tokens**
2. Click **Create Token**
3. Set permissions (scopes) for the token
4. **Copy token immediately** - it's shown only once
5. Store securely in environment variables or secrets manager

### Token Usage

```typescript
const headers = {
  'Authorization': `Bearer ${API_TOKEN}`,
  'Content-Type': 'application/json'
};

const response = await fetch('https://api.samsara.com/fleet/routes', {
  headers
});
```

### Token Scopes

Tokens have granular permissions. Request only what you need:

- `Read Vehicles`, `Write Vehicles`
- `Read Routes`, `Write Routes`, `Create Routes`
- `Read Drivers`, `Write Drivers`
- `Read Safety Events`
- `Read HOS Logs`

### Token Security Best Practices

1. **Never commit tokens to version control**
2. **Use environment variables**:
   ```bash
   SAMSARA_API_TOKEN=your_token_here
   ```
3. **Rotate tokens periodically** (every 90 days)
4. **Use separate tokens** for development, staging, production
5. **Revoke unused tokens** immediately
6. **Monitor token usage** in dashboard

### OAuth 2.0 (For Third-Party Apps)

For marketplace applications, use OAuth 2.0:

```typescript
// Step 1: Redirect user to authorize
const authUrl = 'https://api.samsara.com/oauth2/authorize' +
  `?client_id=${CLIENT_ID}` +
  `&redirect_uri=${REDIRECT_URI}` +
  `&response_type=code` +
  `&scope=read:routes write:routes`;

// Step 2: Exchange code for token
const tokenResponse = await fetch('https://api.samsara.com/oauth2/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authorizationCode,
    client_id: CLIENT_ID,
    client_secret: CLIENT_SECRET,
    redirect_uri: REDIRECT_URI
  })
});

const { access_token, refresh_token } = await tokenResponse.json();
```

## Rate Limiting

### Three-Tier Structure

Samsara enforces rate limits at three levels:

1. **Per-Token**: 150 requests/second
2. **Per-Organization**: 200 requests/second (aggregate across all tokens)
3. **Endpoint-Specific**: Varies by endpoint

### Endpoint-Specific Limits

| Endpoint Category | Rate Limit |
|-------------------|------------|
| Fleet Vehicles (List) | 25 req/sec |
| Fleet Vehicles (Stats) | 50 req/sec |
| Fleet Locations | 25 req/sec |
| Fleet Locations (Feed) | 50 req/sec |
| Safety Events | 5 req/sec |
| HOS Logs | 5 req/sec |
| Routes | 25 req/sec |

### Rate Limit Headers

Samsara returns rate limit info in response headers:

```
X-RateLimit-Limit: 150        // Max requests per window
X-RateLimit-Remaining: 143    // Requests remaining
X-RateLimit-Reset: 1675444860 // Unix timestamp when limit resets
```

### 429 Rate Limit Response

When rate limited, Samsara returns:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 5

{
  "error": {
    "type": "RateLimitError",
    "message": "Rate limit exceeded"
  }
}
```

**Always respect the `Retry-After` header.**

## Rate Limiter Implementation

### Production-Ready Rate Limiter

```typescript
class SamsaraRateLimiter {
  private requestTimes: number[] = [];
  private perSecondLimit = 5;    // Conservative limit
  private perMinuteLimit = 300;
  
  async throttle(): Promise<void> {
    const now = Date.now();
    
    // Remove requests older than 1 minute
    this.requestTimes = this.requestTimes.filter(
      time => now - time < 60000
    );
    
    // Check per-second limit (last 1 second)
    const recentRequests = this.requestTimes.filter(
      time => now - time < 1000
    );
    
    if (recentRequests.length >= this.perSecondLimit) {
      const oldestRecent = Math.min(...recentRequests);
      const waitTime = 1000 - (now - oldestRecent);
      await this.sleep(waitTime + 50); // Add 50ms buffer
    }
    
    // Check per-minute limit
    if (this.requestTimes.length >= this.perMinuteLimit) {
      const oldestRequest = Math.min(...this.requestTimes);
      const waitTime = 60000 - (now - oldestRequest);
      await this.sleep(waitTime + 100); // Add 100ms buffer
    }
    
    // Record this request
    this.requestTimes.push(now);
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  reset(): void {
    this.requestTimes = [];
  }
}
```

### Exponential Backoff with Jitter

```typescript
async function makeRequestWithRetry(
  url: string,
  options: RequestInit,
  maxRetries = 5
): Promise<Response> {
  let lastError: Error;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        const retryAfter = parseInt(
          response.headers.get('Retry-After') || '1'
        );
        
        // Exponential backoff: 2^attempt seconds
        const backoff = Math.min(
          1000 * Math.pow(2, attempt),
          30000  // Cap at 30 seconds
        );
        
        // Add jitter (random 0-1000ms) to prevent thundering herd
        const jitter = Math.random() * 1000;
        
        const waitTime = Math.max(
          retryAfter * 1000,
          backoff
        ) + jitter;
        
        console.log(`Rate limited, waiting ${waitTime}ms before retry ${attempt + 1}`);
        await sleep(waitTime);
        continue;
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return response;
      
    } catch (error) {
      lastError = error;
      if (attempt === maxRetries - 1) break;
      
      // Exponential backoff for network errors
      const backoff = Math.min(1000 * Math.pow(2, attempt), 30000);
      await sleep(backoff);
    }
  }
  
  throw new Error(`Max retries (${maxRetries}) exceeded: ${lastError.message}`);
}
```

### Request Queue Pattern

```typescript
class RequestQueue {
  private queue: Array<() => Promise<any>> = [];
  private processing = false;
  private rateLimiter = new SamsaraRateLimiter();
  
  async enqueue<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push(async () => {
        try {
          const result = await request();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      
      this.processQueue();
    });
  }
  
  private async processQueue() {
    if (this.processing || this.queue.length === 0) return;
    
    this.processing = true;
    
    while (this.queue.length > 0) {
      const request = this.queue.shift();
      
      await this.rateLimiter.throttle();
      await request();
    }
    
    this.processing = false;
  }
}

// Usage
const queue = new RequestQueue();

// All requests go through queue and are automatically rate-limited
const route = await queue.enqueue(() => 
  fetch('/fleet/routes/123')
);
```

### Batch Request Handler

```typescript
async function batchRequests<T>(
  requests: Array<() => Promise<T>>,
  concurrency = 5
): Promise<T[]> {
  const results: T[] = [];
  const rateLimiter = new SamsaraRateLimiter();
  
  for (let i = 0; i < requests.length; i += concurrency) {
    const batch = requests.slice(i, i + concurrency);
    
    const batchResults = await Promise.all(
      batch.map(async (request) => {
        await rateLimiter.throttle();
        return await request();
      })
    );
    
    results.push(...batchResults);
    
    // Small delay between batches
    if (i + concurrency < requests.length) {
      await sleep(100);
    }
  }
  
  return results;
}

// Usage
const routeRequests = routeIds.map(id => 
  () => fetch(`/fleet/routes/${id}`)
);

const routes = await batchRequests(routeRequests, 5);
```

## Monitoring Rate Limits

### Track Usage

```typescript
class RateLimitMonitor {
  private metrics = {
    totalRequests: 0,
    rateLimited: 0,
    retries: 0,
    successRate: 0
  };
  
  recordRequest(status: number, retryCount: number = 0) {
    this.metrics.totalRequests++;
    
    if (status === 429) {
      this.metrics.rateLimited++;
    }
    
    if (retryCount > 0) {
      this.metrics.retries += retryCount;
    }
    
    this.metrics.successRate = 
      (this.metrics.totalRequests - this.metrics.rateLimited) / 
      this.metrics.totalRequests;
  }
  
  getMetrics() {
    return {
      ...this.metrics,
      averageRetries: this.metrics.retries / this.metrics.totalRequests
    };
  }
  
  shouldAlert(): boolean {
    // Alert if >10% of requests are rate limited
    return this.metrics.successRate < 0.9;
  }
}
```

### Alert on High Rate Limit Usage

```typescript
async function monitorRateLimits() {
  const monitor = new RateLimitMonitor();
  
  // Check every minute
  setInterval(() => {
    const metrics = monitor.getMetrics();
    
    if (metrics.rateLimited > 100) {
      sendAlert({
        message: 'High rate limit usage',
        rateLimited: metrics.rateLimited,
        successRate: `${(metrics.successRate * 100).toFixed(2)}%`
      });
    }
  }, 60000);
}
```

## Best Practices

### 1. Use Conservative Limits

Set your client-side rate limits **below** Samsara's limits:

```typescript
// Samsara allows 150 req/sec, but use 100 for safety
const rateLimiter = new SamsaraRateLimiter();
rateLimiter.perSecondLimit = 100;
```

### 2. Implement Circuit Breaker

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure: number | null = null;
  private state: 'closed' | 'open' | 'half-open' = 'closed';
  private threshold = 5;
  private timeout = 60000; // 1 minute
  
  async execute<T>(request: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure! > this.timeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is open');
      }
    }
    
    try {
      const result = await request();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  private onSuccess() {
    this.failures = 0;
    this.state = 'closed';
  }
  
  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    
    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }
}
```

### 3. Cache Frequently Accessed Data

```typescript
class CachedSamsaraClient {
  private cache = new Map<string, { data: any, expires: number }>();
  private ttl = 60000; // 1 minute
  
  async getRoute(id: string): Promise<any> {
    const cached = this.cache.get(id);
    
    if (cached && Date.now() < cached.expires) {
      return cached.data;
    }
    
    const data = await fetch(`/fleet/routes/${id}`);
    
    this.cache.set(id, {
      data,
      expires: Date.now() + this.ttl
    });
    
    return data;
  }
}
```

### 4. Use Feeds Instead of Polling

❌ **Bad**: Repeatedly calling snapshot endpoints
```typescript
// Wastes rate limit quota
setInterval(async () => {
  const vehicles = await fetch('/fleet/vehicles/stats');
}, 5000);
```

✅ **Good**: Use feed endpoints
```typescript
// Efficient, uses cursor-based updates
let cursor = null;
setInterval(async () => {
  const response = await fetch('/fleet/vehicles/stats/feed', {
    params: cursor ? { after: cursor } : {}
  });
  cursor = response.pagination.endCursor;
}, 5000);
```

### 5. Batch Operations

❌ **Bad**: Sequential requests
```typescript
for (const id of routeIds) {
  await fetch(`/fleet/routes/${id}`);
}
```

✅ **Good**: Parallel with rate limiting
```typescript
await batchRequests(
  routeIds.map(id => () => fetch(`/fleet/routes/${id}`)),
  5 // Concurrency
);
```

## Troubleshooting

### Consistently Hitting Rate Limits

**Symptoms**: Frequent 429 responses

**Solutions**:
1. Reduce polling frequency
2. Use feed endpoints instead of snapshots
3. Implement caching
4. Batch requests more conservatively
5. Review and optimize query patterns

### Sporadic Rate Limit Errors

**Symptoms**: Occasional 429s during bursts

**Solutions**:
1. Implement request queue
2. Add exponential backoff
3. Distribute requests over time
4. Use circuit breaker pattern

### Organization-Wide Rate Limits

**Symptoms**: 429s despite low per-token usage

**Cause**: Multiple tokens/apps sharing org limit (200 req/sec)

**Solutions**:
1. Coordinate across applications
2. Implement shared rate limiter
3. Prioritize critical operations
4. Contact Samsara to increase limits

## Environment-Specific Configuration

```typescript
const config = {
  development: {
    rateLimit: {
      perSecond: 2,
      perMinute: 100
    },
    retryConfig: {
      maxRetries: 3,
      backoffMultiplier: 1.5
    }
  },
  production: {
    rateLimit: {
      perSecond: 100,
      perMinute: 5000
    },
    retryConfig: {
      maxRetries: 5,
      backoffMultiplier: 2
    }
  }
};

const env = process.env.NODE_ENV || 'development';
const rateLimiter = new SamsaraRateLimiter(config[env].rateLimit);
```
