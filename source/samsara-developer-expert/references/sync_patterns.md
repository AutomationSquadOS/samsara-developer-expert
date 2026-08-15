# Data Synchronization Patterns

Comprehensive guide to synchronizing data between Samsara and your system.

## Pattern Selection

Choose the appropriate pattern based on your requirements:

| Pattern | Use Case | Frequency | Latency |
|---------|----------|-----------|---------|
| Feed | Real-time tracking, live dashboards | 5-10 sec | Seconds |
| Snapshot | Current state dashboards | On-demand | Immediate |
| Historical | Reporting, backfilling | Ad-hoc | N/A |

## 1. Feed-Based Synchronization (Recommended)

Feed endpoints provide incremental updates using cursor-based pagination.

### Key Characteristics

- **Incremental**: Only returns changes since last cursor
- **Real-time**: Updates available within seconds
- **Efficient**: Minimal data transfer
- **Resumable**: Store cursor to resume after interruptions

### Feed Endpoints

- `/fleet/vehicles/stats/feed`
- `/fleet/locations/feed`
- `/fleet/safety-events/feed`

### Implementation Pattern

```typescript
class FeedSync {
  private cursor: string | null = null;
  private intervalId: NodeJS.Timeout | null = null;
  
  async start(pollIntervalMs = 10000) {
    this.intervalId = setInterval(() => {
      this.poll();
    }, pollIntervalMs);
  }
  
  async poll() {
    try {
      const params = this.cursor ? { after: this.cursor } : {};
      const response = await fetch('/fleet/vehicles/stats/feed', {
        params,
        headers: { 'Authorization': `Bearer ${API_TOKEN}` }
      });
      
      const data = await response.json();
      
      // Process incremental updates
      for (const stat of data.data) {
        await this.processUpdate(stat);
      }
      
      // Save cursor for next iteration
      if (data.pagination?.endCursor) {
        this.cursor = data.pagination.endCursor;
        await this.saveCursor(this.cursor);
      }
      
    } catch (error) {
      console.error('Feed poll error:', error);
      // Continue polling despite errors
    }
  }
  
  async processUpdate(stat: any) {
    // Update your database
    await db.vehicles.upsert({
      where: { samsaraId: stat.id },
      update: {
        gps: stat.gps,
        updatedAt: new Date()
      },
      create: {
        samsaraId: stat.id,
        gps: stat.gps
      }
    });
  }
  
  async saveCursor(cursor: string) {
    // Persist cursor to resume after restart
    await db.syncState.upsert({
      where: { feed: 'vehicles_stats' },
      update: { cursor },
      create: { feed: 'vehicles_stats', cursor }
    });
  }
  
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }
}

// Usage
const sync = new FeedSync();
await sync.start(10000); // Poll every 10 seconds
```

### Feed Best Practices

1. **Start with No Cursor**: On first run, omit `after` parameter to get current state
2. **Persist Cursors**: Store cursors in database to survive restarts
3. **Handle Errors Gracefully**: Continue polling even if one iteration fails
4. **Monitor Lag**: Track time between Samsara timestamp and processing
5. **Backpressure**: If processing falls behind, consider batching updates

### Cursor Management

```typescript
// Load cursor on startup
async function initializeFeed() {
  const savedState = await db.syncState.findUnique({
    where: { feed: 'vehicles_stats' }
  });
  
  return savedState?.cursor || null;
}

// Reset cursor (for full resync)
async function resetFeed() {
  await db.syncState.update({
    where: { feed: 'vehicles_stats' },
    data: { cursor: null }
  });
}
```

## 2. Snapshot Pattern

Request current state without historical context.

### Use Cases

- Dashboard displays showing current status
- On-demand data refresh
- User-initiated updates

### Implementation

```typescript
async function getCurrentVehicleStats(vehicleIds?: string[]) {
  const response = await fetch('/fleet/vehicles/stats', {
    params: vehicleIds ? { vehicleIds } : {},
    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
  });
  
  const data = await response.json();
  return data.data;
}

// Usage in dashboard
app.get('/api/dashboard/vehicles', async (req, res) => {
  const stats = await getCurrentVehicleStats();
  res.json(stats);
});
```

### Snapshot vs Feed

- **Snapshot**: Full state, no incremental updates
- **Feed**: Incremental updates, requires cursor management

Use snapshots for:
- Infrequent updates
- Full refresh operations
- Simple use cases without real-time needs

Use feeds for:
- Continuous monitoring
- Real-time dashboards
- High-frequency updates

## 3. Historical Data Pattern

Query past data for reporting and analytics.

### History Endpoints

- `/fleet/vehicles/stats/history`
- `/locations/history`

### Implementation

