/**
 * HOPPER Neural Visualization
 * Réseau neuronal 3D interactif représentant l'activité de HOPPER
 */

class NeuralNetwork {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.neurons = [];
        this.connections = [];
        this.particleSystem = null;
        
        // Configuration
        this.config = {
            neuronCount: 50,
            layerCount: 5,
            connectionProbability: 0.15,
            baseColor: 0x00ff00,
            activeColor: 0xff00ff,
            pulseSpeed: 2.0,
            rotationSpeed: 0.001
        };

        this.init();
    }

    init() {
        const container = document.getElementById('canvas-container');
        
        // Scene
        this.scene = new THREE.Scene();
        this.scene.fog = new THREE.FogExp2(0x000000, 0.02);
        
        // Camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.z = 30;
        this.camera.position.y = 5;
        
        // Renderer
        this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setClearColor(0x000000, 1);
        container.appendChild(this.renderer.domElement);
        
        // Lights
        this.addLights();
        
        // Create neural network
        this.createNeuralNetwork();
        
        // Create particle system
        this.createParticleSystem();
        
        // Event listeners
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Start animation
        this.animate();
        
        // Hide loading
        setTimeout(() => {
            document.getElementById('loading').style.display = 'none';
        }, 1000);
        
        console.log('✅ Neural Network initialized');
    }

    addLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);
        
        // Point lights
        const light1 = new THREE.PointLight(0x00ff00, 1, 100);
        light1.position.set(10, 10, 10);
        this.scene.add(light1);
        
        const light2 = new THREE.PointLight(0x0088ff, 1, 100);
        light2.position.set(-10, -10, -10);
        this.scene.add(light2);
    }

    createNeuralNetwork() {
        const { neuronCount, layerCount } = this.config;
        const neuronsPerLayer = Math.floor(neuronCount / layerCount);
        
        // Create neurons in layers
        for (let layer = 0; layer < layerCount; layer++) {
            const layerZ = (layer - layerCount / 2) * 10;
            
            for (let i = 0; i < neuronsPerLayer; i++) {
                const angle = (i / neuronsPerLayer) * Math.PI * 2;
                const radius = 15 + Math.random() * 5;
                
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;
                const z = layerZ + (Math.random() - 0.5) * 3;
                
                const neuron = this.createNeuron(x, y, z, layer);
                this.neurons.push(neuron);
                this.scene.add(neuron.mesh);
            }
        }
        
        // Create connections
        this.createConnections();
        
        console.log(`✅ Created ${this.neurons.length} neurons and ${this.connections.length} connections`);
    }

    createNeuron(x, y, z, layer) {
        const geometry = new THREE.SphereGeometry(0.3, 16, 16);
        const material = new THREE.MeshPhongMaterial({
            color: this.config.baseColor,
            emissive: this.config.baseColor,
            emissiveIntensity: 0.5,
            shininess: 100
        });
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.set(x, y, z);
        
        // Add glow
        const glowGeometry = new THREE.SphereGeometry(0.5, 16, 16);
        const glowMaterial = new THREE.MeshBasicMaterial({
            color: this.config.baseColor,
            transparent: true,
            opacity: 0.2
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        mesh.add(glow);
        
        return {
            mesh: mesh,
            glow: glow,
            layer: layer,
            activity: 0,
            targetActivity: 0,
            type: this.getNeuronType(layer)
        };
    }

    getNeuronType(layer) {
        const types = ['input', 'stt', 'dispatcher', 'llm', 'output'];
        return types[layer] || 'hidden';
    }

    createConnections() {
        const { connectionProbability } = this.config;
        
        for (let i = 0; i < this.neurons.length; i++) {
            for (let j = i + 1; j < this.neurons.length; j++) {
                const n1 = this.neurons[i];
                const n2 = this.neurons[j];
                
                // Connect neurons in adjacent layers
                if (Math.abs(n1.layer - n2.layer) === 1 && Math.random() < connectionProbability) {
                    const connection = this.createConnection(n1, n2);
                    this.connections.push(connection);
                    this.scene.add(connection.line);
                }
            }
        }
    }

    createConnection(neuron1, neuron2) {
        const points = [
            neuron1.mesh.position,
            neuron2.mesh.position
        ];
        
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({
            color: this.config.baseColor,
            transparent: true,
            opacity: 0.1
        });
        
        const line = new THREE.Line(geometry, material);
        
        return {
            line: line,
            neuron1: neuron1,
            neuron2: neuron2,
            activity: 0
        };
    }

    createParticleSystem() {
        const particleCount = 1000;
        const particles = new THREE.BufferGeometry();
        const positions = new Float32Array(particleCount * 3);
        
        for (let i = 0; i < particleCount * 3; i++) {
            positions[i] = (Math.random() - 0.5) * 100;
        }
        
        particles.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        
        const material = new THREE.PointsMaterial({
            color: 0x00ff00,
            size: 0.1,
            transparent: true,
            opacity: 0.3,
            blending: THREE.AdditiveBlending
        });
        
        this.particleSystem = new THREE.Points(particles, material);
        this.scene.add(this.particleSystem);
    }

    activateNeuronsByType(type, intensity = 1.0) {
        this.neurons.forEach(neuron => {
            if (neuron.type === type) {
                neuron.targetActivity = intensity;
            }
        });
    }

    activateRandomNeurons(count = 5, intensity = 1.0) {
        for (let i = 0; i < count; i++) {
            const neuron = this.neurons[Math.floor(Math.random() * this.neurons.length)];
            neuron.targetActivity = intensity;
        }
    }

    pulseActivity(eventType) {
        // Map event types to neuron layers
        const typeMap = {
            'stt': 'stt',
            'llm': 'llm',
            'tts': 'output',
            'dispatch': 'dispatcher',
            'service': 'hidden'
        };
        
        const neuronType = typeMap[eventType] || 'hidden';
        this.activateNeuronsByType(neuronType, 1.5);
        
        // Random activation for realism
        this.activateRandomNeurons(3, 0.8);
    }

    updateNeurons(delta) {
        this.neurons.forEach(neuron => {
            // Smooth activity transition
            neuron.activity += (neuron.targetActivity - neuron.activity) * 0.1;
            neuron.targetActivity *= 0.95; // Decay
            
            // Update visual
            const intensity = Math.max(0.5, neuron.activity);
            neuron.mesh.material.emissiveIntensity = intensity;
            
            if (neuron.activity > 0.8) {
                neuron.mesh.material.emissive.setHex(this.config.activeColor);
                neuron.glow.material.opacity = 0.5;
            } else {
                neuron.mesh.material.emissive.setHex(this.config.baseColor);
                neuron.glow.material.opacity = 0.2;
            }
            
            // Pulse glow
            const pulse = Math.sin(Date.now() * 0.003 * this.config.pulseSpeed) * 0.1 + 0.9;
            neuron.glow.scale.setScalar(pulse);
        });
    }

    updateConnections() {
        this.connections.forEach(connection => {
            const activity = (connection.neuron1.activity + connection.neuron2.activity) / 2;
            connection.activity = activity;
            
            connection.line.material.opacity = Math.max(0.1, activity * 0.5);
            
            if (activity > 0.8) {
                connection.line.material.color.setHex(this.config.activeColor);
            } else {
                connection.line.material.color.setHex(this.config.baseColor);
            }
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        const delta = 0.016; // Approximate 60fps
        
        // Update neurons
        this.updateNeurons(delta);
        this.updateConnections();
        
        // Rotate scene slowly
        this.scene.rotation.y += this.config.rotationSpeed;
        
        // Animate particles
        if (this.particleSystem) {
            this.particleSystem.rotation.y += 0.0005;
            this.particleSystem.rotation.x += 0.0002;
        }
        
        // Camera movement
        this.camera.position.x = Math.sin(Date.now() * 0.0001) * 5;
        this.camera.lookAt(this.scene.position);
        
        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    // Public API
    getStats() {
        const activeNeurons = this.neurons.filter(n => n.activity > 0.5).length;
        const activeConnections = this.connections.filter(c => c.activity > 0.3).length;
        
        return {
            neurons: this.neurons.length,
            activeNeurons: activeNeurons,
            connections: this.connections.length,
            activeConnections: activeConnections
        };
    }
}

// Initialize
const neuralNet = new NeuralNetwork();

// Export for WebSocket client
window.neuralNet = neuralNet;
