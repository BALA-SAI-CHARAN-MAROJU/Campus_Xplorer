/**
 * Enhanced Route Service for Campus Explorer
 * Provides accurate routing with multiple API fallbacks and error handling
 */

class RouteService {
    constructor() {
        this.apiKeys = {
            openroute: '5b3ce3597851110001cf6248c0943ad6dce547e59c20450a5741cbaa',
            mapbox: null, // Add Mapbox token if available
            google: null  // Add Google Maps API key if available
        };
        
        this.apiEndpoints = {
            openroute: 'https://api.openrouteservice.org/v2/directions',
            mapbox: 'https://api.mapbox.com/directions/v5/mapbox',
            google: 'https://maps.googleapis.com/maps/api/directions/json'
        };
        
        this.requestCache = new Map();
        this.maxCacheSize = 100;
        this.cacheTimeout = 300000; // 5 minutes
    }
    
    async calculateRoute(start, end, options = {}) {
        const cacheKey = this.generateCacheKey(start, end, options);
        
        // Check cache first
        if (this.requestCache.has(cacheKey)) {
            const cached = this.requestCache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
            this.requestCache.delete(cacheKey);
        }
        
        const routeOptions = {
            profile: options.profile || 'foot-walking',
            campus: options.campus || 'amrita-chennai',
            avoidHighways: true,
            preferPedestrian: true,
            ...options
        };
        
        // Try multiple routing services with fallback
        const services = ['openroute', 'mapbox', 'google'];
        let lastError = null;
        
        for (const service of services) {
            if (!this.apiKeys[service] && service !== 'openroute') continue;
            
            try {
                const routeData = await this.callRoutingService(service, start, end, routeOptions);
                
                // Cache successful result
                this.cacheResult(cacheKey, routeData);
                
                return routeData;
                
            } catch (error) {
                console.warn(`Routing service ${service} failed:`, error);
                lastError = error;
                continue;
            }
        }
        
        // All services failed, return direct route
        console.error('All routing services failed, using direct route');
        return this.createDirectRoute(start, end, lastError);
    }
    
    async callRoutingService(service, start, end, options) {
        switch (service) {
            case 'openroute':
                return await this.callOpenRouteService(start, end, options);
            case 'mapbox':
                return await this.callMapboxService(start, end, options);
            case 'google':
                return await this.callGoogleService(start, end, options);
            default:
                throw new Error(`Unknown routing service: ${service}`);
        }
    }
    
    async callOpenRouteService(start, end, options) {
        const profile = options.profile === 'foot-walking' ? 'foot-walking' : 'driving-car';
        const url = `${this.apiEndpoints.openroute}/${profile}`;
        
        const requestBody = {
            coordinates: [[start[1], start[0]], [end[1], end[0]]],
            format: 'geojson',
            instructions: true,
            geometry_simplify: false,
            continue_straight: false
        };
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': this.apiKeys.openroute,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`OpenRouteService API error: ${response.status}`);
        }
        
