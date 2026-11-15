import { useEffect, useRef } from "react";
import * as THREE from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

function faceTexture(symbol, colors, ink) {
  const s = 512;
  const c = document.createElement("canvas");
  c.width = c.height = s;
  const g = c.getContext("2d");
  const grad = g.createRadialGradient(s / 2, s / 2, 40, s / 2, s / 2, s / 2);
  grad.addColorStop(0, colors[0]);
  grad.addColorStop(1, colors[1]);
  g.fillStyle = grad;
  g.fillRect(0, 0, s, s);
  g.translate(s / 2, s / 2);
  g.rotate(-Math.PI / 2); // cylinder cap UVs are turned 90 degrees; this corrects it
  g.strokeStyle = ink;
  g.lineWidth = 10;
  g.beginPath(); g.arc(0, 0, s * 0.4, 0, Math.PI * 2); g.stroke();
  g.lineWidth = 3;
  g.beginPath(); g.arc(0, 0, s * 0.35, 0, Math.PI * 2); g.stroke();
  g.fillStyle = ink;
  g.font = "bold 280px 'Segoe UI', Arial, sans-serif";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.fillText(symbol, 0, 14);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

export default function Coin3D({ size = 120 }) {
  const mount = useRef(null);

  useEffect(() => {
    const el = mount.current;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(size, size);
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.set(0, 0, 6);

    const purple = new THREE.PointLight(0x8b5cf6, 60, 20);
    purple.position.set(-3, 2, 3);
    const cyan = new THREE.PointLight(0x22d3ee, 60, 20);
    cyan.position.set(3, -2, 3);
    scene.add(purple, cyan);

    const frontTex = faceTexture("$", ["#fde68a", "#d4a017"], "#6b4e00");
    const backTex = faceTexture("₹", ["#c4b5fd", "#6d28d9"], "#2e1065");
    const edge = new THREE.MeshStandardMaterial({ color: 0xf5c451, metalness: 1, roughness: 0.25 });
    const front = new THREE.MeshStandardMaterial({ map: frontTex, metalness: 0.9, roughness: 0.3 });
    const back = new THREE.MeshStandardMaterial({ map: backTex, metalness: 0.9, roughness: 0.3 });
    const geometry = new THREE.CylinderGeometry(1.6, 1.6, 0.28, 96);
    const coin = new THREE.Mesh(geometry, [edge, front, back]); // side, top, bottom
    coin.rotation.x = Math.PI / 2;
    const group = new THREE.Group();
    group.add(coin);
    scene.add(group);

    let tx = 0, ty = 0, spin = 0, raf;
    const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const onMove = (e) => {
      tx = (e.clientX / window.innerWidth - 0.5) * 0.8;
      ty = (e.clientY / window.innerHeight - 0.5) * 0.6;
    };
    window.addEventListener("pointermove", onMove);

    const clock = new THREE.Clock();
    const loop = () => {
      const t = clock.getElapsedTime();
      if (!calm) spin += 0.012;
      group.rotation.y = spin + tx;
      group.rotation.x = ty;
      group.position.y = Math.sin(t * 1.5) * 0.08;
      renderer.render(scene, camera);
      raf = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("pointermove", onMove);
      geometry.dispose();
      [edge, front, back].forEach((m) => m.dispose());
      frontTex.dispose();
      backTex.dispose();
      pmrem.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === el) el.removeChild(renderer.domElement);
    };
  }, [size]);

  return <div ref={mount} style={{ width: size, height: size }} />;
}