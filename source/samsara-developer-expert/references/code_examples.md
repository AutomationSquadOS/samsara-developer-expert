# Production Code Examples

Real-world, production-tested code patterns for Samsara API integration.

## Complete Sync Service

### TypeScript Sync Implementation

```typescript
import axios, { AxiosInstance } from 'axios';

interface SamsaraSyncConfig {
  baseURL: string;
  apiToken: string;
  rateLimitPerSecond: number;
  rateLimitPerMinute: number;
}

class SamsaraSyncService {
  private client: AxiosInstance;
  private rateLimiter: RateLimiter;
  
  constructor(config: SamsaraSyncConfig) {
    this.client = axios.create({
      baseURL: config.baseURL,
      headers: {
        'Authorization': `Bearer ${config.apiToken}`,
        'Content-Type': 'application/json'
      }
    });
    
    this.rateLimiter = new RateLimiter(
      config.rateLimitPerSecond,
      config.rateLimitPerMinute
    );
  }
  
  /**
   * Sync drivers from Samsara to local database
   */
  async syncDriversFromSamsara() {
    await this.rateLimiter.throttle();
    
    const response = await this.client.get('/fleet/drivers');
    const samsaraDrivers = response.data.data;
    
    for (const samsaraDriver of samsaraDrivers) {
      // Skip excluded drivers (example: test accounts)
      if (this.isExcludedDriver(samsaraDriver.name)) {
        continue;
      }
      
      // Upsert driver
      await db.drivers.upsert({
        where: { samsaraId: samsaraDriver.id },
        update: {
          name: samsaraDriver.name,
          username: samsaraDriver.username,
          phone: samsaraDriver.phone,
          email: samsaraDriver.email,
          externalIds: samsaraDriver.externalIds,
          updatedAt: new Date()
        },
        create: {
          samsaraId: samsaraDriver.id,
          name: samsaraDriver.name,
          username: samsaraDriver.username,
          phone: samsaraDriver.phone,
          email: samsaraDriver.email,
          externalIds: samsaraDriver.externalIds
        }
      });
    }
    
    console.log(`Synced ${samsaraDrivers.length} drivers`);
  }
  
  /**
   * Sync routes for a date range
   */
  async syncRoutesFromSamsara(startDate: Date, endDate: Date) {
    const startTime = startDate.toISOString();
    const endTime = endDate.toISOString();
    
    await this.rateLimiter.throttle();
    
    const response = await this.client.get('/fleet/routes', {
      params: { startTime, endTime }
    });
    
    const routes = response.data.data || [];
    
    for (const samsaraRoute of routes) {
      await this.syncSingleRoute(samsaraRoute);
    }
    
    console.log(`Synced ${routes.length} routes`);
  }
  
  /**
   * Sync a single route with full stop details
   */
  private async syncSingleRoute(samsaraRoute: any) {
    // Find existing route by external ID
    let localRoute = await this.findMatchingRoute(samsaraRoute);
    
    if (!localRoute) {
      // Create new route
      localRoute = await db.routes.create({
        data: {
          samsaraRouteId: samsaraRoute.id,
          name: samsaraRoute.name,
          driverId: await this.findDriverBySamsaraId(samsaraRoute.driverId),
          vehicleId: await this.findVehicleBySamsaraId(samsaraRoute.vehicleId),
          scheduledStartTime: new Date(samsaraRoute.scheduledStartTime),
          status: this.mapRouteStatus(samsaraRoute.status),
          externalIds: samsaraRoute.externalIds
        }
      });
    } else {
      // Update existing route
      await db.routes.update({
        where: { id: localRoute.id },
        data: {
          name: samsaraRoute.name,
          driverId: await this.findDriverBySamsaraId(samsaraRoute.driverId),
          status: this.mapRouteStatus(samsaraRoute.status),
          updatedAt: new Date()
        }
      });
    }
    
    // Sync stops
    await this.syncRouteStops(localRoute.id, samsaraRoute.stops || []);
  }
  
  /**
   * Sync stops for a route, handling creates, updates, and deletes
   */
  private async syncRouteStops(routeId: string, samsaraStops: any[]) {
    const seenSamsaraJobIds = new Set<string>();
    
    // Get current stops in local database
    const currentStops = await db.containerActions.findMany({
      where: { routeId }
    });
    
    // Process each Samsara stop
    for (const samsaraStop of samsaraStops) {
      seenSamsaraJobIds.add(samsaraStop.id);
      
      // Try to find matching local action
      let action = await this.findMatchingStop(samsaraStop, routeId);
      
      if (action) {
        // Update existing stop
        await this.updateStop(action.id, samsaraStop);
      } else {
        // Import new stop from Samsara (two-way sync)
        await this.createStopFromSamsara(routeId, samsaraStop);
      }
    }
    
    // Handle orphans (stops in local DB but not in Samsara)
    const orphans = currentStops.filter(
      stop => !seenSamsaraJobIds.has(stop.samsaraJobId)
    );
    
    for (const orphan of orphans) {
      // Unschedule orphaned stops
      await db.containerActions.update({
        where: { id: orphan.id },
        data: {
          routeId: null,
          samsaraJobId: null,
          status: 'PENDING'
        }
      });
    }
  }
  
  /**
   * Update stop with data from Samsara
   */
  private async updateStop(actionId: string, samsaraStop: any) {
    const currentAction = await db.containerActions.findUnique({
      where: { id: actionId }
    });
    
    const newStatus = this.mapStopState(samsaraStop.state);
    
    // GUARD: Don't revert completed status
    if (currentAction.status === 'COMPLETED' && newStatus !== 'COMPLETED') {
      console.warn(`Skipping status update for completed stop ${actionId}`);
      return;
    }
    
    await db.containerActions.update({
      where: { id: actionId },
      data: {
        status: newStatus,
        arrivalTime: samsaraStop.arrivalTime 
          ? new Date(samsaraStop.arrivalTime) 
          : null,
        departureTime: samsaraStop.departureTime 
          ? new Date(samsaraStop.departureTime) 
          : null,
        notes: samsaraStop.notes || currentAction.notes
      }
    });
  }
  
  /**
   * Create stop from Samsara data (two-way sync)
   */
  private async createStopFromSamsara(routeId: string, samsaraStop: any) {
    // Parse address
    const address = this.parseAddress(samsaraStop);
    
    // Get or create service request
    const request = await this.getOrCreateServiceRequest(address);
    
    // Create container action
    await db.containerActions.create({
      data: {
        routeId,
        samsaraJobId: samsaraStop.id,
        serviceRequestId: request.id,
        actionType: 'DUMP_RETURN', // Default type
        status: this.mapStopState(samsaraStop.state),
        notes: samsaraStop.notes,
        scheduledDate: new Date(samsaraStop.scheduledArrivalTime),
        externalIds: samsaraStop.externalIds
      }
    });
  }
  
  /**
   * Push route from local system to Samsara
   */
  async pushRouteToSamsara(localRoute: any, containerActions: any[]) {
    const externalId = localRoute.externalIds?.cmc || localRoute.id;
    
    if (localRoute.samsaraRouteId) {
      // Update existing route
      await this.rateLimiter.throttle();
      
      // CRITICAL: Fetch existing first to get stop IDs
      const existing = await this.client.get(
        `/fleet/routes/${localRoute.samsaraRouteId}`
      );
      
      const existingStopsMap = new Map(
        existing.data.stops.map(s => [s.externalIds?.cmc, s])
      );
      
      // Build stops array, preserving IDs
      const stops = containerActions.map(action => {
        const existingStop = existingStopsMap.get(action.id);
        
        return {
          ...(existingStop?.id ? { id: existingStop.id } : {}),
          address: {
            formattedAddress: this.formatAddress(action.serviceRequest)
          },
          scheduledArrivalTime: action.scheduledDate.toISOString(),
          notes: action.notes || '',
          externalIds: { cmc: action.id }
        };
      });
      
      // PATCH route
      await this.client.patch(
        `/fleet/routes/${localRoute.samsaraRouteId}`,
        { stops }
      );
      
    } else {
      // Create new route
      await this.rateLimiter.throttle();
      
      const route = {
        name: localRoute.name,
        driverId: localRoute.driver.samsaraId,
        vehicleId: localRoute.vehicle.samsaraId,
        scheduledStartTime: localRoute.scheduledStartTime.toISOString(),
        stops: containerActions.map(action => ({
          address: {
            formattedAddress: this.formatAddress(action.serviceRequest)
          },
          scheduledArrivalTime: action.scheduledDate.toISOString(),
          notes: action.notes || '',
          externalIds: { cmc: action.id }
        })),
        externalIds: { cmc: externalId }
      };
      
      const response = await this.client.post('/fleet/routes', route);
      
      // Save Samsara route ID
      await db.routes.update({
        where: { id: localRoute.id },
        data: { samsaraRouteId: response.data.id }
      });
    }
  }
  
  /**
   * Helpers
   */
  
  private async findMatchingRoute(samsaraRoute: any) {
    // Try external ID first
    if (samsaraRoute.externalIds?.cmc) {
      const route = await db.routes.findFirst({
        where: {
          externalIds: {
            path: ['cmc'],
            equals: samsaraRoute.externalIds.cmc
          }
        }
      });
      if (route) return route;
    }
    
    // Fallback to Samsara ID
    return await db.routes.findFirst({
      where: { samsaraRouteId: samsaraRoute.id }
    });
  }
  
  private async findMatchingStop(samsaraStop: any, routeId: string) {
    // Try external ID
    if (samsaraStop.externalIds?.cmc) {
      const stop = await db.containerActions.findFirst({
        where: {
          routeId,
          externalIds: {
            path: ['cmc'],
            equals: samsaraStop.externalIds.cmc
          }
        }
      });
      if (stop) return stop;
    }
    
    // Fallback to Samsara job ID
    return await db.containerActions.findFirst({
      where: { samsaraJobId: samsaraStop.id, routeId }
    });
  }
  
  private mapStopState(state: string): string {
    const map: Record<string, string> = {
      'scheduled': 'PENDING',
      'en route': 'ENROUTE',
      'en_route': 'ENROUTE',
      'arrived': 'ARRIVED',
      'departed': 'COMPLETED',
      'completed': 'COMPLETED',
      'skipped': 'CANCELLED'
    };
    
    return map[state] || 'PENDING';
  }
  
  private parseAddress(stop: any) {
    if (stop.address?.formattedAddress) {
      const parts = stop.address.formattedAddress.split(',').map(s => s.trim());
      
      if (parts.length >= 3) {
        const [address1, city, stateZip] = parts;
        const match = stateZip.match(/([A-Z]{2})\s+(\d{5})/);
        
        return {
          address1,
          city,
          state: match ? match[1] : null,
          zipCode: match ? match[2] : null
        };
      }
    }
    
    return {
      address1: stop.name || 'Unknown Location',
      city: null,
      state: null,
      zipCode: null
    };
  }
  
  private formatAddress(serviceRequest: any): string {
    const parts = [
      serviceRequest.address1,
      serviceRequest.city,
      `${serviceRequest.state} ${serviceRequest.zipCode}`
    ].filter(Boolean);
    
    return parts.join(', ');
  }
  
  private isExcludedDriver(name: string): boolean {
    const excluded = ['test', 'demo', 'inactive'];
    return excluded.some(term => 
      name.toLowerCase().includes(term)
    );
  }
}
```

