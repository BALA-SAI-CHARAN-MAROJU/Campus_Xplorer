/**
 * Enhanced Map Manager for Campus Explorer
 * Fixed: correct class syntax, working navigateToLocation with ORS + fallback
 */

class EnhancedMapManager {
    constructor() {
        this.map = null;
        this.mapInitialized = false;
        this.markers = [];
        this.routeLayer = null;
        this.tspLayer = null;
        this.currentCampus = 'amrita-chennai';
        this.campusData = {};
        this.errorHandler = new MapErrorHandler();
        this.init();
    }

    async init() {
        try {
            await this.loadCampusData();
            this.setupEventListeners();
            this.initializeMapIfNeeded();
        } catch (e) { this.errorHandler.handleError('initialization', e); }
    }

    async loadCampusData() {
        try {
            const r = await fetch('/api/campuses');
            if (!r.ok) throw new Error('HTTP ' + r.status);
            const data = await r.json();
            this.campusData = {};
            data.campuses.forEach(c => { this.campusData[c.id] = c; });
        } catch (e) {
            console.warn('Campus API failed, using fallback:', e);
            this.loadFallbackCampusData();
        }
    }

    loadFallbackCampusData() {
        this.campusData = {
            'amrita-chennai': {
                id: 'amrita-chennai',
                display_name: 'Amrita Chennai Campus',
                center_coordinates: [13.2630, 80.0274],
                locations: {
                    'Academic Block': [13.263018, 80.027427],
                    'Library': [13.262621, 80.026525],
                    'Canteen': [13.262856, 80.028401],
                    'Pond': [13.262198, 80.027673],
                    'AVV Gym for Girls': [13.262141, 80.026830],
                    'Junior Girls Hostel': [13.261993, 80.026421],
                    'Junior Boys Hostel': [13.261805, 80.028076],
                    'Lab Block': [13.262768, 80.028147],
                    'Mechanical Lab': [13.261205, 80.027488],
                    'Volley Ball Court': [13.261009, 80.027530],
                    'Basket Ball Court': [13.260909, 80.027256],
                    'Senior Girls Hostel': [13.260658, 80.028184],
                    'Senior Boys Hostel': [13.260550, 80.027272],
                    '2nd Year Boys Hostel': [13.259570, 80.026694],
                    'Amrita Indoor Stadium': [13.259880, 80.025990],
                    'AVV Gym for Boys': [13.260146, 80.026143],
                    'AVV Ground': [13.259708, 80.025416],
                    'Amrita Vishwa Vidyapeetham': [13.2630, 80.0274],
                    'Night Canteen (Chennai)': [13.260200, 80.027100]
                }
            },
            'amrita-bengaluru': {
                id: 'amrita-bengaluru',
                display_name: 'Amrita Bengaluru Campus',
                center_coordinates: [12.8938021, 77.6759379],
                locations: {
                    'Amrita Vishwa Vidyapeetham (Main)': [12.8938021, 77.6759379],
                    'Amrita University - Kasavanahalli': [12.8968642, 77.6751856],
                    'Amrita Boys Hostel':                [12.8962203, 77.6759762],
                    'Cafeteria':                         [12.8938083, 77.6750777]
                }
            },
            'amrita-coimbatore': {
                display_name: 'Amrita Coimbatore Campus',
                center_coordinates: [10.904074937894901, 76.89836242462337],
                locations: {
                    'Main Campus Building': [10.904074937894901, 76.89836242462337],
                    'Night Canteen (Coimbatore)': [10.9025578753743, 76.89667799731579],
                    'Amrita AARTC': [10.90408547299856, 76.89571240206453],
                    'A2B IT Canteen': [10.905233799859277, 76.89815857675325],
                    'Amrita School of Business': [10.904675439657765, 76.90187075402632],
                    'CIR': [10.905623597889173, 76.90190294053538],
                    'Amriteshwari Hall': [10.900724747825256, 76.90374830038827],
                    'Amrita School of Engineering': [10.900493820979708, 76.9028854093871],
                    'Amrita Swimming Pool': [10.906125938404955, 76.89887868119759],
                    'Anugraha Hall': [10.906628961241658, 76.89738759282525],
                    'Amrita Girls Hostel': [10.907590091795447, 76.89929033136173],
                    'Amrita Central Library': [10.904302473452303, 76.89913481900076]
                }
            }
        };
    }