        const data = await response.json();
        return this.parseOpenRouteResponse(data, start, end);
    }
    
    parseOpenRouteResponse(data, start, end) {
        if (!data.features || data.features.length === 0) {
            throw new Error('No route found in OpenRouteService response');
        }
        
        const feature = data.features[0];
        const geometry = feature.geometry;
        const properties = feature.properties;
        
        // Convert coordinates from [lng, lat] to [lat, lng]
        const coordinates = geometry.coordinates.map(coord => [coord[1], coord[0]]);
        
        // Parse instructions
        const instructions = [];
        if (properties.segments && properties.segments[0] && properties.segments[0].steps) {
            properties.segments[0].steps.forEach(step => {
                instructions.push({
                    text: step.instruction,
                    distance: step.distance,
                    duration: step.duration,
                    type: step.type
                });
            });
        }
        
        return {
            coordinates,
            distance: properties.summary.distance,
            duration: properties.summary.duration,
            instructions,
            start,
            end,
            service: 'openroute'
        };
    }
}
    
    async callMapboxService(start, end, options) {
        if (!this.apiKeys.mapbox) {
            throw new Error('Mapbox API key not configured');
        }
        
        const profile = options.profile === 'foot-walking' ? 'walking' : 'driving';
        const coordinates = `${start[1]},${start[0]};${end[1]},${end[0]}`;
        
        const url = `${this.apiEndpoints.mapbox}/${profile}/${coordinates}?` +
                   `access_token=${this.apiKeys.mapbox}&` +
                   `geometries=geojson&` +
                   `steps=true&` +
                   `overview=full`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Mapbox API error: ${response.status}`);
        }
        
        const data = await response.json();
        return this.parseMapboxResponse(data, start, end);
    }
    
    parseMapboxResponse(data, start, end) {
        if (!data.routes || data.routes.length === 0) {
            throw new Error('No route found in Mapbox response');
        }
        
        const route = data.routes[0];
        
        // Convert coordinates from [lng, lat] to [lat, lng]
        const coordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
        
        // Parse instructions
        const instructions = [];
        if (route.legs && route.legs[0] && route.legs[0].steps) {
            route.legs[0].steps.forEach(step => {
                instructions.push({
                    text: step.maneuver.instruction,
                    distance: step.distance,
                    duration: step.duration,
                    type: step.maneuver.type
                });
            });
        }
        
        return {
            coordinates,
            distance: route.distance,
            duration: route.duration,
            instructions,
            start,
            end,
            service: 'mapbox'
        };
    }
    
    async callGoogleService(start, end, options) {
        if (!this.apiKeys.google) {
            throw new Error('Google Maps API key not configured');
        }
        
        const mode = options.profile === 'foot-walking' ? 'walking' : 'driving';
        const origin = `${start[0]},${start[1]}`;
        const destination = `${end[0]},${end[1]}`;
        
        const url = `${this.apiEndpoints.google}?` +
                   `origin=${origin}&` +
                   `destination=${destination}&` +
                   `mode=${mode}&` +
                   `key=${this.apiKeys.google}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Google Maps API error: ${response.status}`);
        }
        
        const data = await response.json();
        return this.parseGoogleResponse(data, start, end);
    }
    
    parseGoogleResponse(data, start, end) {
        if (!data.routes || data.routes.length === 0) {
            throw new Error('No route found in Google response');
        }
        
        const route = data.routes[0];
        const leg = route.legs[0];
        
        // Decode polyline
        const coordinates = this.decodePolyline(route.overview_polyline.points);
        
        // Parse instructions
        const instructions = [];
        if (leg.steps) {
            leg.steps.forEach(step => {
                instructions.push({
                    text: step.html_instructions.replace(/<[^>]*>/g, ''), // Strip HTML
                    distance: step.distance.value,
                    duration: step.duration.value,
                    type: step.maneuver || 'straight'
                });
            });
        }
        
        return {
            coordinates,
            distance: leg.distance.value,
            duration: leg.duration.value,
            instructions,
            start,
            end,
            service: 'google'
        };
    }
    
    createDirectRoute(start, end, error) {
        const distance = this.calculateDistance(start, end) * 1000; // Convert to meters
        const duration = (distance / 1.4) * 60; // Assume 1.4 m/s walking speed
        
        return {
            coordinates: [start, end],
            distance,
            duration,
            instructions: [{
                text: `Walk directly to destination (${(distance / 1000).toFixed(2)} km)`,
                distance,
                duration,
                type: 'direct'
            }],
            start,
            end,
            service: 'direct',
            error: error?.message || 'Routing service unavailable'
        };
    }
    
    calculateDistance(coord1, coord2) {
        const R = 6371; // Earth's radius in km
        const dLat = this.deg2rad(coord2[0] - coord1[0]);
        const dLon = this.deg2rad(coord2[1] - coord1[1]);
        
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(this.deg2rad(coord1[0])) * Math.cos(this.deg2rad(coord2[0])) *
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }
    
    deg2rad(deg) {
        return deg * (Math.PI/180);
    }
    
    decodePolyline(encoded) {
        // Google polyline decoding algorithm
        const poly = [];
        let index = 0;
        const len = encoded.length;
        let lat = 0;
        let lng = 0;
        
        while (index < len) {
            let b;
            let shift = 0;
            let result = 0;
            
            do {
                b = encoded.charCodeAt(index++) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);
            
            const dlat = ((result & 1) ? ~(result >> 1) : (result >> 1));
            lat += dlat;
            
            shift = 0;
            result = 0;
            
            do {
                b = encoded.charCodeAt(index++) - 63;
                result |= (b & 0x1f) << shift;
                shift += 5;
            } while (b >= 0x20);
            
            const dlng = ((result & 1) ? ~(result >> 1) : (result >> 1));
            lng += dlng;
            
            poly.push([lat / 1e5, lng / 1e5]);
        }
        
        return poly;
    }
    
    generateCacheKey(start, end, options) {
        return `${start[0]},${start[1]}-${end[0]},${end[1]}-${JSON.stringify(options)}`;
    }
    
    cacheResult(key, data) {
        // Implement LRU cache
        if (this.requestCache.size >= this.maxCacheSize) {
            const firstKey = this.requestCache.keys().next().value;
            this.requestCache.delete(firstKey);
        }
        
        this.requestCache.set(key, {
            data,
            timestamp: Date.now()
        });
    }
    
    clearCache() {
        this.requestCache.clear();
    }
    
    setApiKey(service, key) {
        if (this.apiKeys.hasOwnProperty(service)) {
            this.apiKeys[service] = key;
        }
    }
}

// Location Service for enhanced location management
class LocationService {
    constructor() {
        this.locationCache = new Map();
        this.geocodingService = 'nominatim'; // Free geocoding service
    }
    
    async validateLocation(coordinates, locationName) {
        try {
            // Reverse geocode to validate location
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?` +
                `lat=${coordinates[0]}&lon=${coordinates[1]}&format=json&zoom=18`
            );
            
            if (!response.ok) {
                return { valid: false, reason: 'Geocoding service unavailable' };
            }
            
            const data = await response.json();
            
            return {
                valid: true,
                address: data.display_name,
                confidence: this.calculateLocationConfidence(data, locationName)
            };
            
        } catch (error) {
            return { valid: false, reason: error.message };
        }
    }
    
    calculateLocationConfidence(geocodeData, expectedName) {
        if (!geocodeData || !expectedName) return 0;
        
        const address = geocodeData.display_name.toLowerCase();
        const name = expectedName.toLowerCase();
        
        // Simple confidence calculation based on name matching
        if (address.includes(name)) return 0.9;
        if (name.split(' ').some(word => address.includes(word))) return 0.7;
        
        return 0.5; // Default confidence for valid coordinates
    }
    
    async enhanceLocationData(locations) {
        const enhanced = {};
        
        for (const [name, coordinates] of Object.entries(locations)) {
            const validation = await this.validateLocation(coordinates, name);
            
            enhanced[name] = {
                coordinates,
                validated: validation.valid,
                confidence: validation.confidence || 0,
                address: validation.address,
                lastUpdated: new Date().toISOString()
            };
            
            // Small delay to avoid rate limiting
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        
        return enhanced;
    }
}