## Rate Limiter Class

```typescript
class RateLimiter {
  private requestTimes: number[] = [];
  private perSecondLimit: number;
  private perMinuteLimit: number;
  
  constructor(perSecondLimit = 5, perMinuteLimit = 300) {
    this.perSecondLimit = perSecondLimit;
    this.perMinuteLimit = perMinuteLimit;
  }
  
  async throttle(): Promise<void> {
    const now = Date.now();
    
    // Remove old requests (older than 1 minute)
    this.requestTimes = this.requestTimes.filter(
      time => now - time < 60000
    );
    
    // Check per-second limit
    const recentRequests = this.requestTimes.filter(
      time => now - time < 1000
    );
    
    if (recentRequests.length >= this.perSecondLimit) {
      const oldestRecent = Math.min(...recentRequests);
      const waitTime = 1000 - (now - oldestRecent) + 50;
      await this.sleep(waitTime);
    }
    
    // Check per-minute limit
    if (this.requestTimes.length >= this.perMinuteLimit) {
      const oldestRequest = Math.min(...this.requestTimes);
      const waitTime = 60000 - (now - oldestRequest) + 100;
      await this.sleep(waitTime);
    }
    
    // Record this request
    this.requestTimes.push(Date.now());
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Feed Synchronization

```typescript
class VehicleStatsFeed {
  private cursor: string | null = null;
  private samsara: SamsaraSyncService;
  
