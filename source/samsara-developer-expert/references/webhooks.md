# Webhooks

Complete guide to implementing and managing Samsara webhooks for real-time event notifications.

## Overview

Webhooks provide real-time notifications when events occur in your Samsara account.

**Benefits**:
- Instant notifications (seconds of latency)
- No polling required
- Reduced API calls
- Event-driven architecture

## Setup

### 1. Configure in Dashboard

1. Navigate to **Settings** → **Developer** → **Webhooks**
2. Click **Create Webhook**
3. Enter your public HTTPS endpoint URL
4. Select event types to receive
5. Save and copy the **webhook secret**

### 2. Event Types

Available webhook events:

| Event Type | Description | Use Case |
|------------|-------------|----------|
| `Alert` | Geofence, speeding, harsh events | Safety monitoring |
| `RouteStopEtaUpdated` | Route progress updates | Real-time tracking |
| `VehicleMalfunctionDetected` | Diagnostic trouble code | Maintenance alerts |
| `VehicleMalfunctionCleared` | DTC cleared | Maintenance tracking |
| `HosLogUpdated` | HOS log changes | Compliance monitoring |

## Webhook Payload

### Structure

```json
{
  "id": "webhook_event_123",
  "eventType": "Alert",
  "createdAtTime": "2025-02-03T14:30:00Z",
  "orgId": "org_456",
  "data": {
    // Event-specific data
  }
}
```

### Alert Event

```json
{
  "eventType": "Alert",
  "data": {
    "id": "alert_789",
    "alertType": "geofence_exit",
    "severity": "critical",
    "triggeredAtTime": "2025-02-03T14:30:00Z",
    "vehicle": {
      "id": "vehicle_123",
      "name": "Truck 5"
    },
    "driver": {
      "id": "driver_456",
      "name": "John Doe"
    },
    "location": {
      "latitude": 37.7749,
      "longitude": -122.4194
    }
  }
}
```

### RouteStopEtaUpdated Event

```json
{
  "eventType": "RouteStopEtaUpdated",
  "data": {
    "routeId": "route_123",
    "stopId": "stop_456",
    "externalIds": {
      "cmc": "action_789"
    },
    "estimatedArrivalTime": "2025-02-03T15:00:00Z",
    "state": "enRoute",
    "location": {
      "latitude": 37.7749,
      "longitude": -122.4194
    }
  }
}
```

## Security: HMAC Signature Verification

Verify webhook authenticity using HMAC SHA-256 signatures.

### Node.js Implementation

```typescript
import crypto from 'crypto';

function verifyWebhookSignature(
  payload: string | Buffer,
  signature: string,
  secret: string
): boolean {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(payload).digest('hex');
  
  // Constant-time comparison to prevent timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(digest)
  );
}

// Express.js example
app.post('/webhooks/samsara', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-samsara-signature'] as string;
  const payload = req.body; // Raw buffer from express.raw()
  
  if (!verifyWebhookSignature(payload, signature, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }
  
  const data = JSON.parse(payload.toString());
  // Process webhook...
  res.status(200).json({ received: true });
});
```

### Python Implementation

```python
import hmac
import hashlib

def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    expected_signature = mac.hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature, expected_signature)

# Flask example
@app.route('/webhooks/samsara', methods=['POST'])
def samsara_webhook():
    signature = request.headers.get('X-Samsara-Signature')
    payload = request.get_data()
    
    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return {'error': 'Invalid signature'}, 401
    
    data = request.get_json()
    # Process webhook...
    return {'received': True}, 200
```

## Webhook Handler Implementation

### Production-Ready Handler

```typescript
import express from 'express';
import crypto from 'crypto';

interface WebhookEvent {
  id: string;
  eventType: string;
  createdAtTime: string;
  orgId: string;
  data: any;
}

class SamsaraWebhookHandler {
  private secret: string;
  private handlers: Map<string, (event: WebhookEvent) => Promise<void>>;
  
  constructor(secret: string) {
    this.secret = secret;
    this.handlers = new Map();
  }
  
  on(eventType: string, handler: (event: WebhookEvent) => Promise<void>) {
    this.handlers.set(eventType, handler);
  }
  
  async handle(payload: Buffer, signature: string): Promise<void> {
    // Verify signature
    if (!this.verifySignature(payload, signature)) {
      throw new Error('Invalid webhook signature');
    }
    
    // Parse event
    const event: WebhookEvent = JSON.parse(payload.toString());
    
    // Get handler for event type
    const handler = this.handlers.get(event.eventType);
    if (!handler) {
      console.warn(`No handler for event type: ${event.eventType}`);
      return;
    }
    
    // Execute handler
    await handler(event);
  }
  
  private verifySignature(payload: Buffer, signature: string): boolean {
    const hmac = crypto.createHmac('sha256', this.secret);
    const digest = hmac.update(payload).digest('hex');
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(digest)
    );
  }
}

// Usage
const webhookHandler = new SamsaraWebhookHandler(WEBHOOK_SECRET);

// Register event handlers
webhookHandler.on('Alert', async (event) => {
  console.log('Alert received:', event.data);
  await processAlert(event.data);
});

webhookHandler.on('RouteStopEtaUpdated', async (event) => {
  console.log('ETA updated:', event.data);
  await updateEta(event.data);
});

// Express endpoint
app.post('/webhooks/samsara', 
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    try {
      const signature = req.headers['x-samsara-signature'] as string;
      await webhookHandler.handle(req.body, signature);
      res.status(200).json({ received: true });
    } catch (error) {
      console.error('Webhook error:', error);
      res.status(500).json({ error: 'Processing failed' });
    }
  }
);
```

