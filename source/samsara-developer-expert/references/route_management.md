# Route Management

Comprehensive guide to creating, updating, and managing routes with stop state preservation.

## Route Lifecycle

```
CREATE → SCHEDULED → IN_PROGRESS → COMPLETED
                ↓          ↓
            CANCELLED  MODIFIED
```

## Critical Concepts

### Stop State Preservation

**THE MOST IMPORTANT RULE**: When updating a route via PATCH, include stop IDs to preserve their state.

**Why This Matters**:
- Samsara tracks arrival/departure times on stop records
- Omitting a stop ID causes Samsara to delete and recreate the stop
- Recreating stops **loses all arrival/departure timestamps and driver progress**

**Correct Pattern**:
```typescript
// STEP 1: Fetch existing route
const existing = await fetch(`/fleet/routes/${routeId}`);
const existingData = await existing.json();

// STEP 2: Build stops list with IDs preserved
const updatedStops = existingData.stops.map(stop => ({
  id: stop.id,  // CRITICAL: Keep the ID
  // Update other fields as needed
  notes: getUpdatedNotes(stop),
  scheduledArrivalTime: getUpdatedTime(stop)
}));

// STEP 3: PATCH with preserved IDs
await fetch(`/fleet/routes/${routeId}`, {
  method: 'PATCH',
  body: JSON.stringify({ stops: updatedStops })
});
```

**Incorrect Pattern (Loses State)**:
```typescript
// BAD: No ID included - stop will be deleted and recreated
const stops = yourStops.map(s => ({
  addressId: s.addressId,
  scheduledArrivalTime: s.time
  // Missing: id field
}));

await patch(`/fleet/routes/${routeId}`, { stops });
// Result: All arrival/departure times LOST
```

## Creating Routes

### Basic Route Creation

```typescript
async function createRoute(routeData: {
  name: string;
  driverId: string;
  vehicleId: string;
  scheduledStartTime: string;
  stops: Array<{
    address: string;
    scheduledArrivalTime: string;
    notes?: string;
  }>;
}) {
  const route = {
    name: routeData.name,
    driverId: routeData.driverId,
    vehicleId: routeData.vehicleId,
    scheduledStartTime: routeData.scheduledStartTime,
    stops: routeData.stops.map(stop => ({
      address: {
        formattedAddress: stop.address
      },
      scheduledArrivalTime: stop.scheduledArrivalTime,
      notes: stop.notes || ''
    })),
    externalIds: {
      yourSystem: generateRouteId()
    }
  };
  
  const response = await fetch('/fleet/routes', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(route)
  });
  
  return await response.json();
}
```

### Using Address Objects

```typescript
// Option 1: Use existing addressId
const stop = {
  addressId: "addr_123",
  scheduledArrivalTime: "2025-02-04T09:00:00Z"
};

// Option 2: Use single-use location with full address
const stop = {
  singleUseLocation: {
    address: {
      formattedAddress: "123 Main St, City, ST 12345"
    },
    latitude: 37.7749,
    longitude: -122.4194
  },
  scheduledArrivalTime: "2025-02-04T09:00:00Z"
};

// Option 3: Use stop name (simple label, no full address)
const stop = {
  name: "Customer Site A",
  scheduledArrivalTime: "2025-02-04T09:00:00Z"
};
```

### External IDs for Linking

```typescript
const route = {
  name: "Route 001",
  // ... other fields
  stops: [
    {
      // ... stop fields
      externalIds: {
        cmc: "action_abc123",          // Your internal action ID
        tms: "delivery_789",           // TMS system ID
        customerRef: "PO-2025-001"     // Customer reference
      }
    }
  ],
  externalIds: {
    cmc: "route_xyz789",
    tms: "route_456"
  }
};
```

## Updating Routes

### Adding Stops (Preserving Existing)

