import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, Text } from '@react-three/drei';
import * as THREE from 'three';
import { MozaTelemetry } from '../hooks/useMozaTelemetry';

interface SpatialViewportProps {
  telemetry: MozaTelemetry;
}

function PatronCluster({ count }: { count: number }) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.2) * 0.05;
    }
  });

  // Generate synthetic 3D patron positions based on real-time count
  const patrons = React.useMemo(() => {
    return Array.from({ length: Math.min(count, 50) }).map((_, i) => {
      const angle = (i / Math.max(count, 1)) * Math.PI * 2;
      const radius = 1.5 + (i % 4) * 0.8;
      return {
        id: i,
        x: Math.cos(angle) * radius,
        z: Math.sin(angle) * radius,
        height: 1.7 + (i % 3) * 0.1,
      };
    });
  }, [count]);

  return (
    <group ref={groupRef}>
      {patrons.map((p) => (
        <group key={p.id} position={[p.x, p.height / 2, p.z]}>
          {/* 3D Patron Cylinder */}
          <mesh castShadow>
            <cylinderGeometry args={[0.25, 0.25, p.height, 16]} />
            <meshStandardMaterial
              color="#00f2fe"
              emissive="#00f2fe"
              emissiveIntensity={0.3}
              roughness={0.2}
              metalness={0.8}
            />
          </mesh>
          {/* Head sphere */}
          <mesh position={[0, p.height / 2 + 0.2, 0]}>
            <sphereGeometry args={[0.18, 16, 16]} />
            <meshStandardMaterial color="#4facfe" />
          </mesh>
        </group>
      ))}
    </group>
  );
}

function CocktailBarZone({ beverageCount }: { beverageCount: number }) {
  return (
    <group position={[0, 0, -4]}>
      {/* Bar Counter */}
      <mesh position={[0, 0.5, 0]}>
        <boxGeometry args={[6, 1, 0.8]} />
        <meshStandardMaterial color="#1e222d" roughness={0.4} metalness={0.6} />
      </mesh>
      <Text
        position={[0, 1.2, 0]}
        fontSize={0.28}
        color="#f6d365"
        anchorX="center"
        anchorY="middle"
      >
        {`BAR ZONE (${beverageCount} Active Vessels)`}
      </Text>
    </group>
  );
}

export const SpatialViewport: React.FC<SpatialViewportProps> = ({ telemetry }) => {
  return (
    <div style={{ width: '100%', height: '100%', position: 'relative', background: '#07080a' }}>
      <Canvas
        camera={{ position: [0, 6, 8], fov: 45 }}
        gl={{ antialias: true, alpha: false }}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={0.6} />
        <pointLight position={[10, 15, 10]} intensity={1.5} />
        <directionalLight position={[-10, 12, -5]} intensity={0.8} />

        {/* 3D Metric Grid (Bobby Homography Ground Plane) */}
        <Grid
          infiniteGrid
          cellSize={1}
          cellThickness={1}
          cellColor="#1e293b"
          sectionSize={5}
          sectionThickness={1.5}
          sectionColor="#334155"
          fadeDistance={30}
        />

        {/* 3D Venue Objects */}
        <CocktailBarZone beverageCount={telemetry.total_beverages} />
        <PatronCluster count={telemetry.people_count} />

        <OrbitControls
          makeDefault
          maxPolarAngle={Math.PI / 2.1}
          minDistance={3}
          maxDistance={25}
        />
      </Canvas>

      {/* Floating 3D HUD Badge */}
      <div
        className="glass-panel"
        style={{
          position: 'absolute',
          top: 16,
          left: 16,
          padding: '8px 14px',
          fontFamily: 'var(--font-mono)',
          fontSize: '12px',
          color: 'var(--neon-cyan)',
        }}
      >
        THREE.JS 3D SPATIAL HUD (60 FPS)
      </div>
    </div>
  );
};