## Event Processing

### Alert Handler

```typescript
async function processAlert(alertData: any) {
  const alert = {
    samsaraId: alertData.id,
    type: alertData.alertType,
    severity: alertData.severity,
    vehicleId: alertData.vehicle?.id,
    driverId: alertData.driver?.id,
    location: alertData.location,
    triggeredAt: new Date(alertData.triggeredAtTime)
  };
  
  // Store in database
  await db.alerts.create({ data: alert });
  
  // Send notifications based on severity
  if (alert.severity === 'critical') {
    await notifyDispatcher(alert);
  }
  
  // Log for analytics
  await analytics.track('alert_received', alert);
}
```

### Route Stop ETA Handler

```typescript
async function updateEta(etaData: any) {
  // Find action by external ID
  const action = await db.containerActions.findFirst({
    where: {
      externalIds: { 
        path: ['cmc'], 
        equals: etaData.externalIds?.cmc 
      }
    }
  });
  
  if (!action) {
    console.warn(`Action not found for stop ${etaData.stopId}`);
    return;
  }
  
  // Update ETA and state
  await db.containerActions.update({
    where: { id: action.id },
    data: {
      estimatedArrival: new Date(etaData.estimatedArrivalTime),
      status: mapStopStateToStatus(etaData.state),
      lastLocation: etaData.location
    }
  });
  
  // Notify customer if applicable
  if (shouldNotifyCustomer(action, etaData)) {
    await sendCustomerNotification(action, etaData);
  }
}
```

## Retry Logic

Samsara retries failed webhooks with exponential backoff:

- Retry 1: Immediately
- Retry 2: After 5 seconds
- Retry 3: After 25 seconds
- Retry 4: After 125 seconds
- Retry 5: After 625 seconds (final attempt)

### Your Endpoint Requirements

1. **Return 2XX quickly** (< 5 seconds)
2. **Process asynchronously** if operation is slow
3. **Handle idempotent processing** (same event may arrive multiple times)

### Async Processing Pattern

```typescript
app.post('/webhooks/samsara', 
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    try {
      // Quick validation
      const signature = req.headers['x-samsara-signature'] as string;
      if (!verifyWebhookSignature(req.body, signature, WEBHOOK_SECRET)) {
        return res.status(401).json({ error: 'Invalid signature' });
      }
      
      // Acknowledge immediately
      res.status(200).json({ received: true });
      
      // Process asynchronously
      const event = JSON.parse(req.body.toString());
      setImmediate(async () => {
        try {
          await processEvent(event);
        } catch (error) {
          console.error('Async processing error:', error);
          // Log to error tracking service
        }
      });
      
    } catch (error) {
      console.error('Webhook error:', error);
      res.status(500).json({ error: 'Processing failed' });
    }
  }
);
```

## Idempotency

Webhooks may be delivered multiple times. Implement idempotent processing:

```typescript
async function processEventIdempotent(event: WebhookEvent) {
  // Check if already processed
  const existing = await db.processedWebhooks.findUnique({
    where: { eventId: event.id }
  });
  
  if (existing) {
    console.log(`Event ${event.id} already processed, skipping`);
    return;
  }
  
  // Process event
  await processEvent(event);
  
  // Mark as processed
  await db.processedWebhooks.create({
    data: {
      eventId: event.id,
      eventType: event.eventType,
      processedAt: new Date()
    }
  });
}
```

## Testing Webhooks

### Local Testing with ngrok

1. Install ngrok: `npm install -g ngrok`
2. Start your local server: `node server.js`
3. Expose with ngrok: `ngrok http 3000`
4. Use ngrok URL in Samsara dashboard: `https://abc123.ngrok.io/webhooks/samsara`

### Mock Webhook Events