```typescript
async function addStopsToRoute(routeId: string, newStops: any[]) {
  // 1. Fetch existing route
  const existing = await fetch(`/fleet/routes/${routeId}`);
  const existingData = await existing.json();
  
  // 2. Preserve existing stops with their IDs
  const existingStops = existingData.stops.map(stop => ({
    id: stop.id,  // Preserve ID
    addressId: stop.addressId,
    scheduledArrivalTime: stop.scheduledArrivalTime,
    notes: stop.notes,
    externalIds: stop.externalIds
  }));
  
  // 3. Format new stops (no ID, will be created)
  const newStopsFormatted = newStops.map(stop => ({
    address: { formattedAddress: stop.address },
    scheduledArrivalTime: stop.scheduledArrivalTime,
    notes: stop.notes,
    externalIds: { cmc: stop.id }
  }));
  
  // 4. Combine and update
  const allStops = [...existingStops, ...newStopsFormatted];
  
  await fetch(`/fleet/routes/${routeId}`, {
    method: 'PATCH',
    headers: {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ stops: allStops })
  });
}
```

### Removing Stops

```typescript
async function removeStopFromRoute(routeId: string, stopIdToRemove: string) {
  // 1. Fetch existing route
  const existing = await fetch(`/fleet/routes/${routeId}`);
  const existingData = await existing.json();
  
  // 2. Filter out the stop to remove, keeping IDs on remaining
  const remainingStops = existingData.stops
    .filter(stop => stop.id !== stopIdToRemove)
    .map(stop => ({
      id: stop.id,  // Preserve IDs
      addressId: stop.addressId,
      scheduledArrivalTime: stop.scheduledArrivalTime,
      notes: stop.notes,
      externalIds: stop.externalIds
    }));
  
  // 3. Update with remaining stops
  await fetch(`/fleet/routes/${routeId}`, {
    method: 'PATCH',
    body: JSON.stringify({ stops: remainingStops })
  });
}
```

### Reordering Stops

```typescript
async function reorderStops(
  routeId: string,
  orderedStopIds: string[]
) {
  // 1. Fetch existing route
  const existing = await fetch(`/fleet/routes/${routeId}`);
  const existingData = await existing.json();
  
  // 2. Create map for quick lookup
  const stopMap = new Map(
    existingData.stops.map(stop => [stop.id, stop])
  );
  
  // 3. Build ordered list preserving IDs
  const reorderedStops = orderedStopIds.map(id => {
    const stop = stopMap.get(id);
    return {
      id: stop.id,  // CRITICAL
      addressId: stop.addressId,
      scheduledArrivalTime: stop.scheduledArrivalTime,
      notes: stop.notes,
      externalIds: stop.externalIds
    };
  });
  
  // 4. Update
  await fetch(`/fleet/routes/${routeId}`, {
    method: 'PATCH',
    body: JSON.stringify({ stops: reorderedStops })
  });
}
```

### Updating Stop Details

```typescript
async function updateStopNotes(
  routeId: string,
  stopId: string,
  newNotes: string
) {
  // 1. Fetch existing
  const existing = await fetch(`/fleet/routes/${routeId}`);
  const existingData = await existing.json();
  
  // 2. Update specific stop, preserve all IDs
  const updatedStops = existingData.stops.map(stop => ({
    id: stop.id,  // Always preserve
    addressId: stop.addressId,
    scheduledArrivalTime: stop.scheduledArrivalTime,
    notes: stop.id === stopId ? newNotes : stop.notes,
    externalIds: stop.externalIds
  }));
  
  // 3. PATCH
  await fetch(`/fleet/routes/${routeId}`, {
    method: 'PATCH',
    body: JSON.stringify({ stops: updatedStops })
  });
}
```

## Reading Routes

### Get Single Route with Details

```typescript
async function getRouteDetails(routeId: string) {
  const response = await fetch(`/fleet/routes/${routeId}`, {
    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
  });
  
  const route = await response.json();
  
  return {
    id: route.id,
    name: route.name,
    driver: route.driver,
    vehicle: route.vehicle,
    scheduledStartTime: route.scheduledStartTime,
    stops: route.stops.map(stop => ({
      id: stop.id,
      address: stop.address || stop.name,
      state: stop.state,
      arrivalTime: stop.arrivalTime,
      departureTime: stop.departureTime,
      scheduledArrivalTime: stop.scheduledArrivalTime,
      notes: stop.notes,
      externalIds: stop.externalIds
    }))
  };
}
```

