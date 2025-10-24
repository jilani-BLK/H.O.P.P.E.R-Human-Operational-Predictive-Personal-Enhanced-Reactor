/**
 * HOPPER WebSocket Client
 * Connecte l'interface neuronale au serveur temps réel
 */

class NeuralWebSocketClient {
    constructor() {
        this.ws = null;
        this.reconnectInterval = 3000;
        this.reconnectTimer = null;
        this.connected = false;
        this.serverUrl = 'ws://localhost:5050/ws/neural';
        
        this.stats = {
            eventsReceived: 0,
            lastEventTime: null,
            services: {}
        };

        this.connect();
    }

    connect() {
        console.log(`🔌 Connecting to ${this.serverUrl}...`);
        
        try {
            this.ws = new WebSocket(this.serverUrl);
            
            this.ws.onopen = () => this.onOpen();
            this.ws.onmessage = (event) => this.onMessage(event);
            this.ws.onerror = (error) => this.onError(error);
            this.ws.onclose = () => this.onClose();
            
        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            this.scheduleReconnect();
        }
    }

    onOpen() {
        console.log('✅ WebSocket connected');
        this.connected = true;
        this.updateConnectionStatus(true);
        
        // Clear reconnect timer
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }

        // Send initial ping
        this.send({ type: 'ping' });
    }

    onMessage(event) {
        try {
            const data = JSON.parse(event.data);
            this.handleEvent(data);
            
            this.stats.eventsReceived++;
            this.stats.lastEventTime = Date.now();
            
        } catch (error) {
            console.error('❌ Failed to parse message:', error);
        }
    }

    handleEvent(data) {
        const { type, payload } = data;
        
        console.log(`📡 Event received: ${type}`, payload);
        
        switch (type) {
            case 'neural_activity':
                this.handleNeuralActivity(payload);
                break;
            
            case 'service_event':
                this.handleServiceEvent(payload);
                break;
            
            case 'stats':
                this.handleStats(payload);
                break;
            
            case 'voice_activity':
                this.handleVoiceActivity(payload);
                break;
            
            case 'pong':
                this.updateLatency(payload.latency);
                break;
            
            default:
                console.log('Unknown event type:', type);
        }
    }

    handleNeuralActivity(payload) {
        const { event_type, intensity, metadata } = payload;
        
        // Pulse neural network
        if (window.neuralNet) {
            window.neuralNet.pulseActivity(event_type, intensity);
        }
        
        // Log activity
        this.addLogEntry(event_type, metadata);
        
        // Update HUD
        this.updateActivityLevel(event_type);
    }

    handleServiceEvent(payload) {
        const { service, status, duration } = payload;
        
        // Track service status
        this.stats.services[service] = {
            status: status,
            lastSeen: Date.now(),
            duration: duration
        };
        
        // Update services display
        this.updateServicesStatus();
        
        // Log
        this.addLogEntry('service', {
            service: service,
            status: status,
            duration: duration ? `${duration.toFixed(2)}s` : null
        });
    }

    handleStats(payload) {
        // Update HUD stats
        if (payload.neurons) {
            document.getElementById('neurons-count').textContent = 
                `${payload.neurons.active}/${payload.neurons.total}`;
        }
        
        if (payload.connections) {
            document.getElementById('connections-count').textContent = 
                `${payload.connections.active}/${payload.connections.total}`;
        }
    }

    handleVoiceActivity(payload) {
        const { speaking, text, duration } = payload;
        
        if (speaking) {
            // When HOPPER speaks, accelerate neurons
            if (window.neuralNet) {
                window.neuralNet.config.pulseSpeed = 4.0; // Double speed
                window.neuralNet.activateRandomNeurons(15, 1.5);
            }
            
            this.addLogEntry('tts', {
                text: text ? text.substring(0, 50) + '...' : 'Speaking',
                duration: duration
            });
        } else {
            // Return to normal speed
            if (window.neuralNet) {
                window.neuralNet.config.pulseSpeed = 2.0;
            }
        }
    }

    updateActivityLevel(eventType) {
        const activityMap = {
            'stt': 'Listening 👂',
            'llm': 'Thinking 🧠',
            'tts': 'Speaking 🗣️',
            'dispatch': 'Processing ⚡',
            'service': 'Working 🔧'
        };
        
        const activity = activityMap[eventType] || 'Active';
        document.getElementById('activity-level').textContent = activity;
        
        // Reset to idle after delay
        setTimeout(() => {
            document.getElementById('activity-level').textContent = 'Idle';
        }, 2000);
    }

    updateServicesStatus() {
        const services = Object.keys(this.stats.services);
        const healthyServices = services.filter(s => 
            this.stats.services[s].status === 'healthy' ||
            this.stats.services[s].status === 'active'
        );
        
        document.getElementById('services-status').textContent = 
            `${healthyServices.length}/${services.length}`;
    }

    updateLatency(latency) {
        document.getElementById('latency').textContent = `${latency.toFixed(0)}ms`;
    }

    addLogEntry(type, metadata) {
        const logEntries = document.getElementById('log-entries');
        const timestamp = new Date().toLocaleTimeString();
        
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        
        let text = `[${timestamp}] ${type.toUpperCase()}`;
        
        if (metadata) {
            if (metadata.text) {
                text += `: ${metadata.text}`;
            } else if (metadata.service) {
                text += `: ${metadata.service} - ${metadata.status}`;
                if (metadata.duration) {
                    text += ` (${metadata.duration})`;
                }
            } else {
                text += `: ${JSON.stringify(metadata)}`;
            }
        }
        
        entry.textContent = text;
        logEntries.insertBefore(entry, logEntries.firstChild);
        
        // Keep only last 50 entries
        while (logEntries.children.length > 50) {
            logEntries.removeChild(logEntries.lastChild);
        }
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        
        if (connected) {
            statusEl.className = 'connected';
            statusEl.innerHTML = '<span class="pulse">✅ Connecté</span>';
        } else {
            statusEl.className = '';
            statusEl.innerHTML = '<span class="pulse">⚠️ Déconnecté</span>';
        }
    }

    onError(error) {
        console.error('❌ WebSocket error:', error);
    }

    onClose() {
        console.log('🔌 WebSocket disconnected');
        this.connected = false;
        this.updateConnectionStatus(false);
        
        // Schedule reconnect
        this.scheduleReconnect();
    }

    scheduleReconnect() {
        if (this.reconnectTimer) return;
        
        console.log(`⏳ Reconnecting in ${this.reconnectInterval/1000}s...`);
        
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connect();
        }, this.reconnectInterval);
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    // Send periodic stats request
    startStatsPolling(interval = 1000) {
        setInterval(() => {
            if (this.connected && window.neuralNet) {
                const stats = window.neuralNet.getStats();
                this.send({
                    type: 'client_stats',
                    payload: stats
                });
            }
        }, interval);
    }

    // Send periodic ping
    startPing(interval = 5000) {
        setInterval(() => {
            if (this.connected) {
                this.send({
                    type: 'ping',
                    payload: { timestamp: Date.now() }
                });
            }
        }, interval);
    }
}

// Initialize WebSocket client
const wsClient = new NeuralWebSocketClient();

// Start polling
wsClient.startStatsPolling(1000);
wsClient.startPing(5000);

// Simulate activity for testing (remove in production)
if (window.location.search.includes('demo=true')) {
    console.log('🎭 Demo mode enabled - simulating activity');
    
    setInterval(() => {
        const events = ['stt', 'llm', 'tts', 'dispatch', 'service'];
        const randomEvent = events[Math.floor(Math.random() * events.length)];
        
        wsClient.handleNeuralActivity({
            event_type: randomEvent,
            intensity: Math.random(),
            metadata: { demo: true }
        });
    }, 2000);
}

// Export for debugging
window.wsClient = wsClient;
