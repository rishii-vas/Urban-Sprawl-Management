// Global Config
const API_BASE_URL = 'http://127.0.0.1:8000';

// DOM Elements
const loginForm = document.getElementById('login-form');
const logoutBtn = document.getElementById('logout-btn');

// --- Auth Functions ---

async function login(email, password, department = null) {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, department })
        });

        if (!response.ok) throw new Error('Login failed');

        const data = await response.json();
        // Save to LocalStorage
        localStorage.setItem('token', data.token); // Mock token is just email
        localStorage.setItem('role', data.role);
        localStorage.setItem('user_name', data.name);

        return data;
    } catch (error) {
        console.error('Login Error:', error);
        alert('Invalid credentials');
        return null;
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user_name');
    window.location.href = '../index.html';
}

function checkAuth(requiredRole = null) {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');

    if (!token) {
        window.location.href = 'login-' + (requiredRole || 'user') + '.html'; // Redirect to a login page
        return false;
    }

    if (requiredRole && role !== requiredRole) {
        alert('Access Denied');
        window.location.href = '../index.html';
        return false;
    }
    return true;
}

// --- Data Fetching ---

async function fetchCityOverview(domain = null) {
    let url = `${API_BASE_URL}/city/overview`;
    if (domain) url += `?domain=${domain}`;
    const res = await fetch(url);
    return await res.json();
}

async function fetchWards(domain = null) {
    let url = `${API_BASE_URL}/wards`;
    if (domain) url += `?domain=${domain}`;
    const res = await fetch(url);
    return await res.json();
}

async function submitPrediction(data) {
    const res = await fetch(`${API_BASE_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return await res.json();
}

async function submitFeedback(category, message, ward_name, domain, feedback_type) {
    try {
        const res = await fetch(`${API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ category, message, ward_name, domain, feedback_type })
        });

        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Failed to submit feedback');
        }

        return data;
    } catch (error) {
        console.error("Feedback error:", error);
        alert(`Error: ${error.message}`);
        return null;
    }
}

// --- Map Logic (Leaflet Wrapper) ---
let mapInstance = null;
let wardsLayer = null;

function initMap(elementId, center = [12.9716, 77.5946], zoom = 12) {
    const mapElement = document.getElementById(elementId);
    if (!mapElement) return null;

    // Check if Leaflet is loaded
    if (typeof L === 'undefined') {
        console.error('Leaflet JS not loaded');
        return null;
    }

    // Reuse existing map instance if it exists
    if (mapInstance) {
        // Just invalidate size to ensure it renders correctly (e.g. if container was hidden)
        setTimeout(() => {
            mapInstance.invalidateSize();
        }, 100);
        return mapInstance;
    }

    // Initialize Map
    mapInstance = L.map(elementId).setView(center, zoom);

    // Add OpenStreetMap Tile Layer (Reliable & Free)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(mapInstance);

    // Create a layer group for wards
    wardsLayer = L.layerGroup().addTo(mapInstance);

    // Initial resize check
    setTimeout(() => {
        mapInstance.invalidateSize();
    }, 200);

    return mapInstance;
}

function addWardMarkers(wards, onClick = null) {
    if (!mapInstance || !wardsLayer) {
        // Try to init if not ready
        initMap('map');
        if (!mapInstance || !wardsLayer) return;
    }

    // Clear existing markers FIRST
    wardsLayer.clearLayers();

    wards.forEach(ward => {
        const color = ward.color || '#3b82f6';

        const circle = L.circleMarker([ward.lat, ward.lng], {
            radius: 12,
            fillColor: color,
            color: '#fff',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });

        // Add to LayerGroup instead of map directly
        circle.addTo(wardsLayer);

        circle.bindTooltip(`<b>${ward.name}</b><br>Stress: ${ward.stressLevel}`);

        if (onClick) {
            circle.on('click', () => onClick(ward));
        }
    });

    // Invalidate size strictly after adding markers/switching
    setTimeout(() => {
        mapInstance.invalidateSize();
    }, 100);
}