  constructor(samsara: SamsaraSyncService) {
    this.samsara = samsara;
  }
  
  async start(intervalMs = 10000) {
    // Load saved cursor
    this.cursor = await this.loadCursor();
    
    // Poll every intervalMs
    setInterval(() => this.poll(), intervalMs);
  }
  
  private async poll() {
    try {
      const params: any = {
        types: ['gps', 'engineStates', 'fuelPercents'],
        decorations: ['gps']
      };
      
      if (this.cursor) {
        params.after = this.cursor;
      }
      
      const response = await this.samsara.client.get(
        '/fleet/vehicles/stats/feed',
        { params }
      );
      
      const data = response.data;
      
      // Process updates
      for (const stat of data.data || []) {
        await this.processVehicleStat(stat);
      }
      
      // Save cursor
      if (data.pagination?.endCursor) {
        this.cursor = data.pagination.endCursor;
        await this.saveCursor(this.cursor);
      }
      
    } catch (error) {
      console.error('Feed poll error:', error);
    }
  }
  
  private async processVehicleStat(stat: any) {
    await db.vehicles.upsert({
      where: { samsaraId: stat.id },
      update: {
        latitude: stat.gps?.latitude,
        longitude: stat.gps?.longitude,
        speed: stat.gps?.speedMilesPerHour,
        heading: stat.gps?.headingDegrees,
        engineState: stat.engineStates?.[0]?.value,
        fuelPercent: stat.fuelPercents?.[0]?.value,
        lastUpdate: new Date()
      },
      create: {
        samsaraId: stat.id,
        latitude: stat.gps?.latitude,
        longitude: stat.gps?.longitude,
        speed: stat.gps?.speedMilesPerHour
      }
    });
  }
  
