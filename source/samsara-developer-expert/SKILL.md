---
name: samsara-developer-expert
description: Expert guidance for developing with the Samsara Fleet Management API. Use this skill when working with Samsara API integration including fleet management, route synchronization, real-time vehicle tracking, driver management, safety events, HOS compliance, webhooks, or any Samsara-related development tasks. Covers API authentication, rate limiting, data synchronization patterns (feeds, snapshots, historical), external ID linking for TMS integration, route/stop management with state preservation, webhook implementation, and best practices for production integrations.
---

# Samsara Developer Expert

This skill provides comprehensive guidance for developing integrations with the Samsara Fleet Management API, based on official Samsara documentation and proven production patterns.

## Official Documentation

Always reference the official Samsara documentation as the authoritative source:
- **API Reference**: https://developers.samsara.com/reference/overview
- **TMS Integration Guide**: https://developers.samsara.com/docs/tms-integration
- **Developer Guides**: https://developers.samsara.com/docs

## Quick Reference

For detailed technical information, consult these bundled references:

- **[API Endpoints & Methods](references/api_endpoints.md)** - Complete endpoint reference with parameters and examples
- **[Data Synchronization Patterns](references/sync_patterns.md)** - Feed-based, historical, and snapshot patterns
- **[Route Management](references/route_management.md)** - Route creation, updates, and stop state preservation
- **[Authentication & Rate Limiting](references/auth_rate_limits.md)** - Token management and rate limit handling
- **[Webhooks](references/webhooks.md)** - Event types, signature verification, and retry logic
- **[Code Examples](references/code_examples.md)** - Production-tested code patterns

## Core Concepts

### Base URLs
- **US Customers**: `https://api.samsara.com`
- **EU Customers**: `https://api.eu.samsara.com`

Always use the correct base URL for the customer's region.

### Authentication
Use Bearer token authentication:
```
Authorization: Bearer <API_TOKEN>
```

Manage tokens in Dashboard → Settings → API Tokens. Tokens are shown only once upon creation.

### Rate Limiting Structure
Samsara enforces three-tier rate limiting:
1. **Per-Token**: 150 requests/sec
2. **Per-Organization**: 200 requests/sec (aggregate)
3. **Endpoint-Specific**: Varies by endpoint (5-50 req/sec)

Always implement exponential backoff with jitter when receiving 429 responses. Respect the `Retry-After` header.

### External IDs for TMS Integration
Use external IDs to link Samsara entities with your system:
```json
{
  "externalIds": {
    "yourSystemId": "12345",
    "anotherId": "ABC-789"
  }
}
```

Lookup entities using: `GET /fleet/vehicles/yourSystemId:12345`

## Data Synchronization Strategy

Choose the appropriate pattern based on your use case:

### 1. Real-Time Feeds (Recommended for Live Data)
Use feed endpoints for continuous synchronization:
- `/fleet/vehicles/stats/feed`
- `/fleet/locations/feed`
- `/fleet/safety-events/feed`

Poll every 5-10 seconds using cursor-based pagination. Store the `endCursor` to resume from the last position.

### 2. Historical Queries (For Reporting)
Use history endpoints for backfilling or ad-hoc queries:
- `/fleet/vehicles/stats/history`
- `/locations/history`

Specify time range with `startTime` and `endTime` parameters.

### 3. Snapshots (For Current State)
Use snapshot endpoints for dashboard displays:
- `/fleet/vehicles/stats`

Returns current state without historical context.

## Critical Implementation Patterns

### Route Updates with State Preservation
When updating routes via PATCH, you must provide the **FULL** stops list. To preserve stop state (arrival/departure times):

1. **Fetch the current route** to get existing stop IDs
2. **Include stop IDs** in your update payload
3. Omitting IDs causes Samsara to delete and recreate stops, **losing all state**

```typescript
// CORRECT: Preserves stop state
const existingRoute = await fetch(`/fleet/routes/${routeId}`);
const updatedStops = existingRoute.stops.map(stop => ({
  id: stop.id,  // CRITICAL: Include this
  // ... other fields
}));

await patch(`/fleet/routes/${routeId}`, { stops: updatedStops });
```

### Bidirectional Sync Orphan Handling
When syncing from Samsara → Your System, handle "orphaned" stops that exist in your system but are no longer in Samsara:

```typescript
// After processing Samsara stops
const samsaraStopIds = new Set(samsaraStops.map(s => s.id));
const orphanedStops = yourSystemStops.filter(s => 
  !samsaraStopIds.has(s.samsaraJobId)
);

// Unschedule or delete orphans
for (const orphan of orphanedStops) {
  await unscheduleStop(orphan.id);
}
```

### Status Mapping Between Systems
Map Samsara states to your system's statuses consistently:

```typescript
const STATUS_MAP = {
  'scheduled': 'PENDING',
  'en route': 'ENROUTE',
  'en_route': 'ENROUTE',
  'arrived': 'ARRIVED',
  'departed': 'COMPLETED',
  'completed': 'COMPLETED',
  'skipped': 'CANCELLED'
};
```