```typescript
// Test your handler locally
const mockAlert = {
  id: 'test_event_123',
  eventType: 'Alert',
  createdAtTime: new Date().toISOString(),
  orgId: 'test_org',
  data: {
    id: 'alert_123',
    alertType: 'speeding',
    severity: 'medium',
    triggeredAtTime: new Date().toISOString(),
    vehicle: { id: 'v123', name: 'Test Vehicle' }
  }
};

const payload = Buffer.from(JSON.stringify(mockAlert));
const signature = crypto
  .createHmac('sha256', WEBHOOK_SECRET)
  .update(payload)
  .digest('hex');

await webhookHandler.handle(payload, signature);
```

### Integration Tests

```typescript
describe('Webhook Handler', () => {
  it('verifies valid signature', async () => {
    const payload = Buffer.from(JSON.stringify(testEvent));
    const validSig = crypto
      .createHmac('sha256', WEBHOOK_SECRET)
      .update(payload)
      .digest('hex');
    
    const result = await request(app)
      .post('/webhooks/samsara')
      .set('X-Samsara-Signature', validSig)
      .send(payload);
    
    expect(result.status).toBe(200);
  });
  
  it('rejects invalid signature', async () => {
    const payload = Buffer.from(JSON.stringify(testEvent));
    const invalidSig = 'invalid_signature';
    
    const result = await request(app)
      .post('/webhooks/samsara')
      .set('X-Samsara-Signature', invalidSig)
      .send(payload);
    
    expect(result.status).toBe(401);
  });
  
  it('handles events idempotently', async () => {
    const payload = Buffer.from(JSON.stringify(testEvent));
    const sig = generateSignature(payload);
    
    // Send same event twice
    await request(app).post('/webhooks/samsara').set('X-Samsara-Signature', sig).send(payload);
    await request(app).post('/webhooks/samsara').set('X-Samsara-Signature', sig).send(payload);
    
    // Should only process once
    const count = await db.alerts.count({ where: { samsaraId: testEvent.data.id } });
    expect(count).toBe(1);
  });
});
```

## Monitoring

### Track Webhook Health

```typescript
class WebhookMonitor {
  private metrics = {
    received: 0,
    processed: 0,
    failed: 0,
    invalidSignatures: 0
  };
  
  recordReceived() {
    this.metrics.received++;
  }
  
  recordProcessed() {
    this.metrics.processed++;
  }
  
  recordFailed() {
    this.metrics.failed++;
  }
  
  recordInvalidSignature() {
    this.metrics.invalidSignatures++;
  }
  
  getMetrics() {
    return {
      ...this.metrics,
      successRate: this.metrics.processed / this.metrics.received
    };
  }
}

const monitor = new WebhookMonitor();

// In webhook handler
app.post('/webhooks/samsara', async (req, res) => {
  monitor.recordReceived();
  
  try {
    if (!verifySignature(req.body, signature)) {
      monitor.recordInvalidSignature();
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    await processEvent(event);
    monitor.recordProcessed();
    res.status(200).json({ received: true });
    
  } catch (error) {
    monitor.recordFailed();
    res.status(500).json({ error: 'Processing failed' });
  }
});
```

### Alert on Failures

```typescript
setInterval(() => {
  const metrics = monitor.getMetrics();
  
  if (metrics.failed > 10 || metrics.successRate < 0.95) {
    sendAlert({
      message: 'Webhook processing issues detected',
      failed: metrics.failed,
      successRate: `${(metrics.successRate * 100).toFixed(2)}%`
    });
  }
}, 60000); // Check every minute
```

## Best Practices

1. **Always verify signatures** - Never process unverified webhooks
2. **Respond quickly** - Acknowledge within 5 seconds
3. **Process asynchronously** - Don't block the response
4. **Handle idempotency** - Same event may arrive multiple times
5. **Log all events** - For debugging and auditing
6. **Monitor failures** - Alert on processing issues
7. **Use HTTPS** - Required by Samsara
8. **Test locally** - Use ngrok for development
9. **Handle all event types** - Even if you don't process them
10. **Retry processing** - If your processing fails, retry internally

## Troubleshooting

### Webhooks Not Arriving

1. Verify endpoint is publicly accessible via HTTPS
2. Check Samsara dashboard for webhook configuration
3. Review webhook logs in Samsara dashboard
4. Test with curl from external server
5. Verify firewall/security group settings

### Signature Verification Failing

1. Use raw request body (before JSON parsing)
2. Verify webhook secret is correct
3. Check for body parsing middleware interfering
4. Use constant-time comparison
5. Log both expected and received signatures (temporarily)

### Events Being Retried

1. Ensure endpoint returns 2XX status
2. Respond within 5 seconds
3. Check for exceptions in processing
4. Review server logs for errors
5. Verify database connections are stable