    initializeMapIfNeeded() {
        const el = document.getElementById('map');
        if (!el || this.mapInitialized) return;
        try {
            const campus = this.campusData[this.currentCampus];
            const center = campus ? campus.center_coordinates : [13.2630, 80.0274];
            this.map = L.map('map', { preferCanvas: true, maxZoom: 20, minZoom: 12 }).setView(center, 17);
            this.addTileLayers();
            this.addCampusMarkers();
            this.mapInitialized = true;
            this.dispatchMapEvent('mapInitialized');
        } catch (e) { this.errorHandler.handleError('mapInitialization', e); }
    }

    addTileLayers() {
        const osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors', maxZoom: 20
        });
        const sat = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '&copy; Esri', maxZoom: 20
        });
        osm.addTo(this.map);
        L.control.layers({ 'Street Map': osm, 'Satellite': sat }).addTo(this.map);
    }

    addCampusMarkers() {
        this.clearMarkers();
        const campus = this.campusData[this.currentCampus];
        if (!campus || !campus.locations) return;
        Object.entries(campus.locations).forEach(([name, coords]) => {
            const m = L.marker(coords, { icon: this.createCustomIcon(name) }).addTo(this.map);
            m.bindPopup(this.createPopupContent(name, coords));
            this.markers.push(m);
        });
    }

    createCustomIcon(name) {
        return L.divIcon({
            html: '<div class="enhanced-marker"><i class="fas ' + this.getIconClass(name) + '"></i></div>',
            className: 'enhanced-marker-container',
            iconSize: [32, 32], iconAnchor: [16, 32], popupAnchor: [0, -32]
        });
    }

    getIconClass(name) {
        const map = {
            'library': 'fa-book', 'canteen': 'fa-utensils', 'gym': 'fa-dumbbell',
            'hostel': 'fa-bed', 'lab': 'fa-flask', 'academic': 'fa-graduation-cap',
            'stadium': 'fa-running', 'ground': 'fa-futbol', 'court': 'fa-basketball-ball',
            'pool': 'fa-swimming-pool', 'hall': 'fa-building', 'business': 'fa-briefcase',
            'engineering': 'fa-cogs', 'aartc': 'fa-microchip', 'cir': 'fa-flask'
        };
        const lower = name.toLowerCase();
        for (const [k, v] of Object.entries(map)) { if (lower.includes(k)) return v; }
        return 'fa-map-marker-alt';
    }

    createPopupContent(name, coords) {
        return '<div class="enhanced-popup"><div class="popup-header"><h4>' + name + '</h4></div>' +
               '<div class="popup-body"><p><i class="fas fa-map-marker-alt"></i> ' +
               coords[0].toFixed(6) + ', ' + coords[1].toFixed(6) + '</p>' +
               '<div class="popup-actions"><button onclick="window.enhancedMapManager.navigateToLocation(\'' + name.replace(/'/g, "\\'") + '\')" class="popup-btn primary">' +
               '<i class="fas fa-directions"></i> Get Directions</button></div></div></div>';
    }

    async switchToCampus(campusId) {
        if (!this.campusData[campusId]) return;
        this.currentCampus = campusId;
        if (this.mapInitialized && this.map) {
            this.map.flyTo(this.campusData[campusId].center_coordinates, 16, { animate: true, duration: 1.5 });
            setTimeout(() => this.addCampusMarkers(), 1600);
            this.clearRoutes();
        }
        this.dispatchMapEvent('campusChanged', { campusId });
    }

    async navigateToLocation(locationName, startLocation) {
        try {
            const mapEl = document.getElementById('map');
            if (mapEl) mapEl.style.display = 'block';
            if (!this.mapInitialized) {
                this.initializeMapIfNeeded();
                await new Promise(r => setTimeout(r, 600));
            }
            const campus = this.campusData[this.currentCampus];
            if (!campus) throw new Error('Campus data not loaded');
            const destination = campus.locations[locationName];
            if (!destination) throw new Error('Location "' + locationName + '" not found');
            const startCoords = startLocation ? campus.locations[startLocation] : this.getDefaultStartLocation();
            if (!startCoords) throw new Error('No valid start location');

            this.showRouteLoading(true);
            let routeData = null;
            try { routeData = await this.fetchOrsRoute(startCoords, destination); }
            catch (e) { console.warn('ORS failed, using straight-line:', e); }

            this.clearRoutes();
            if (routeData && routeData.coordinates && routeData.coordinates.length > 1) {
                this.routeLayer = L.polyline(routeData.coordinates, { color: '#4f46e5', weight: 6, opacity: 0.85 }).addTo(this.map);
                this.map.fitBounds(this.routeLayer.getBounds().pad(0.15));
                this.showRouteInfo(routeData, locationName);
            } else {
                this.routeLayer = L.polyline([startCoords, destination], { color: '#ef4444', weight: 4, opacity: 0.75, dashArray: '10, 6' }).addTo(this.map);
                this.map.fitBounds(this.routeLayer.getBounds().pad(0.2));
                this.showRouteInfo({ distance: this.haversineDistance(startCoords, destination), duration: null, instructions: [] }, locationName);
            }
            this.addRouteMarkers(startCoords, destination, locationName);
        } catch (e) {
            this.errorHandler.handleError('navigation', e);
            this.showRouteLoading(false);
        }
    }

    async fetchOrsRoute(start, end) {
        const key = '5b3ce3597851110001cf6248c0943ad6dce547e59c20450a5741cbaa';
        const url = 'https://api.openrouteservice.org/v2/directions/foot-walking?api_key=' + key +
                    '&start=' + start[1] + ',' + start[0] + '&end=' + end[1] + ',' + end[0];
        const r = await fetch(url);
        if (!r.ok) throw new Error('ORS HTTP ' + r.status);
        const data = await r.json();
        const feat = data.features && data.features[0];
        if (!feat) throw new Error('No route in ORS response');
        const coords = feat.geometry.coordinates.map(c => [c[1], c[0]]);
        const summary = feat.properties.summary;
        const steps = (feat.properties.segments[0] || {}).steps || [];
        return {
            coordinates: coords,
            distance: summary.distance,
            duration: summary.duration,
            instructions: steps.map(s => ({ text: s.instruction, distance: s.distance }))
        };
    }

    haversineDistance(a, b) {
        const R = 6371000, toRad = d => d * Math.PI / 180;
        const dLat = toRad(b[0] - a[0]), dLng = toRad(b[1] - a[1]);
        const x = Math.sin(dLat/2)**2 + Math.cos(toRad(a[0]))*Math.cos(toRad(b[0]))*Math.sin(dLng/2)**2;
        return R * 2 * Math.atan2(Math.sqrt(x), Math.sqrt(1-x));
    }

    getDefaultStartLocation() {
        const campus = this.campusData[this.currentCampus];
        if (!campus || !campus.locations) return null;
        const priorities = ['Main Campus Building', 'Academic Block', 'Main Building', 'Entrance'];
        for (const p of priorities) {
            for (const n of Object.keys(campus.locations)) {
                if (n.includes(p)) return campus.locations[n];
            }
        }
        return Object.values(campus.locations)[0] || null;
    }

    addRouteMarkers(start, end, destName) {
        const sm = L.marker(start, { icon: L.divIcon({ html: '<div class="route-marker start-marker"><i class="fas fa-play"></i></div>', className: 'route-marker-container', iconSize: [30,30] }) }).addTo(this.map);
        sm.bindTooltip('Start', { permanent: false, direction: 'top' });
        const em = L.marker(end, { icon: L.divIcon({ html: '<div class="route-marker end-marker"><i class="fas fa-flag-checkered"></i></div>', className: 'route-marker-container', iconSize: [30,30] }) }).addTo(this.map);
        em.bindTooltip(destName, { permanent: false, direction: 'top' });
        this.markers.push(sm, em);
    }

    showRouteInfo(routeData, destName) {
        const el = document.getElementById('route-info');
        if (!el) return;
        const dist = routeData.distance ? (routeData.distance/1000).toFixed(2)+' km' : 'N/A';
        const dur  = routeData.duration ? Math.ceil(routeData.duration/60)+' min' : 'N/A';
        const instrHtml = (routeData.instructions && routeData.instructions.length)
            ? '<div class="route-instructions"><h5><i class="fas fa-list-ol"></i> Directions</h5><ol class="instructions-list">' +
              routeData.instructions.map(s => '<li class="instruction-item"><div class="instruction-text">'+s.text+'</div><div class="instruction-distance">'+(s.distance/1000).toFixed(2)+' km</div></li>').join('') +
              '</ol></div>' : '';
        el.innerHTML = '<div class="enhanced-route-info"><div class="route-info-header"><h4><i class="fas fa-route"></i> Route to '+destName+'</h4>' +
            '<button onclick="window.enhancedMapManager.clearRoutes()" class="close-route-btn"><i class="fas fa-times"></i></button></div>' +
            '<div class="route-stats"><div class="route-stat"><div class="stat-icon"><i class="fas fa-ruler"></i></div><div class="stat-info"><div class="stat-label">Distance</div><div class="stat-value">'+dist+'</div></div></div>' +
            '<div class="route-stat"><div class="stat-icon"><i class="fas fa-clock"></i></div><div class="stat-info"><div class="stat-label">Walking Time</div><div class="stat-value">'+dur+'</div></div></div></div>' +
            instrHtml + '</div>';
        el.style.display = 'block';
    }

    showRouteLoading(show) {
        const el = document.getElementById('route-info');
        if (!el) return;
        if (show) { el.innerHTML = '<div class="route-loading"><div class="loading-spinner"></div><p>Calculating route...</p></div>'; el.style.display = 'block'; }
        else { el.style.display = 'none'; }
    }

    clearRoutes() {
        if (this.routeLayer && this.map) { this.map.removeLayer(this.routeLayer); this.routeLayer = null; }
        if (this.tspLayer  && this.map) { this.map.removeLayer(this.tspLayer);   this.tspLayer  = null; }
        this.markers = this.markers.filter(m => {
            if (m.options.icon && m.options.icon.options.className === 'route-marker-container') {
                if (this.map) this.map.removeLayer(m); return false;
            }
            return true;
        });
        const el = document.getElementById('route-info');
        if (el) el.style.display = 'none';
    }

    clearMarkers() {
        this.markers.forEach(m => { if (this.map) this.map.removeLayer(m); });
        this.markers = [];
    }

    shareLocation(name) {
        const url = window.location.origin + '?campus=' + this.currentCampus + '&location=' + encodeURIComponent(name);
        if (navigator.share) { navigator.share({ title: name, url }); }
        else { navigator.clipboard.writeText(url).then(() => { if (window.showNotification) window.showNotification('Link copied!', 'success'); }); }
    }

    setupEventListeners() {
        document.addEventListener('campusChanged', e => this.switchToCampus(e.detail.campusId));
        document.addEventListener('navigateToLocation', e => this.navigateToLocation(e.detail.locationName, e.detail.startLocation));
        window.addEventListener('storage', async (e) => {
            if (e.key !== 'locationsUpdated') return;
            try {
                const payload = JSON.parse(e.newValue);
                await this.loadCampusData();
                if (this.mapInitialized && payload.campusId === this.currentCampus) this.addCampusMarkers();
            } catch (err) { console.warn('Failed to refresh after location update:', err); }
        });
        window.addEventListener('locationsUpdated', async (e) => {
            try {
                await this.loadCampusData();
                if (this.mapInitialized && e.detail.campusId === this.currentCampus) this.addCampusMarkers();
            } catch (err) { console.warn('locationsUpdated error:', err); }
        });
    }

    dispatchMapEvent(name, detail = {}) { document.dispatchEvent(new CustomEvent(name, { detail })); }
    showNotification(msg, type) { if (window.showNotification) window.showNotification(msg, type); }
    getMap()           { return this.map; }
    isInitialized()    { return this.mapInitialized; }
    getCurrentCampus() { return this.currentCampus; }
    getCampusData(id)  { return id ? this.campusData[id] : this.campusData; }
}
