# Samsara API Endpoints Reference

Complete reference for key Samsara API endpoints with parameters, responses, and usage examples.

## Fleet Management

### Routes

**GET /fleet/routes**
- **Scope**: `Read Routes`
- **Rate Limit**: 25 req/sec
- **Description**: Lists all routes with optional filters
- **Parameters**:
  - `startTime` (string): RFC 3339 timestamp for start of range
  - `endTime` (string): RFC 3339 timestamp for end of range
  - `driverIds` (array): Filter by specific driver IDs
  - `limit` (integer): Max results per page (default: 100)
  - `after` (string): Cursor for pagination
- **Response**: Array of route objects with summary data

**GET /fleet/routes/{id}**
- **Scope**: `Read Routes`
- **Description**: Retrieves a single route with **full details** including all stops
- **Response**: Complete route object with:
  - Route metadata (name, driver, vehicle, dates)
  - Full stops array with state and timing information
  - External IDs
  - Tracking data

**POST /fleet/routes**
- **Scope**: `Create Routes`
- **Description**: Create a new route
- **Payload**:
```json
{
  "name": "Daily Route 01",
  "driverId": "driver_123",
  "vehicleId": "vehicle_456",
  "scheduledStartTime": "2025-02-04T08:00:00Z",
  "scheduledEndTime": "2025-02-04T17:00:00Z",
  "stops": [
    {
      "addressId": "addr_789",
      "scheduledArrivalTime": "2025-02-04T09:00:00Z",
      "notes": "Ring doorbell",
      "externalIds": { "yourSystem": "stop_001" }
    }
  ],
  "externalIds": { "yourSystem": "route_001" }
}
```
- **Response**: Created route object with Samsara-assigned ID

**PATCH /fleet/routes/{id}**
- **Scope**: `Update Routes`
- **Description**: Updates a route
- **Critical**: Must provide **FULL** stops array. Include stop IDs to preserve state.
- **Payload Example**:
```json
{
  "name": "Updated Route Name",
  "stops": [
    {
      "id": "stop_abc",  // CRITICAL: Include to preserve state
      "addressId": "addr_789",
      "scheduledArrivalTime": "2025-02-04T09:30:00Z",
      "notes": "Updated instructions"
    }
  ]
}
```

### Route Stops

**Stop States**:
- `scheduled` - Not yet started
- `enRoute` - Driver heading to location
- `arrived` - Driver at location
- `departed` - Driver left location
- `skipped` - Stop was skipped
- `completed` - Stop finished

**Stop Fields**:
- `id` - Unique stop identifier
- `addressId` - Reference to address object
- `state` - Current state (see above)
- `arrivalTime` - Actual arrival timestamp
- `departureTime` - Actual departure timestamp
- `scheduledArrivalTime` - Planned arrival
- `notes` - Instructions for driver
- `externalIds` - Links to your system

### Vehicles

**GET /fleet/vehicles**
- **Scope**: `Read Vehicles`
- **Rate Limit**: 25 req/sec
- **Parameters**:
  - `tagIds` (array): Filter by tag IDs
  - `limit` (integer): Results per page
  - `after` (string): Pagination cursor
- **Response**: Array of vehicle objects

**GET /fleet/vehicles/stats**
- **Scope**: `Read Vehicles`
- **Description**: Current state snapshot
- **Response**: Vehicle stats including GPS, odometer, fuel level

**GET /fleet/vehicles/stats/feed**
- **Scope**: `Read Vehicles`
- **Rate Limit**: 50 req/sec
- **Description**: Real-time telemetry feed
- **Parameters**:
  - `types` (array): Data types (gps, engineStates, fuelPercents)
  - `decorations` (array): Additional context (gps, location)
  - `after` (string): Cursor from previous call
- **Response**:
```json
{
  "data": [
    {
      "id": "vehicle_123",
      "gps": {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "time": "2025-02-03T14:30:00Z",
        "speedMilesPerHour": 35.2
      }
    }
  ],
  "pagination": {
    "endCursor": "eyJhZnR...",
    "hasNextPage": true
  }
}
```

**GET /fleet/vehicles/stats/history**
- **Scope**: `Read Vehicles`
- **Description**: Historical telemetry data
- **Parameters**:
  - `vehicleIds` (array): Specific vehicles
  - `startTime` (string): Start of time range
  - `endTime` (string): End of time range
  - `types` (array): Data types to retrieve

### Drivers

**GET /fleet/drivers**
- **Scope**: `Read Drivers`
- **Response**: Array of driver objects with:
  - Driver ID, name, username
  - Contact information
  - License information
  - Tags and attributes
  - External IDs