**Important**: Guard against reverting completed statuses during sync:
```typescript
if (currentStatus === 'COMPLETED' && newStatus !== 'COMPLETED') {
  // Skip update - don't revert completed jobs
  return;
}
```

## Common Workflows

### Sync Drivers and Vehicles
Always sync drivers and vehicles before syncing routes to maintain referential integrity:

```typescript
// 1. Sync drivers
const drivers = await fetch('/fleet/drivers');
await syncDriversToYourSystem(drivers);

// 2. Sync vehicles  
const vehicles = await fetch('/fleet/vehicles');
await syncVehiclesToYourSystem(vehicles);

// 3. Now safe to sync routes
const routes = await fetch('/fleet/routes?startTime=...&endTime=...');
await syncRoutesToYourSystem(routes);
```

### Create a Route with Stops
```typescript
const route = {
  name: "Route Name",
  driverId: "driver_123",
  vehicleId: "vehicle_456",
  scheduledStartTime: "2025-02-04T08:00:00Z",
  stops: [
    {
      address: {
        formattedAddress: "123 Main St, City, ST 12345"
      },
      scheduledArrivalTime: "2025-02-04T09:00:00Z",
      externalIds: { cmc: "action_789" },
      notes: "Gate code: 1234"
    }
  ],
  externalIds: { cmc: "route_999" }
};

await post('/fleet/routes', route);
```

### Handle Webhook Events
Verify HMAC signature and process events:

```typescript
const signature = request.headers['x-samsara-signature'];
const isValid = verifyHmacSignature(payload, signature, webhookSecret);

if (!isValid) {
  return res.status(401).json({ error: 'Invalid signature' });
}

const { eventType, data } = payload;
if (eventType === 'Alert') {
  await handleAlert(data);
} else if (eventType === 'RouteStopEtaUpdated') {
  await handleEtaUpdate(data);
}

res.status(200).json({ received: true });
```

## Error Handling

### Rate Limit Responses (429)
Implement exponential backoff:

```typescript
async function makeRequestWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, options);
    
    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '1');
      const backoff = Math.min(1000 * Math.pow(2, i), 30000);
      const jitter = Math.random() * 1000;
      await sleep(Math.max(retryAfter * 1000, backoff) + jitter);
      continue;
    }
    
    return response;
  }
  throw new Error('Max retries exceeded');
}
```

### Data Validation
Always validate data before sending to Samsara:

```typescript
// Validate required fields
if (!route.driverId || !route.vehicleId) {
  throw new Error('Driver and vehicle are required');
}

// Validate timestamps are RFC 3339
const timestamp = "2025-02-04T08:00:00Z";
if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(timestamp)) {
  throw new Error('Invalid timestamp format');
}
```

## Testing Recommendations

### Unit Tests
- Status mapping functions
- Address parsing logic
- External ID formatting
- Data transformations

### Integration Tests
- Full sync workflows
- Rate limiter behavior
- Error recovery
- Webhook signature verification

### Manual Testing Checklist
1. Sync routes for various date ranges
2. Create routes with multiple stops
3. Update routes while preserving stop state
4. Test with missing/incomplete data
5. Verify rate limiting behavior
6. Test webhook event handling
7. Validate bidirectional sync with orphan handling

## Helper Scripts

The skill includes production-tested helper scripts:

- **`scripts/rate_limiter.py`** - Rate limiting implementation
- **`scripts/sync_helpers.py`** - Common sync utilities
- **`scripts/webhook_verifier.py`** - HMAC signature verification

## Troubleshooting

### Routes Not Syncing
1. Check API token validity and scopes
2. Verify date range parameters
3. Confirm driver/vehicle IDs exist
4. Review rate limit status
5. Check for network connectivity

### Stops Losing State on Update
- Ensure you're fetching existing route first
- Verify stop IDs are included in update payload
- Check that you're using PATCH, not POST

### Webhooks Not Working
1. Verify webhook URL is publicly accessible
2. Check HMAC signature verification
3. Ensure endpoint returns 2XX within timeout
4. Review Samsara webhook retry logs

## Best Practices

1. **Always use external IDs** for entity linking
2. **Implement proper rate limiting** before production
3. **Use feeds for real-time data**, not repeated snapshots
4. **Preserve stop state** when updating routes
5. **Handle orphaned data** during bidirectional sync
6. **Guard completed statuses** from being reverted
7. **Verify webhook signatures** for security
8. **Log all sync operations** for debugging
9. **Test with incomplete data** scenarios
10. **Monitor API usage** and rate limits

## Performance Considerations

- Use batch operations where available
- Implement caching for frequently accessed data
- Use cursor-based pagination for large datasets
- Monitor and optimize database queries
- Consider async/background processing for heavy operations

## Security

- Store API tokens securely (environment variables, secrets manager)
- Implement webhook signature verification
- Validate all input data
- Use HTTPS for all API communication
- Rotate tokens periodically
- Log security events

## Additional Resources

For advanced topics and specific scenarios, consult the reference documents in the `references/` directory. Each document provides in-depth technical guidance for its domain.