// Map Error Handler
class MapErrorHandler {
    constructor() {
        this.errorLog = [];
        this.maxLogSize = 50;
    }
    
    handleError(context, error) {
        const errorInfo = {
            context,
            message: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        };
        
        this.logError(errorInfo);
        this.showUserFriendlyError(context, error);
        
        // Report to analytics if available
        if (window.gtag) {
            window.gtag('event', 'exception', {
                description: `Map Error: ${context} - ${error.message}`,
                fatal: false
            });
        }
    }
    
    logError(errorInfo) {
        this.errorLog.push(errorInfo);
        
        if (this.errorLog.length > this.maxLogSize) {
            this.errorLog.shift();
        }
        
        console.error('Map Error:', errorInfo);
    }
    
    showUserFriendlyError(context, error) {
        const messages = {
            initialization: 'Failed to initialize map. Please refresh the page.',
            mapInitialization: 'Map could not be loaded. Check your internet connection.',
            navigation: 'Unable to calculate route. Please try again.',
            campusSwitch: 'Failed to switch campus. Please try again.',
            routing: 'Route calculation failed. Showing direct path instead.'
        };
        
        const message = messages[context] || 'An unexpected error occurred with the map.';
        
        if (window.showNotification) {
            window.showNotification(message, 'error');
        } else {
            alert(message);
        }
    }
    
    getErrorLog() {
        return [...this.errorLog];
    }
    
    clearErrorLog() {
        this.errorLog = [];
    }
}