  private async loadCursor(): Promise<string | null> {
    const state = await db.syncState.findUnique({
      where: { feed: 'vehicle_stats' }
    });
    return state?.cursor || null;
  }
  
  private async saveCursor(cursor: string) {
    await db.syncState.upsert({
      where: { feed: 'vehicle_stats' },
      update: { cursor },
      create: { feed: 'vehicle_stats', cursor }
    });
  }
}
```

## Express API Endpoints

```typescript
import express from 'express';

const app = express();
const samsara = new SamsaraSyncService(config);

// Manual sync trigger
app.post('/api/samsara/sync-routes', async (req, res) => {
  try {
    const { date } = req.body;
    const startDate = new Date(date);
    const endDate = new Date(date);
    endDate.setHours(23, 59, 59, 999);
    
    await samsara.syncRoutesFromSamsara(startDate, endDate);
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get unscheduled actions
app.get('/api/container-actions/unscheduled', async (req, res) => {
  const actions = await db.containerActions.findMany({
    where: {
      isSchedulable: true,
      isAddOn: false,
      status: 'PENDING',
      routeId: null
    },
    include: {
      serviceRequest: true,
      customer: true
    }
  });
  
  res.json(actions);
});

// Assign action to route
app.post('/api/container-actions/:id/assign-route', async (req, res) => {
  const { id } = req.params;
  const { routeId } = req.body;
  
  const action = await db.containerActions.update({
    where: { id },
    data: { routeId }
  });
  
  // Push to Samsara
  const route = await db.routes.findUnique({
    where: { id: routeId },
    include: { containerActions: true }
  });
  
  await samsara.pushRouteToSamsara(route, route.containerActions);
  
  res.json({ success: true, action });
});
```

## Usage Example

```typescript
// Initialize service
const samsara = new SamsaraSyncService({
  baseURL: 'https://api.samsara.com',
  apiToken: process.env.SAMSARA_API_TOKEN,
  rateLimitPerSecond: 5,
  rateLimitPerMinute: 300
});

// Sync drivers and vehicles on startup
await samsara.syncDriversFromSamsara();
await samsara.syncVehiclesFromSamsara();

// Sync routes for today
const today = new Date();
await samsara.syncRoutesFromSamsara(today, today);

// Start vehicle stats feed
const vehicleFeed = new VehicleStatsFeed(samsara);
await vehicleFeed.start(10000); // Poll every 10 seconds

// Push local route to Samsara
const route = await db.routes.findUnique({
  where: { id: 'route_123' },
  include: { 
    containerActions: true,
    driver: true,
    vehicle: true
  }
});

await samsara.pushRouteToSamsara(route, route.containerActions);
```
