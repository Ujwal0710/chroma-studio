"""Interactive 3D Architectural Room Experience powered by Three.js & WebGL.

Provides perspective room rotation, real-time wall surface recolouring from active palettes,
PBR material finish rendering (Matte, Eggshell, Satin, Gloss), and diurnal ambient lighting shifts.
"""
import streamlit.components.v1 as components


def generate_3d_room_html(
    primary_wall_hex: str = "#B85C38",
    secondary_wall_hex: str = "#D6C5B3",
    accent_hex: str = "#30271F",
    trim_hex: str = "#F7F3EE",
    room_type: str = "Living Room",
    theme: str = "light",
    canvas_height: int = 580
) -> str:
    """Generate complete HTML/WebGL/Three.js payload for interactive 3D spatial room simulation."""

    bg_canvas = "#F5F0E8" if theme == "light" else "#171916"
    card_bg = "rgba(255, 252, 247, 0.92)" if theme == "light" else "rgba(27, 30, 25, 0.92)"
    text_color = "#171916" if theme == "light" else "#F4F1EA"
    border_color = "rgba(227, 216, 203, 0.6)" if theme == "light" else "rgba(53, 58, 50, 0.6)"

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chroma Studio 3D Spatial Canvas</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            user-select: none;
        }}
        body {{
            background-color: {bg_canvas};
            color: {text_color};
            font-family: -apple-system, BlinkMacSystemFont, 'Plus Jakarta Sans', 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
            width: 100vw;
            height: {canvas_height}px;
        }}
        #canvas-container {{
            width: 100%;
            height: 100%;
            position: relative;
            cursor: grab;
        }}
        #canvas-container:active {{
            cursor: grabbing;
        }}
        /* Floating HUD Controls */
        .hud-overlay {{
            position: absolute;
            top: 16px;
            left: 16px;
            background: {card_bg};
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid {border_color};
            border-radius: 14px;
            padding: 12px 18px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
            z-index: 10;
            pointer-events: auto;
        }}
        .hud-title {{
            font-size: 0.76rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #B85C38;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .hud-desc {{
            font-size: 0.82rem;
            font-weight: 600;
            color: {text_color};
        }}
        /* Control Bar Bottom */
        .controls-panel {{
            position: absolute;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            background: {card_bg};
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid {border_color};
            border-radius: 16px;
            padding: 10px 18px;
            display: flex;
            align-items: center;
            gap: 16px;
            box-shadow: 0 12px 30px rgba(0,0,0,0.1);
            z-index: 10;
        }}
        .control-group {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.78rem;
            font-weight: 600;
        }}
        .control-label {{
            color: #725640;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 0.70rem;
        }}
        .btn-pill {{
            background: rgba(184, 92, 56, 0.08);
            border: 1px solid rgba(184, 92, 56, 0.2);
            color: {text_color};
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.74rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .btn-pill:hover, .btn-pill.active {{
            background: #B85C38;
            color: #FFFFFF;
            border-color: #B85C38;
        }}
        .swatch-indicator {{
            display: inline-block;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 1px solid rgba(0,0,0,0.2);
            vertical-align: middle;
            margin-right: 4px;
        }}
        /* Tooltip hint */
        .hint-badge {{
            position: absolute;
            bottom: 16px;
            right: 16px;
            font-size: 0.72rem;
            color: rgba(114, 86, 64, 0.8);
            background: {card_bg};
            padding: 6px 12px;
            border-radius: 8px;
            border: 1px solid {border_color};
            pointer-events: none;
        }}
    </style>
    <!-- Three.js + OrbitControls -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>
    <div id="canvas-container">
        <!-- Floating HUD -->
        <div class="hud-overlay">
            <div class="hud-title">🏛️ 3D Architectural Spatial Model</div>
            <div class="hud-desc">{room_type} • PBR Specular Materials</div>
        </div>

        <!-- Hint -->
        <div class="hint-badge">🖱️ Drag to Orbit • Scroll to Zoom • Right-Click to Pan</div>

        <!-- Bottom Controls -->
        <div class="controls-panel">
            <div class="control-group">
                <span class="control-label">Wall Finish:</span>
                <button class="btn-pill" onclick="setFinish('matte')">Matte</button>
                <button class="btn-pill active" onclick="setFinish('eggshell')">Eggshell</button>
                <button class="btn-pill" onclick="setFinish('satin')">Satin</button>
                <button class="btn-pill" onclick="setFinish('gloss')">Gloss</button>
            </div>
            <div style="width: 1px; height: 20px; background: {border_color};"></div>
            <div class="control-group">
                <span class="control-label">Lighting:</span>
                <button class="btn-pill active" onclick="setLighting('noon')">☀️ Noon 5500K</button>
                <button class="btn-pill" onclick="setLighting('morning')">🌅 Morning 3200K</button>
                <button class="btn-pill" onclick="setLighting('evening')">🌆 Dusk 2700K</button>
            </div>
            <div style="width: 1px; height: 20px; background: {border_color};"></div>
            <button class="btn-pill" onclick="resetCamera()">🔄 Reset View</button>
        </div>
    </div>

    <script>
        // State variables
        const PRIMARY_HEX = "{primary_wall_hex}";
        const SECONDARY_HEX = "{secondary_wall_hex}";
        const ACCENT_HEX = "{accent_hex}";
        const TRIM_HEX = "{trim_hex}";

        let scene, camera, renderer, controls;
        let mainWallMat, featureWallMat, ceilingMat, trimMat, floorMat;
        let sunLight, ambientLight, lampLight;

        function init() {{
            const container = document.getElementById('canvas-container');
            const width = container.clientWidth;
            const height = container.clientHeight;

            // 1. Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color("{bg_canvas}");
            scene.fog = new THREE.FogExp2("{bg_canvas}", 0.035);

            // 2. Camera
            camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
            camera.position.set(0, 1.8, 5.2);

            // 3. Renderer with antialiasing and shadow map
            renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: "high-performance" }});
            renderer.setSize(width, height);
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.05;
            container.appendChild(renderer.domElement);

            // 4. Controls
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.maxPolarAngle = Math.PI / 2 - 0.02; // Don't go below floor
            controls.minDistance = 2.0;
            controls.maxDistance = 8.5;
            controls.target.set(0, 1.3, 0);

            // 5. Lighting Setup
            ambientLight = new THREE.AmbientLight(0xFFF7EE, 0.65);
            scene.add(ambientLight);

            sunLight = new THREE.DirectionalLight(0xFFF2DF, 1.2);
            sunLight.position.set(3.8, 4.2, 2.5);
            sunLight.castShadow = true;
            sunLight.shadow.mapSize.width = 2048;
            sunLight.shadow.mapSize.height = 2048;
            sunLight.shadow.camera.near = 0.5;
            sunLight.shadow.camera.far = 15;
            sunLight.shadow.camera.left = -4;
            sunLight.shadow.camera.right = 4;
            sunLight.shadow.camera.top = 4;
            sunLight.shadow.camera.bottom = -4;
            sunLight.shadow.bias = -0.0005;
            scene.add(sunLight);

            // Warm interior architectural fill
            lampLight = new THREE.PointLight(0xF8D8B0, 0.6, 6);
            lampLight.position.set(-1.8, 2.2, 0.5);
            scene.add(lampLight);

            // 6. Build Architectural Room Geometry
            buildRoom();

            // 7. Window resize listener
            window.addEventListener('resize', onWindowResize);

            // 8. Animation loop
            animate();
        }}

        function buildRoom() {{
            const roomWidth = 5.0;
            const roomHeight = 3.0;
            const roomDepth = 4.4;

            // PBR Wall Materials (Default: Eggshell)
            mainWallMat = new THREE.MeshStandardMaterial({{
                color: PRIMARY_HEX,
                roughness: 0.70,
                metalness: 0.05
            }});

            featureWallMat = new THREE.MeshStandardMaterial({{
                color: SECONDARY_HEX,
                roughness: 0.65,
                metalness: 0.05
            }});

            ceilingMat = new THREE.MeshStandardMaterial({{
                color: TRIM_HEX,
                roughness: 0.90,
                metalness: 0.0
            }});

            trimMat = new THREE.MeshStandardMaterial({{
                color: TRIM_HEX,
                roughness: 0.35,
                metalness: 0.1
            }});

            floorMat = new THREE.MeshStandardMaterial({{
                color: 0xC49A6C, // Warm Oak Hardwood
                roughness: 0.35,
                metalness: 0.05
            }});

            // Floor Plane
            const floorGeo = new THREE.PlaneGeometry(roomWidth, roomDepth);
            const floorMesh = new THREE.Mesh(floorGeo, floorMat);
            floorMesh.rotation.x = -Math.PI / 2;
            floorMesh.receiveShadow = true;
            scene.add(floorMesh);

            // Ceiling Plane
            const ceilingGeo = new THREE.PlaneGeometry(roomWidth, roomDepth);
            const ceilingMesh = new THREE.Mesh(ceilingGeo, ceilingMat);
            ceilingMesh.position.y = roomHeight;
            ceilingMesh.rotation.x = Math.PI / 2;
            scene.add(ceilingMesh);

            // Back Wall (Primary Wall)
            const backWallGeo = new THREE.PlaneGeometry(roomWidth, roomHeight);
            const backWallMesh = new THREE.Mesh(backWallGeo, mainWallMat);
            backWallMesh.position.set(0, roomHeight / 2, -roomDepth / 2);
            backWallMesh.receiveShadow = true;
            scene.add(backWallMesh);

            // Left Wall with Window Opening (Feature Wall)
            const leftWallGeo = new THREE.PlaneGeometry(roomDepth, roomHeight);
            const leftWallMesh = new THREE.Mesh(leftWallGeo, featureWallMat);
            leftWallMesh.position.set(-roomWidth / 2, roomHeight / 2, 0);
            leftWallMesh.rotation.y = Math.PI / 2;
            leftWallMesh.receiveShadow = true;
            scene.add(leftWallMesh);

            // Right Wall (Primary Wall)
            const rightWallGeo = new THREE.PlaneGeometry(roomDepth, roomHeight);
            const rightWallMesh = new THREE.Mesh(rightWallGeo, mainWallMat);
            rightWallMesh.position.set(roomWidth / 2, roomHeight / 2, 0);
            rightWallMesh.rotation.y = -Math.PI / 2;
            rightWallMesh.receiveShadow = true;
            scene.add(rightWallMesh);

            // Architectural Baseboard Trim
            const baseboardMat = trimMat;
            const baseboardGeo = new THREE.BoxGeometry(roomWidth, 0.14, 0.04);
            const baseboardBack = new THREE.Mesh(baseboardGeo, baseboardMat);
            baseboardBack.position.set(0, 0.07, -roomDepth / 2 + 0.02);
            scene.add(baseboardBack);

            // 7. Contemporary Furniture & Styling
            // Minimalist Low Architectural Sofa
            const sofaMat = new THREE.MeshStandardMaterial({{
                color: ACCENT_HEX,
                roughness: 0.85,
                metalness: 0.05
            }});
            const sofaBase = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.45, 0.95), sofaMat);
            sofaBase.position.set(0, 0.225, -0.9);
            sofaBase.castShadow = true;
            sofaBase.receiveShadow = true;
            scene.add(sofaBase);

            const sofaBack = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.55, 0.25), sofaMat);
            sofaBack.position.set(0, 0.65, -1.25);
            sofaBack.castShadow = true;
            scene.add(sofaBack);

            // Designer Coffee Table (Dark Oak / Stone)
            const tableMat = new THREE.MeshStandardMaterial({{
                color: 0x24201C,
                roughness: 0.35,
                metalness: 0.1
            }});
            const tableMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.32, 32), tableMat);
            tableMesh.position.set(0, 0.16, 0.2);
            tableMesh.castShadow = true;
            tableMesh.receiveShadow = true;
            scene.add(tableMesh);

            // Architectural Accent Rug
            const rugMat = new THREE.MeshStandardMaterial({{
                color: 0xDDD4C5,
                roughness: 0.95,
                metalness: 0.0
            }});
            const rugMesh = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 2.0), rugMat);
            rugMesh.position.set(0, 0.005, -0.4);
            rugMesh.rotation.x = -Math.PI / 2;
            rugMesh.receiveShadow = true;
            scene.add(rugMesh);

            // Modern Slim Floor Lamp
            const lampStemMat = new THREE.MeshStandardMaterial({{ color: 0x1A1815, roughness: 0.2, metalness: 0.8 }});
            const lampStem = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 2.0, 16), lampStemMat);
            lampStem.position.set(-1.8, 1.0, 0.5);
            lampStem.castShadow = true;
            scene.add(lampStem);

            const lampShadeMat = new THREE.MeshStandardMaterial({{ color: 0xF5F0E8, roughness: 0.4, emissive: 0xF5E5C8, emissiveIntensity: 0.3 }});
            const lampShade = new THREE.Mesh(new THREE.ConeGeometry(0.24, 0.35, 24), lampShadeMat);
            lampShade.position.set(-1.8, 2.0, 0.5);
            lampShade.rotation.x = Math.PI;
            scene.add(lampShade);

            // Large Canvas Art Piece on Back Wall
            const artFrameMat = new THREE.MeshStandardMaterial({{ color: 0x181512, roughness: 0.3, metalness: 0.2 }});
            const artCanvasMat = new THREE.MeshStandardMaterial({{ color: 0xEDE2D0, roughness: 0.8, metalness: 0.0 }});
            const artGroup = new THREE.Group();
            const frameMesh = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.1, 0.04), artFrameMat);
            const canvasMesh = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.0, 0.042), artCanvasMat);
            artGroup.add(frameMesh);
            artGroup.add(canvasMesh);
            artGroup.position.set(0, 1.85, -roomDepth / 2 + 0.03);
            artGroup.castShadow = true;
            scene.add(artGroup);
        }}

        // Interactive Finish Switcher
        function setFinish(type) {{
            document.querySelectorAll('.controls-panel button').forEach(b => {{
                if (b.innerText.toLowerCase().includes(type)) b.classList.add('active');
                else if (['matte', 'eggshell', 'satin', 'gloss'].some(t => b.innerText.toLowerCase().includes(t))) b.classList.remove('active');
            }});

            let r = 0.70, m = 0.05;
            if (type === 'matte') {{ r = 0.95; m = 0.0; }}
            else if (type === 'eggshell') {{ r = 0.70; m = 0.05; }}
            else if (type === 'satin') {{ r = 0.45; m = 0.10; }}
            else if (type === 'gloss') {{ r = 0.15; m = 0.25; }}

            if (mainWallMat) {{ mainWallMat.roughness = r; mainWallMat.metalness = m; }}
            if (featureWallMat) {{ featureWallMat.roughness = r; featureWallMat.metalness = m; }}
        }}

        // Interactive Diurnal Lighting Switcher
        function setLighting(condition) {{
            document.querySelectorAll('.controls-panel button').forEach(b => {{
                if (b.innerText.toLowerCase().includes(condition)) b.classList.add('active');
                else if (['noon', 'morning', 'dusk'].some(t => b.innerText.toLowerCase().includes(t))) b.classList.remove('active');
            }});

            if (condition === 'noon') {{
                ambientLight.color.setHex(0xFFF7EE);
                ambientLight.intensity = 0.70;
                sunLight.color.setHex(0xFFF4E5);
                sunLight.intensity = 1.25;
                sunLight.position.set(3.5, 4.5, 2.5);
                renderer.toneMappingExposure = 1.05;
            }} else if (condition === 'morning') {{
                ambientLight.color.setHex(0xFFEBD4);
                ambientLight.intensity = 0.55;
                sunLight.color.setHex(0xFFA660);
                sunLight.intensity = 1.40;
                sunLight.position.set(4.5, 2.5, 2.0); // Low-angle warm morning ray
                renderer.toneMappingExposure = 0.98;
            }} else if (condition === 'evening') {{
                ambientLight.color.setHex(0xD4CEE0);
                ambientLight.intensity = 0.35;
                sunLight.color.setHex(0xFF8844);
                sunLight.intensity = 0.85;
                sunLight.position.set(4.8, 1.2, 1.5); // Twilight golden hour
                lampLight.intensity = 1.1; // Lamp turns on warmly
                renderer.toneMappingExposure = 0.92;
            }}
        }}

        function resetCamera() {{
            camera.position.set(0, 1.8, 5.2);
            controls.target.set(0, 1.3, 0);
            controls.update();
        }}

        function onWindowResize() {{
            const container = document.getElementById('canvas-container');
            const w = container.clientWidth;
            const h = container.clientHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        window.onload = init;
    </script>
</body>
</html>
"""
    return html_content


def render_interactive_3d_room(
    primary_wall_hex: str = "#B85C38",
    secondary_wall_hex: str = "#D6C5B3",
    accent_hex: str = "#30271F",
    trim_hex: str = "#F7F3EE",
    room_type: str = "Living Room",
    theme: str = "light",
    height: int = 580
) -> None:
    """Render the interactive Three.js 3D room canvas inside Streamlit."""
    html_code = generate_3d_room_html(
        primary_wall_hex=primary_wall_hex,
        secondary_wall_hex=secondary_wall_hex,
        accent_hex=accent_hex,
        trim_hex=trim_hex,
        room_type=room_type,
        theme=theme,
        canvas_height=height
    )
    components.html(html_code, height=height, scrolling=False)
