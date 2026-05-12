"""Three.js 3D viewer endpoint for wine bottle reconstructions.

Serves interactive WebGL viewer for inspecting and comparing 3D models with
proper lighting, PBR materials, and camera pose visualization.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
import json

from backend.app.api.routers.reconstruction import get_reconstruction_service
from backend.app.services.reconstruction_service import ReconstructionService

router = APIRouter(tags=["3d-viewer"])


@router.get("/viewer")
async def get_viewer_html() -> HTMLResponse:
    """Serve interactive Three.js viewer for 3D bottle reconstruction."""
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Wine-O 3D Bottle Viewer</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
                color: #fff;
                height: 100vh;
                overflow: hidden;
            }
            
            .container {
                display: flex;
                height: 100vh;
                gap: 20px;
                padding: 20px;
            }
            
            #canvas {
                flex: 1;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                background: #000;
            }
            
            .control-panel {
                width: 320px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 20px;
                overflow-y: auto;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            .control-section {
                display: flex;
                flex-direction: column;
                gap: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                padding-bottom: 16px;
            }
            
            .control-section:last-child {
                border-bottom: none;
            }
            
            .control-label {
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                opacity: 0.9;
            }
            
            .slider-group {
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
            
            input[type="range"] {
                width: 100%;
                height: 6px;
                border-radius: 3px;
                background: linear-gradient(to right, #ff6b6b, #4ecdc4);
                outline: none;
                -webkit-appearance: none;
            }
            
            input[type="range"]::-webkit-slider-thumb {
                -webkit-appearance: none;
                appearance: none;
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: #fff;
                cursor: pointer;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            }
            
            input[type="range"]::-moz-range-thumb {
                width: 16px;
                height: 16px;
                border-radius: 50%;
                background: #fff;
                cursor: pointer;
                border: none;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            }
            
            .slider-value {
                font-size: 12px;
                opacity: 0.8;
                text-align: right;
            }
            
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 10px;
                cursor: pointer;
            }
            
            input[type="checkbox"] {
                width: 18px;
                height: 18px;
                cursor: pointer;
                accent-color: #4ecdc4;
            }
            
            .checkbox-label {
                font-size: 14px;
                cursor: pointer;
                flex: 1;
            }
            
            .button {
                padding: 10px 16px;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                cursor: pointer;
                font-size: 14px;
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            .button-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            
            .button-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
            }
            
            .button-secondary {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .button-secondary:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            
            .stats {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                font-family: 'Courier New', monospace;
                line-height: 1.6;
                opacity: 0.8;
            }
            
            .stat-line {
                display: flex;
                justify-content: space-between;
                gap: 10px;
            }
            
            .stat-label {
                color: #4ecdc4;
            }
            
            .stat-value {
                text-align: right;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            
            .loading.active {
                display: block;
            }
            
            .spinner {
                width: 40px;
                height: 40px;
                border: 3px solid rgba(255, 255, 255, 0.3);
                border-top-color: #fff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <canvas id="canvas"></canvas>
            
            <div class="control-panel">
                <h2 style="margin-bottom: 10px;">Wine-O Viewer</h2>
                
                <div class="control-section">
                    <label class="control-label">Lighting</label>
                    <div class="slider-group">
                        <label style="display: flex; justify-content: space-between; font-size: 13px;">
                            Intensity: <span id="intensityValue" style="color: #4ecdc4;">1.0</span>
                        </label>
                        <input type="range" id="intensitySlider" min="0" max="2" step="0.1" value="1">
                    </div>
                    <div class="slider-group">
                        <label style="display: flex; justify-content: space-between; font-size: 13px;">
                            Ambient: <span id="ambientValue" style="color: #4ecdc4;">0.3</span>
                        </label>
                        <input type="range" id="ambientSlider" min="0" max="1" step="0.05" value="0.3">
                    </div>
                </div>
                
                <div class="control-section">
                    <label class="control-label">Material</label>
                    <div class="slider-group">
                        <label style="display: flex; justify-content: space-between; font-size: 13px;">
                            Roughness: <span id="roughnessValue" style="color: #4ecdc4;">0.7</span>
                        </label>
                        <input type="range" id="roughnessSlider" min="0" max="1" step="0.05" value="0.7">
                    </div>
                    <div class="slider-group">
                        <label style="display: flex; justify-content: space-between; font-size: 13px;">
                            Metallic: <span id="metallicValue" style="color: #4ecdc4;">0.1</span>
                        </label>
                        <input type="range" id="metallicSlider" min="0" max="1" step="0.05" value="0.1">
                    </div>
                </div>
                
                <div class="control-section">
                    <label class="control-label">View</label>
                    <div class="checkbox-group">
                        <input type="checkbox" id="showNormals" checked>
                        <label class="checkbox-label" for="showNormals">Show Normals</label>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="wireframe" unchecked>
                        <label class="checkbox-label" for="wireframe">Wireframe</label>
                    </div>
                    <div class="checkbox-group">
                        <input type="checkbox" id="autoRotate" checked>
                        <label class="checkbox-label" for="autoRotate">Auto Rotate</label>
                    </div>
                </div>
                
                <div class="control-section">
                    <label class="control-label">Actions</label>
                    <button class="button button-primary" onclick="resetView()">Reset View</button>
                    <button class="button button-secondary" onclick="downloadModel()">Download glTF</button>
                </div>
                
                <div class="stats">
                    <div class="stat-line">
                        <span class="stat-label">Vertices:</span>
                        <span class="stat-value" id="vertexCount">0</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">Triangles:</span>
                        <span class="stat-value" id="triangleCount">0</span>
                    </div>
                    <div class="stat-line">
                        <span class="stat-label">FPS:</span>
                        <span class="stat-value" id="fpsCounter">0</span>
                    </div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Loading model...</p>
                </div>
            </div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@r128/examples/js/loaders/GLTFLoader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@r128/examples/js/controls/OrbitControls.js"></script>
        
        <script>
            // Scene setup
            const canvas = document.getElementById('canvas');
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x000000);
            
            const camera = new THREE.PerspectiveCamera(
                75,
                canvas.clientWidth / canvas.clientHeight,
                0.1,
                1000
            );
            camera.position.set(0, 0, 2);
            
            const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
            renderer.setSize(canvas.clientWidth, canvas.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            
            // Controls
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.autoRotate = true;
            controls.autoRotateSpeed = 2;
            
            // Lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.3);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(5, 5, 5);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 1024;
            directionalLight.shadow.mapSize.height = 1024;
            scene.add(directionalLight);
            
            // Load sample model (placeholder)
            let model = null;
            
            function setupControls() {
                // Intensity
                document.getElementById('intensitySlider').addEventListener('input', (e) => {
                    directionalLight.intensity = parseFloat(e.target.value);
                    document.getElementById('intensityValue').textContent = parseFloat(e.target.value).toFixed(1);
                });
                
                // Ambient
                document.getElementById('ambientSlider').addEventListener('input', (e) => {
                    ambientLight.intensity = parseFloat(e.target.value);
                    document.getElementById('ambientValue').textContent = parseFloat(e.target.value).toFixed(2);
                });
                
                // Roughness
                document.getElementById('roughnessSlider').addEventListener('input', (e) => {
                    if (model && model.children[0]?.material) {
                        model.children[0].material.roughness = parseFloat(e.target.value);
                    }
                    document.getElementById('roughnessValue').textContent = parseFloat(e.target.value).toFixed(2);
                });
                
                // Metallic
                document.getElementById('metallicSlider').addEventListener('input', (e) => {
                    if (model && model.children[0]?.material) {
                        model.children[0].material.metalness = parseFloat(e.target.value);
                    }
                    document.getElementById('metallicValue').textContent = parseFloat(e.target.value).toFixed(2);
                });
                
                // Auto rotate
                document.getElementById('autoRotate').addEventListener('change', (e) => {
                    controls.autoRotate = e.target.checked;
                });
                
                // Wireframe
                document.getElementById('wireframe').addEventListener('change', (e) => {
                    if (model) {
                        model.traverse((child) => {
                            if (child.material) {
                                child.material.wireframe = e.target.checked;
                            }
                        });
                    }
                });
            }
            
            function resetView() {
                camera.position.set(0, 0, 2);
                controls.target.set(0, 0, 0);
                controls.update();
            }
            
            function downloadModel() {
                alert('Download feature coming soon!');
            }
            
            // Create simple test geometry
            function loadTestModel() {
                const geometry = new THREE.CylinderGeometry(1, 1, 2, 32, 32);
                const material = new THREE.MeshStandardMaterial({
                    color: 0x8B0000,
                    roughness: 0.7,
                    metalness: 0.1,
                });
                model = new THREE.Mesh(geometry, material);
                scene.add(model);
                
                updateStats();
            }
            
            function updateStats() {
                let vertexCount = 0;
                let triangleCount = 0;
                
                scene.traverse((obj) => {
                    if (obj.geometry) {
                        vertexCount += obj.geometry.attributes.position.count;
                        triangleCount += obj.geometry.index.count / 3;
                    }
                });
                
                document.getElementById('vertexCount').textContent = vertexCount.toLocaleString();
                document.getElementById('triangleCount').textContent = Math.floor(triangleCount).toLocaleString();
            }
            
            // Animation loop
            let lastTime = Date.now();
            let frameCount = 0;
            
            function animate() {
                requestAnimationFrame(animate);
                
                controls.update();
                
                if (model) {
                    model.rotation.y += 0.001;
                }
                
                renderer.render(scene, camera);
                
                // FPS counter
                frameCount++;
                const now = Date.now();
                if (now >= lastTime + 1000) {
                    document.getElementById('fpsCounter').textContent = frameCount;
                    frameCount = 0;
                    lastTime = now;
                }
            }
            
            // Handle window resize
            window.addEventListener('resize', () => {
                const width = canvas.clientWidth;
                const height = canvas.clientHeight;
                camera.aspect = width / height;
                camera.updateProjectionMatrix();
                renderer.setSize(width, height);
            });
            
            // Initialize
            setupControls();
            loadTestModel();
            animate();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)


@router.get("/reconstruction/{reconstruction_id}/viewer")
async def get_reconstruction_viewer(
    reconstruction_id: str,
    reconstruction_service: ReconstructionService = Depends(get_reconstruction_service),
) -> HTMLResponse:
    """Get viewer for specific reconstruction with pre-loaded data."""

    reconstruction = reconstruction_service.get_reconstruction(reconstruction_id)
    if reconstruction is None:
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head><title>Reconstruction Not Found</title></head>
            <body style=\"font-family:sans-serif;padding:24px;\">
                <h2>Reconstruction not found</h2>
                <p>No reconstruction exists for ID: {reconstruction_id}</p>
            </body>
            </html>
            """,
            status_code=404,
        )

    gltf_json = reconstruction.metadata.get("gltf_json", {})
    gltf_json_js = json.dumps(gltf_json)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Reconstruction {reconstruction_id}</title>
        <style>
            body {{ margin: 0; background: #000; font-family: sans-serif; }}
            #canvas {{ display: block; width: 100%; height: 100vh; }}
            .info {{ position: absolute; top: 20px; left: 20px; color: #0f0; font-family: monospace; font-size: 12px; }}
        </style>
    </head>
    <body>
        <canvas id="canvas"></canvas>
        <div class="info">
            <div>Reconstruction: {reconstruction_id}</div>
            <div id="status">Loading...</div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@r128/examples/js/loaders/GLTFLoader.js"></script>
        
        <script>
            // Scene setup
            const scene = new THREE.Scene();
            scene.background = new THREE.Color(0x111111);
            const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            const renderer = new THREE.WebGLRenderer({ antialias: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.shadowMap.enabled = true;
            document.body.appendChild(renderer.domElement);
            
            // Lighting
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambientLight);
            
            const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
            directionalLight.position.set(5, 5, 5);
            directionalLight.castShadow = true;
            scene.add(directionalLight);

            const statusEl = document.getElementById('status');

            async function loadModel() {{
                try {{
                    statusEl.textContent = 'Loading glTF...';
                    const response = await fetch('/api/v1/3d/export/{reconstruction_id}?format=gltf');
                    const payload = await response.json();

                    if (!response.ok || payload.error) {{
                        statusEl.textContent = payload.error || 'Failed to fetch reconstruction';
                        return;
                    }}

                    const exportResponse = await fetch('/api/v1/3d/status/{reconstruction_id}');
                    if (exportResponse.ok) {{
                        statusEl.textContent = 'Rendering';
                    }}

                    const gltfJson = {gltf_json_js};
                    const loader = new THREE.GLTFLoader();
                    loader.parse(
                        JSON.stringify(gltfJson),
                        '',
                        (gltf) => {{
                            scene.add(gltf.scene);
                            camera.position.set(0, 0.8, 2.2);
                            statusEl.textContent = 'Loaded';
                        }},
                        (error) => {{
                            console.error(error);
                            statusEl.textContent = 'glTF parse failed';
                        }}
                    );
                }} catch (error) {{
                    console.error(error);
                    statusEl.textContent = 'Load error';
                }}
            }}
            
            // Animation loop
            function animate() {{
                requestAnimationFrame(animate);
                renderer.render(scene, camera);
            }}

            loadModel();
            animate();
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html)