### List Routes with Filters

```typescript
async function getRoutesForDateRange(
  startTime: string,
  endTime: string,
  driverIds?: string[]
) {
  const params = new URLSearchParams({
    startTime,
    endTime,
    ...(driverIds && { driverIds: driverIds.join(',') })
  });
  
  const response = await fetch(`/fleet/routes?${params}`, {
    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
  });
  
  return await response.json();
}
```

### Lookup by External ID

```typescript
async function getRouteByExternalId(systemId: string, idValue: string) {
  const response = await fetch(`/fleet/routes/${systemId}:${idValue}`, {
    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
  });
  
  if (response.status === 404) {
    return null; // Route not found
  }
  
  return await response.json();
}

// Usage
const route = await getRouteByExternalId('cmc', 'route_xyz789');
```

## Stop State Management

### Stop States

```typescript
type StopState = 
  | 'scheduled'   // Not started
  | 'enRoute'     // Driver heading to stop
  | 'arrived'     // Driver at location
  | 'departed'    // Driver left location
  | 'skipped'     // Stop was skipped
  | 'completed';  // Stop finished

interface Stop {
  id: string;
  state: StopState;
  arrivalTime?: string;      // Actual arrival (set by Samsara)
  departureTime?: string;    // Actual departure (set by Samsara)
  scheduledArrivalTime: string;  // Planned arrival
}
```

### Tracking Stop Progress

```typescript
async function getStopProgress(routeId: string, stopId: string) {
  const route = await fetch(`/fleet/routes/${routeId}`);
  const routeData = await route.json();
  
  const stop = routeData.stops.find(s => s.id === stopId);
  
  return {
    state: stop.state,
    isStarted: stop.state !== 'scheduled',
    isCompleted: stop.state === 'completed' || stop.state === 'departed',
    actualArrival: stop.arrivalTime,
    actualDeparture: stop.departureTime,
    timeAtLocation: stop.arrivalTime && stop.departureTime
      ? calculateDuration(stop.arrivalTime, stop.departureTime)
      : null
  };
}
```

### Protecting Completed State

```typescript
async function safeUpdateStop(
  routeId: string,
  stopId: string,
  updates: any
) {
  const existing = await fetch(`/fleet/routes/${routeId}`);
  const existingData = await existing.json();
  
  const stop = existingData.stops.find(s => s.id === stopId);
  
  // GUARD: Don't revert completed stops
  if (stop.state === 'completed' && updates.state !== 'completed') {
    console.warn(`Preventing state regression for stop ${stopId}`);
    delete updates.state;  // Remove state change
  }
  
  const updatedStops = existingData.stops.map(s => ({
    id: s.id,
    ...(s.id === stopId ? updates : s)
  }));
  
  await fetch(`/fleet/routes/${routeId}`, {
    method: 'PATCH',
    body: JSON.stringify({ stops: updatedStops })
  });
}
```

## Address Parsing

### Parsing Formatted Addresses

```typescript
function parseFormattedAddress(formattedAddress: string) {
  // Format: "123 Main St, City, ST 12345"
  const parts = formattedAddress.split(',').map(s => s.trim());
  
  if (parts.length < 3) {
    return {
      address1: formattedAddress,
      city: null,
      state: null,
      zipCode: null
    };
  }
  
  const [address1, city, stateZip] = parts;
  const stateZipMatch = stateZip.match(/([A-Z]{2})\s+(\d{5}(-\d{4})?)/);
  
  return {
    address1,
    city,
    state: stateZipMatch ? stateZipMatch[1] : null,
    zipCode: stateZipMatch ? stateZipMatch[2] : null
  };
}

// Usage
const parsed = parseFormattedAddress("123 Main St, Greenville, SC 29607");
// { address1: "123 Main St", city: "Greenville", state: "SC", zipCode: "29607" }
```

### Handling Incomplete Addresses

```typescript
function handleAddress(stop: any) {
  if (stop.address?.formattedAddress) {
    return parseFormattedAddress(stop.address.formattedAddress);
  } else if (stop.name) {
    // Only name provided, no full address
    return {
      address1: stop.name,
      city: null,
      state: null,
      zipCode: null
    };
  } else {
    return null;
  }
}
```

