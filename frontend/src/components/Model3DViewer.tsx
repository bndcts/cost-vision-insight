import { useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera } from "@react-three/drei";
import { Card } from "@/components/ui/card";
import * as THREE from "three";

const RotatingModel = () => {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.01;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.2;
    }
  });

  return (
    <group>
      {/* Main component - a stylized mechanical part */}
      <mesh ref={meshRef} castShadow>
        <cylinderGeometry args={[1, 1, 2, 32]} />
        <meshStandardMaterial 
          color="#3b82f6" 
          metalness={0.8} 
          roughness={0.2}
        />
      </mesh>
      
      {/* Inner detail */}
      <mesh castShadow>
        <torusGeometry args={[0.8, 0.15, 16, 32]} />
        <meshStandardMaterial 
          color="#60a5fa" 
          metalness={0.9} 
          roughness={0.1}
        />
      </mesh>

      {/* Top detail */}
      <mesh position={[0, 1.2, 0]} castShadow>
        <cylinderGeometry args={[0.5, 0.5, 0.3, 16]} />
        <meshStandardMaterial 
          color="#1e40af" 
          metalness={0.7} 
          roughness={0.3}
        />
      </mesh>

      {/* Bottom detail */}
      <mesh position={[0, -1.2, 0]} castShadow>
        <cylinderGeometry args={[0.5, 0.5, 0.3, 16]} />
        <meshStandardMaterial 
          color="#1e40af" 
          metalness={0.7} 
          roughness={0.3}
        />
      </mesh>
    </group>
  );
};

export const Model3DViewer = () => {
  return (
    <Card className="p-6 shadow-lg">
      <h3 className="text-xl font-bold mb-4">3D Prototype Model</h3>
      <p className="text-sm text-muted-foreground mb-4">
        AI-generated visualization based on specifications
      </p>
      
      <div className="h-96 rounded-lg overflow-hidden bg-gradient-to-br from-slate-900 to-slate-800">
        <Canvas shadows>
          <PerspectiveCamera makeDefault position={[3, 2, 5]} />
          <OrbitControls 
            enablePan={false} 
            minDistance={3} 
            maxDistance={10}
            autoRotate
            autoRotateSpeed={0.5}
          />
          
          {/* Lighting */}
          <ambientLight intensity={0.3} />
          <directionalLight 
            position={[5, 5, 5]} 
            intensity={1} 
            castShadow 
            shadow-mapSize-width={1024}
            shadow-mapSize-height={1024}
          />
          <pointLight position={[-5, 5, -5]} intensity={0.5} color="#60a5fa" />
          
          <RotatingModel />
          
          {/* Ground plane for shadow */}
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2, 0]} receiveShadow>
            <planeGeometry args={[10, 10]} />
            <shadowMaterial opacity={0.3} />
          </mesh>
        </Canvas>
      </div>
    </Card>
  );
};