```typescript
async function getHistoricalStats(options: {
  vehicleIds: string[];
  startTime: string;
  endTime: string;
  types: string[];
}) {
  const response = await fetch('/fleet/vehicles/stats/history', {
    params: options,
    headers: { 'Authorization': `Bearer ${API_TOKEN}` }
  });
  
  return await response.json();
}

// Generate daily report
async function generateDailyReport(date: Date) {
  const startTime = new Date(date.setHours(0,0,0,0)).toISOString();
  const endTime = new Date(date.setHours(23,59,59,999)).toISOString();
  
  const stats = await getHistoricalStats({
    vehicleIds: await getAllVehicleIds(),
    startTime,
    endTime,
    types: ['gps', 'engineStates', 'fuelPercents']
  });
  
  return generateReport(stats);
}
```

### Pagination for Historical Data

```typescript
async function getAllHistoricalStats(options: any) {
  let allData = [];
  let cursor = null;
  
  do {
    const params = { ...options, ...(cursor ? { after: cursor } : {}) };
    const response = await fetch('/fleet/vehicles/stats/history', { params });
    const data = await response.json();
    
    allData = allData.concat(data.data);
    cursor = data.pagination?.endCursor;
    
  } while (cursor && data.pagination?.hasNextPage);
  
  return allData;
}
```

## Bidirectional Synchronization

Sync data both ways between Samsara and your system.

### Samsara → Your System

```typescript
async function syncFromSamsara() {
  // 1. Fetch from Samsara
  const samsaraRoutes = await fetch('/fleet/routes', {
    params: {
      startTime: getStartOfWeek(),
      endTime: getEndOfWeek()
    }
  });
  
  for (const samsaraRoute of samsaraRoutes.data) {
    // 2. Find existing route by external ID
    const existingRoute = await db.routes.findFirst({
      where: {
        OR: [
          { externalIds: { path: ['cmc'], equals: samsaraRoute.externalIds?.cmc } },
          { samsaraRouteId: samsaraRoute.id }
        ]
      }
    });
    
    if (existingRoute) {
      // 3. Update existing
      await db.routes.update({
        where: { id: existingRoute.id },
        data: mapSamsaraToLocal(samsaraRoute)
      });
    } else {
      // 4. Create new
      await db.routes.create({
        data: {
          ...mapSamsaraToLocal(samsaraRoute),
          samsaraRouteId: samsaraRoute.id
        }
      });
    }
    
    // 5. Sync stops
    await syncStops(existingRoute?.id, samsaraRoute.stops);
  }
  
  // 6. Handle orphans (in your system but not in Samsara)
  await handleOrphans(samsaraRoutes.data);
}
```

### Your System → Samsara

```typescript
async function pushToSamsara(localRoute: any) {
  // 1. Check if route exists in Samsara
  if (localRoute.samsaraRouteId) {
    // 2. Fetch existing to get stop IDs
    const existing = await fetch(`/fleet/routes/${localRoute.samsaraRouteId}`);
    const existingData = await existing.json();
    
    // 3. Map stops, preserving IDs
    const stops = localRoute.stops.map(localStop => {
      const existingStop = existingData.stops.find(
        s => s.externalIds?.cmc === localStop.id
      );
      
      return {
        ...(existingStop?.id ? { id: existingStop.id } : {}),
        address: { formattedAddress: localStop.address },
        scheduledArrivalTime: localStop.scheduledTime,
        externalIds: { cmc: localStop.id },
        notes: localStop.notes
      };
    });
    
    // 4. PATCH to update
    await fetch(`/fleet/routes/${localRoute.samsaraRouteId}`, {
      method: 'PATCH',
      body: JSON.stringify({ stops })
    });
  } else {
    // 5. POST to create new route
    const response = await fetch('/fleet/routes', {
      method: 'POST',
      body: JSON.stringify(mapLocalToSamsara(localRoute))
    });
    
    const created = await response.json();
    
    // 6. Save Samsara ID for future updates
    await db.routes.update({
      where: { id: localRoute.id },
      data: { samsaraRouteId: created.id }
    });
  }
}
```

### Orphan Handling

```typescript
async function handleOrphans(samsaraRoutes: any[]) {
  // Get all Samsara route IDs
  const samsaraIds = new Set(samsaraRoutes.map(r => r.id));
  
  // Find routes in your system with Samsara IDs not in current fetch
  const orphans = await db.routes.findMany({
    where: {
      samsaraRouteId: { not: null },
      samsaraRouteId: { notIn: Array.from(samsaraIds) }
    }
  });
  
  for (const orphan of orphans) {
    // Route deleted in Samsara, handle appropriately
    await db.routes.update({
      where: { id: orphan.id },
      data: {
        samsaraRouteId: null,  // Unlink from Samsara
        status: 'ARCHIVED'     // Or delete based on business logic
      }
    });
  }
}
```

