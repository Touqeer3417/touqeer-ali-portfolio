"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import { useTheme } from "next-themes";
import * as THREE from "three";

import { useMediaQuery } from "@/hooks/useMediaQuery";
import { useReducedMotion } from "@/hooks/useReducedMotion";

type Point3 = [number, number, number];

type ScenePalette = {
  accent: string;
  foreground: string;
  muted: string;
  line: string;
};

const NODE_POSITIONS: Point3[] = [
  [0, 0, 0],
  [-2.45, 1.35, -0.55],
  [2.4, 1.5, -0.9],
  [2.65, -1.2, -0.25],
  [-2.55, -1.45, -0.7],
  [0, 2.55, -1.15],
  [0.15, -2.55, -0.95],
];

const CONNECTIONS: Array<[number, number]> = [
  [0, 1],
  [0, 2],
  [0, 3],
  [0, 4],
  [0, 5],
  [0, 6],
  [1, 5],
  [2, 5],
  [2, 3],
  [3, 6],
  [4, 6],
  [1, 4],
];

const SIGNALS: Array<[number, number, number]> = [
  [0, 1, 0.02],
  [0, 2, 0.18],
  [0, 3, 0.36],
  [4, 0, 0.54],
  [5, 0, 0.7],
  [0, 6, 0.86],
];

function createSeededRandom(seed: number) {
  let value = seed >>> 0;

  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function buildParticlePositions(count: number) {
  const random = createSeededRandom(3417);
  const positions = new Float32Array(count * 3);

  for (let index = 0; index < count; index += 1) {
    const radius = 3.35 + random() * 2.1;
    const theta = random() * Math.PI * 2;
    const vertical = random() * 2 - 1;
    const horizontal = Math.sqrt(1 - vertical * vertical);

    positions[index * 3] = radius * horizontal * Math.cos(theta);
    positions[index * 3 + 1] = radius * vertical;
    positions[index * 3 + 2] = radius * horizontal * Math.sin(theta) - 0.4;
  }

  return positions;
}

function NetworkLines({ palette }: { palette: ScenePalette }) {
  const positions = useMemo(() => {
    const buffer = new Float32Array(CONNECTIONS.length * 6);

    CONNECTIONS.forEach(([startIndex, endIndex], index) => {
      const start = NODE_POSITIONS[startIndex];
      const end = NODE_POSITIONS[endIndex];
      const offset = index * 6;

      buffer[offset] = start[0];
      buffer[offset + 1] = start[1];
      buffer[offset + 2] = start[2];
      buffer[offset + 3] = end[0];
      buffer[offset + 4] = end[1];
      buffer[offset + 5] = end[2];
    });

    return buffer;
  }, []);

  return (
    <lineSegments>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <lineBasicMaterial
        color={palette.line}
        transparent
        opacity={0.42}
        depthWrite={false}
      />
    </lineSegments>
  );
}

function SatelliteNode({
  position,
  palette,
}: {
  position: Point3;
  palette: ScenePalette;
}) {
  return (
    <group position={position}>
      <mesh>
        <sphereGeometry args={[0.18, 16, 16]} />
        <meshStandardMaterial
          color={palette.foreground}
          emissive={palette.accent}
          emissiveIntensity={0.55}
          metalness={0.15}
          roughness={0.35}
        />
      </mesh>

      <mesh scale={2.25}>
        <sphereGeometry args={[0.18, 12, 12]} />
        <meshBasicMaterial
          color={palette.accent}
          transparent
          opacity={0.08}
          depthWrite={false}
          toneMapped={false}
        />
      </mesh>
    </group>
  );
}

function Signal({
  start,
  end,
  offset,
  accent,
}: {
  start: Point3;
  end: Point3;
  offset: number;
  accent: string;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const startVector = useMemo(() => new THREE.Vector3(...start), [start]);
  const endVector = useMemo(() => new THREE.Vector3(...end), [end]);

  useFrame((state) => {
    if (!ref.current) {
      return;
    }

    const raw = (state.clock.elapsedTime * 0.22 + offset) % 1;
    const eased = raw * raw * (3 - 2 * raw);

    ref.current.position.lerpVectors(startVector, endVector, eased);
    ref.current.scale.setScalar(0.75 + Math.sin(raw * Math.PI) * 0.5);
  });

  return (
    <mesh ref={ref} position={start}>
      <sphereGeometry args={[0.055, 10, 10]} />
      <meshBasicMaterial
        color={accent}
        transparent
        opacity={0.95}
        depthWrite={false}
        toneMapped={false}
      />
    </mesh>
  );
}

function ParticleField({
  count,
  palette,
  reducedMotion,
}: {
  count: number;
  palette: ScenePalette;
  reducedMotion: boolean;
}) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => buildParticlePositions(count), [count]);

  useFrame((state) => {
    if (!ref.current || reducedMotion) {
      return;
    }

    ref.current.rotation.y = state.clock.elapsedTime * 0.015;
    ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.12) * 0.025;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color={palette.accent}
        size={0.032}
        sizeAttenuation
        transparent
        opacity={0.48}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        toneMapped={false}
      />
    </points>
  );
}

