/**
 * hero.js — Three.js wireframe icosahedron with mouse tracking.
 * Minimal scene: ONE wireframe object, no shadows, no textures.
 */

import * as THREE from 'three';

export function initHero() {
    const canvas = document.getElementById('hero-canvas');
    if (!canvas) return;

    // ── Scene setup ──────────────────────────────────────────────────────────
    const scene = new THREE.Scene();

    const camera = new THREE.PerspectiveCamera(
        50,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );
    camera.position.z = 5;

    const renderer = new THREE.WebGLRenderer({
        canvas,
        alpha: true,
        antialias: false,
        powerPreference: 'high-performance',
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0);

    // ── Wireframe icosahedron ────────────────────────────────────────────────
    const icoGeo = new THREE.IcosahedronGeometry(1.8, 1);
    const wireGeo = new THREE.WireframeGeometry(icoGeo);
    const wireMat = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.25,
    });
    const wireframe = new THREE.LineSegments(wireGeo, wireMat);
    scene.add(wireframe);

    // Secondary smaller wireframe (inner glow effect)
    const icoGeo2 = new THREE.IcosahedronGeometry(1.2, 0);
    const wireGeo2 = new THREE.WireframeGeometry(icoGeo2);
    const wireMat2 = new THREE.LineBasicMaterial({
        color: 0xffffff,
        transparent: true,
        opacity: 0.1,
    });
    const wireframe2 = new THREE.LineSegments(wireGeo2, wireMat2);
    scene.add(wireframe2);

    // ── Ambient light ────────────────────────────────────────────────────────
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));

    // ── Mouse tracking ───────────────────────────────────────────────────────
    let targetRotX = 0;
    let targetRotY = 0;

    document.addEventListener('mousemove', (e) => {
        targetRotX = (e.clientY / window.innerHeight - 0.5) * 0.4;
        targetRotY = (e.clientX / window.innerWidth - 0.5) * 0.4;
    });

    // ── Visibility observer — pause when off-screen ──────────────────────────
    let isVisible = true;
    const observer = new IntersectionObserver(([entry]) => {
        isVisible = entry.isIntersecting;
    }, { threshold: 0.1 });
    observer.observe(canvas);

    // ── Animation loop ───────────────────────────────────────────────────────
    function animate() {
        requestAnimationFrame(animate);
        if (!isVisible) return;

        // Smooth interpolation toward mouse
        wireframe.rotation.x += (targetRotX - wireframe.rotation.x) * 0.03;
        wireframe.rotation.y += (targetRotY - wireframe.rotation.y) * 0.03;

        // Constant slow rotation
        wireframe.rotation.z += 0.001;

        // Inner wireframe rotates opposite
        wireframe2.rotation.x += (targetRotX * 0.5 - wireframe2.rotation.x) * 0.02;
        wireframe2.rotation.y += (-targetRotY * 0.5 - wireframe2.rotation.y) * 0.02;
        wireframe2.rotation.z -= 0.002;

        renderer.render(scene, camera);
    }
    animate();

    // ── Resize handler ───────────────────────────────────────────────────────
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
}