## Route Synchronization Helpers

### Matching Routes

```typescript
async function findMatchingRoute(samsaraRoute: any) {
  // Try external ID first (most reliable)
  if (samsaraRoute.externalIds?.cmc) {
    const byExternalId = await db.routes.findFirst({
      where: { externalIds: { path: ['cmc'], equals: samsaraRoute.externalIds.cmc } }
    });
    if (byExternalId) return byExternalId;
  }
  
  // Fallback to Samsara ID (for orphaned routes)
  if (samsaraRoute.id) {
    const bySamsaraId = await db.routes.findFirst({
      where: { samsaraRouteId: samsaraRoute.id }
    });
    if (bySamsaraId) return bySamsaraId;
  }
  
  return null;
}
```

### Matching Stops

```typescript
async function findMatchingStop(samsaraStop: any, routeId: string) {
  // Try external ID
  if (samsaraStop.externalIds?.cmc) {
    const byExternalId = await db.stops.findFirst({
      where: {
        routeId,
        externalIds: { path: ['cmc'], equals: samsaraStop.externalIds.cmc }
      }
    });
    if (byExternalId) return byExternalId;
  }
  
  // Fallback to Samsara job ID
  if (samsaraStop.id) {
    const bySamsaraId = await db.stops.findFirst({
      where: { samsaraJobId: samsaraStop.id, routeId }
    });
    if (bySamsaraId) return bySamsaraId;
  }
  
  return null;
}
```

## Common Pitfalls

### ❌ Pitfall 1: Not Fetching Before Update

```typescript
// BAD: Updates without fetching existing
async function badUpdate(routeId: string, newStops: any[]) {
  await patch(`/fleet/routes/${routeId}`, { stops: newStops });
  // Loses all stop state!
}
```

### ✅ Solution: Always Fetch First

```typescript
async function goodUpdate(routeId: string, newStops: any[]) {
  const existing = await fetch(`/fleet/routes/${routeId}`);
  const updatedStops = mergeStops(existing.stops, newStops);
  await patch(`/fleet/routes/${routeId}`, { stops: updatedStops });
}
```

### ❌ Pitfall 2: Forgetting Stop IDs

```typescript
// BAD: Maps without preserving IDs
const stops = existingStops.map(s => ({
  addressId: s.addressId  // Missing: id field
}));
```

### ✅ Solution: Always Include IDs

```typescript
const stops = existingStops.map(s => ({
  id: s.id,  // INCLUDE THIS
  addressId: s.addressId
}));
```

### ❌ Pitfall 3: Reverting Completed Status

```typescript
// BAD: Blindly updates status
async function badStatusUpdate(stopId: string, newStatus: string) {
  await updateStop(stopId, { state: newStatus });
  // Might revert from 'completed' to 'scheduled'!
}
```

### ✅ Solution: Guard Completed State

```typescript
async function goodStatusUpdate(stopId: string, newStatus: string) {
  const current = await getStop(stopId);
  if (current.state === 'completed' && newStatus !== 'completed') {
    return; // Prevent regression
  }
  await updateStop(stopId, { state: newStatus });
}
```

## Testing Route Updates

### Test Suite

```typescript
describe('Route Updates', () => {
  it('preserves stop state on reorder', async () => {
    const route = await createTestRoute();
    const stop = route.stops[0];
    
    // Simulate driver arrival
    await simulateArrival(route.id, stop.id);
    
    // Reorder stops
    await reorderStops(route.id, [stop.id, ...otherStopIds]);
    
    // Verify arrival time preserved
    const updated = await getRoute(route.id);
    expect(updated.stops[0].arrivalTime).toBe(stop.arrivalTime);
  });
  
  it('prevents completed status regression', async () => {
    const route = await createTestRoute();
    const stop = route.stops[0];
    
    await completeStop(route.id, stop.id);
    await updateStopStatus(route.id, stop.id, 'scheduled');
    
    const final = await getRoute(route.id);
    expect(final.stops[0].state).toBe('completed');
  });
});
```