## Status Synchronization

### Status Mapping

```typescript
const SAMSARA_TO_LOCAL_STATUS = {
  'scheduled': 'PENDING',
  'en route': 'ENROUTE',
  'en_route': 'ENROUTE',
  'arrived': 'ARRIVED',
  'departed': 'COMPLETED',
  'completed': 'COMPLETED',
  'skipped': 'CANCELLED'
} as const;

const LOCAL_TO_SAMSARA_STATUS = {
  'PENDING': 'scheduled',
  'ENROUTE': 'en route',
  'ARRIVED': 'arrived',
  'COMPLETED': 'completed',
  'CANCELLED': 'skipped'
} as const;

function mapStatus(
  samsaraState: string,
  direction: 'toLocal' | 'toSamsara'
) {
  const map = direction === 'toLocal' 
    ? SAMSARA_TO_LOCAL_STATUS 
    : LOCAL_TO_SAMSARA_STATUS;
  
  return map[samsaraState] || 'PENDING';
}
```

### Preventing Status Regression

```typescript
async function updateStopStatus(stopId: string, newStatus: string) {
  const currentStop = await db.stops.findUnique({ where: { id: stopId } });
  
  // CRITICAL: Don't revert completed status
  if (currentStop.status === 'COMPLETED' && newStatus !== 'COMPLETED') {
    console.warn(`Preventing status regression for stop ${stopId}`);
    return;
  }
  
  await db.stops.update({
    where: { id: stopId },
    data: { status: newStatus }
  });
}
```

## Conflict Resolution

### Last-Write-Wins

```typescript
async function syncWithConflictResolution(samsaraData: any, localData: any) {
  // Compare timestamps
  const samsaraTime = new Date(samsaraData.updatedAt);
  const localTime = new Date(localData.updatedAt);
  
  if (samsaraTime > localTime) {
    // Samsara is newer, accept their changes
    await updateFromSamsara(samsaraData);
  } else {
    // Local is newer, push to Samsara
    await pushToSamsara(localData);
  }
}
```

### Field-Level Merging

```typescript
async function mergeChanges(samsaraData: any, localData: any) {
  const merged = {
    // Take Samsara's operational data
    status: samsaraData.status,
    arrivalTime: samsaraData.arrivalTime,
    departureTime: samsaraData.departureTime,
    
    // Keep local's business data
    notes: localData.notes,
    internalPriority: localData.internalPriority,
    
    // Merge external IDs
    externalIds: {
      ...samsaraData.externalIds,
      ...localData.externalIds
    }
  };
  
  return merged;
}
```

## Performance Optimization

### Batch Processing

```typescript
async function batchProcessUpdates(updates: any[]) {
  const BATCH_SIZE = 100;
  
  for (let i = 0; i < updates.length; i += BATCH_SIZE) {
    const batch = updates.slice(i, i + BATCH_SIZE);
    await db.$transaction(
      batch.map(update => 
        db.stops.update({
          where: { id: update.id },
          data: update.data
        })
      )
    );
  }
}
```

### Parallel Fetching

```typescript
async function parallelFetch(routeIds: string[]) {
  const CONCURRENCY = 5;
  const results = [];
  
  for (let i = 0; i < routeIds.length; i += CONCURRENCY) {
    const batch = routeIds.slice(i, i + CONCURRENCY);
    const batchResults = await Promise.all(
      batch.map(id => fetch(`/fleet/routes/${id}`))
    );
    results.push(...batchResults);
    
    // Rate limiting delay
    await sleep(200);
  }
  
  return results;
}
```

## Monitoring and Alerting

### Sync Lag Monitoring

```typescript
async function measureSyncLag() {
  const latest = await db.stops.findFirst({
    orderBy: { updatedAt: 'desc' }
  });
  
  const lag = Date.now() - new Date(latest.updatedAt).getTime();
  
  if (lag > 60000) { // More than 1 minute
    await alerting.send({
      message: 'Sync lag exceeds threshold',
      lag: `${lag}ms`
    });
  }
}
```

### Error Tracking

```typescript
async function trackSyncErrors(error: Error, context: any) {
  await db.syncErrors.create({
    data: {
      error: error.message,
      stack: error.stack,
      context: JSON.stringify(context),
      timestamp: new Date()
    }
  });
  
  // Alert if errors spike
  const recentErrors = await db.syncErrors.count({
    where: {
      timestamp: { gte: new Date(Date.now() - 300000) } // Last 5 min
    }
  });
  
  if (recentErrors > 10) {
    await alerting.send({
      message: 'High sync error rate',
      count: recentErrors
    });
  }
}
```