function AgenticNetwork({
  palette,
  reducedMotion,
}: {
  palette: ScenePalette;
  reducedMotion: boolean;
}) {
  const network = useRef<THREE.Group>(null);
  const core = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (!network.current || !core.current || reducedMotion) {
      return;
    }

    const elapsed = state.clock.elapsedTime;
    const targetX = state.pointer.y * 0.12 + Math.sin(elapsed * 0.24) * 0.035;
    const targetY = state.pointer.x * 0.2 + Math.sin(elapsed * 0.18) * 0.07;

    network.current.rotation.x = THREE.MathUtils.damp(
      network.current.rotation.x,
      targetX,
      3.2,
      delta,
    );
    network.current.rotation.y = THREE.MathUtils.damp(
      network.current.rotation.y,
      targetY,
      3.2,
      delta,
    );

    core.current.rotation.x += delta * 0.2;
    core.current.rotation.y += delta * 0.38;

    const pulse = 1 + Math.sin(elapsed * 2.1) * 0.04;
    core.current.scale.setScalar(pulse);
  });

  return (
    <group ref={network} rotation={[0.04, -0.08, 0]}>
      <NetworkLines palette={palette} />

      {/* Central LLM / reasoning core */}
      <group>
        <mesh ref={core}>
          <icosahedronGeometry args={[0.64, 2]} />
          <meshStandardMaterial
            color={palette.accent}
            emissive={palette.accent}
            emissiveIntensity={1.35}
            metalness={0.2}
            roughness={0.22}
            transparent
            opacity={0.88}
          />
        </mesh>

        <mesh scale={1.38}>
          <icosahedronGeometry args={[0.64, 1]} />
          <meshBasicMaterial
            color={palette.foreground}
            wireframe
            transparent
            opacity={0.24}
            depthWrite={false}
          />
        </mesh>

        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <torusGeometry args={[1.12, 0.009, 6, 72]} />
          <meshBasicMaterial
            color={palette.accent}
            transparent
            opacity={0.4}
            depthWrite={false}
            toneMapped={false}
          />
        </mesh>

        <mesh rotation={[Math.PI / 2.9, Math.PI / 5, 0]}>
          <torusGeometry args={[1.36, 0.007, 6, 72]} />
          <meshBasicMaterial
            color={palette.line}
            transparent
            opacity={0.28}
            depthWrite={false}
          />
        </mesh>
      </group>

      {NODE_POSITIONS.slice(1).map((position, index) => (
        <SatelliteNode
          key={`${position.join("-")}-${index}`}
          position={position}
          palette={palette}
        />
      ))}

      {!reducedMotion
        ? SIGNALS.map(([startIndex, endIndex, offset]) => (
            <Signal
              key={`${startIndex}-${endIndex}-${offset}`}
              start={NODE_POSITIONS[startIndex]}
              end={NODE_POSITIONS[endIndex]}
              offset={offset}
              accent={palette.accent}
            />
          ))
        : null}

      <pointLight
        position={[0, 0, 1.4]}
        color={palette.accent}
        intensity={5.5}
        distance={7}
        decay={2}
      />
    </group>
  );
}

function Scene({
  palette,
  particleCount,
  reducedMotion,
}: {
  palette: ScenePalette;
  particleCount: number;
  reducedMotion: boolean;
}) {
  return (
    <>
      <ambientLight intensity={0.58} />
      <directionalLight
        position={[4, 4, 6]}
        color={palette.foreground}
        intensity={1.35}
      />

      <ParticleField
        count={particleCount}
        palette={palette}
        reducedMotion={reducedMotion}
      />

      <AgenticNetwork palette={palette} reducedMotion={reducedMotion} />
    </>
  );
}

export function HeroThreeScene() {
  const { resolvedTheme } = useTheme();
  const reducedMotion = useReducedMotion();
  const isSmallScreen = useMediaQuery("(max-width: 767px)");

  const palette = useMemo<ScenePalette>(() => {
    if (resolvedTheme === "light") {
      return {
        accent: "#0b8c58",
        foreground: "#0c1111",
        muted: "#626b68",
        line: "#6f9d88",
      };
    }

    return {
      accent: "#75f5b5",
      foreground: "#eef4ef",
      muted: "#89938f",
      line: "#6d9482",
    };
  }, [resolvedTheme]);

  const particleCount = reducedMotion ? 36 : isSmallScreen ? 72 : 132;

  return (
    <Canvas
      aria-hidden="true"
      className={isSmallScreen ? "pointer-events-none" : "pointer-events-auto"}
      camera={{
        position: [0, 0, isSmallScreen ? 9.4 : 8.25],
        fov: isSmallScreen ? 46 : 42,
        near: 0.1,
        far: 30,
      }}
      dpr={isSmallScreen ? [1, 1.2] : [1, 1.5]}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{
        alpha: true,
        antialias: !isSmallScreen,
        powerPreference: "high-performance",
      }}
      onCreated={({ gl }) => {
        gl.setClearColor(0x000000, 0);
        gl.outputColorSpace = THREE.SRGBColorSpace;
        gl.toneMapping = THREE.ACESFilmicToneMapping;
        gl.toneMappingExposure = 1;
      }}
    >
      <Scene
        palette={palette}
        particleCount={particleCount}
        reducedMotion={reducedMotion}
      />
    </Canvas>
  );
}