**GET /fleet/drivers/{id}**
- **Scope**: `Read Drivers`
- **Response**: Complete driver profile

### Locations

**GET /fleet/locations/feed**
- **Scope**: `Read Locations`
- **Rate Limit**: 50 req/sec
- **Description**: Real-time location updates for all tracked assets
- **Parameters**:
  - `after` (string): Cursor for incremental updates
- **Response**: Location updates with GPS coordinates

## Safety & Compliance

### Safety Events

**GET /fleet/safety-events**
- **Scope**: `Read Safety Events`
- **Rate Limit**: 5 req/sec
- **Description**: Harsh braking, speeding, collision events
- **Parameters**:
  - `driverIds` (array): Filter by drivers
  - `startTime` (string): Time range start
  - `endTime` (string): Time range end
  - `types` (array): Event types to include

**GET /fleet/safety-events/feed**
- **Scope**: `Read Safety Events`
- **Description**: Real-time safety event stream
- **Parameters**:
  - `after` (string): Resume cursor

### Hours of Service (HOS)

**GET /fleet/hos/logs**
- **Scope**: `Read HOS Logs`
- **Rate Limit**: 5 req/sec
- **Description**: Driver hours of service logs
- **Parameters**:
  - `driverIds` (array): Specific drivers
  - `startTime` (string): Log start time
  - `endTime` (string): Log end time
- **Note**: Data may lag 24-48 hours from ELD sync

## Webhooks

**Event Types**:
- `Alert` - Geofence, speeding, harsh events
- `RouteStopEtaUpdated` - Route progress updates
- `VehicleMalfunctionCleared` - Diagnostic cleared
- `VehicleMalfunctionDetected` - Diagnostic detected

**Webhook Configuration**:
- Set up in Dashboard → Settings → Developer → Webhooks
- Provide publicly accessible HTTPS URL
- Configure event types to receive
- Get webhook secret for signature verification

**Signature Verification**:
```javascript
const crypto = require('crypto');

function verifySignature(payload, signature, secret) {
  const hmac = crypto.createHmac('sha256', secret);
  const digest = hmac.update(JSON.stringify(payload)).digest('hex');
  return signature === digest;
}
```

## TMS Integration

### External ID Lookups

All major entities support external ID lookups:

```
GET /fleet/vehicles/tmsId:12345
GET /fleet/drivers/employeeId:EMP001
GET /fleet/routes/routeNumber:R123
```

Format: `/{resource}/{idType}:{idValue}`

### Setting External IDs

Include in creation/update payloads:

```json
{
  "externalIds": {
    "tmsId": "12345",
    "yourFieldName": "ABC-789",
    "anotherSystem": "XYZ-999"
  }
}
```

## Response Formats

### Pagination

Cursor-based pagination for all list endpoints:

```json
{
  "data": [...],
  "pagination": {
    "endCursor": "eyJhZnRlci...",
    "hasNextPage": true
  }
}
```

Use `endCursor` as `after` parameter in next request.

### Timestamps

All timestamps use RFC 3339 format:
- `2025-02-03T14:30:00Z` (UTC)
- `2025-02-03T09:30:00-05:00` (With timezone)

### Error Responses

```json
{
  "error": {
    "type": "InvalidRequestError",
    "message": "Validation failed",
    "details": {
      "field": "driverId",
      "reason": "Driver does not exist"
    }
  }
}
```

## Rate Limit Headers

Response headers indicate rate limit status:

```
X-RateLimit-Limit: 150
X-RateLimit-Remaining: 143
X-RateLimit-Reset: 1675444860
Retry-After: 5
```

## Common Patterns

### Feed Polling Pattern

```typescript
let cursor = null;

setInterval(async () => {
  const params = cursor ? { after: cursor } : {};
  const response = await fetch('/fleet/vehicles/stats/feed', params);
  
  // Process data
  for (const stat of response.data) {
    await processStat(stat);
  }
  
  // Update cursor for next iteration
  cursor = response.pagination.endCursor;
}, 10000); // Poll every 10 seconds
```

### Batch Operations

```typescript
// Get multiple vehicles by ID
const vehicleIds = ['v1', 'v2', 'v3'];
const vehicles = await Promise.all(
  vehicleIds.map(id => fetch(`/fleet/vehicles/${id}`))
);
```

### Date Range Queries

```typescript
const startTime = new Date('2025-02-01T00:00:00Z').toISOString();
const endTime = new Date('2025-02-28T23:59:59Z').toISOString();

const routes = await fetch('/fleet/routes', {
  params: { startTime, endTime }
});
```
