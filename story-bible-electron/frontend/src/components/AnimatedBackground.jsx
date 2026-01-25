/**
 * Animated Background Component
 * ==============================
 * High-end "Glow Follower / Liquid Mesh" effect
 * Electric Violet (#8B5CF6) blobs that respond to cursor
 */

import { useEffect, useRef } from 'react'
import { motion, useSpring, useMotionValue, useTransform } from 'framer-motion'

function AnimatedBackground() {
  const containerRef = useRef(null)
  
  // Mouse position with spring physics for smooth following
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  
  // Smooth spring configs for different blob speeds
  const springConfig = { damping: 25, stiffness: 150, mass: 0.5 }
  const slowSpringConfig = { damping: 40, stiffness: 90, mass: 1 }
  const slowerSpringConfig = { damping: 50, stiffness: 50, mass: 1.5 }
  
  // Primary blob follows cursor closely
  const blob1X = useSpring(mouseX, springConfig)
  const blob1Y = useSpring(mouseY, springConfig)
  
  // Secondary blob follows with delay
  const blob2X = useSpring(mouseX, slowSpringConfig)
  const blob2Y = useSpring(mouseY, slowSpringConfig)
  
  // Tertiary blob follows slowest
  const blob3X = useSpring(mouseX, slowerSpringConfig)
  const blob3Y = useSpring(mouseY, slowerSpringConfig)
  
  // Offset transforms for organic movement
  const blob1XOffset = useTransform(blob1X, (x) => x - 200)
  const blob1YOffset = useTransform(blob1Y, (y) => y - 200)
  
  const blob2XOffset = useTransform(blob2X, (x) => x + 100)
  const blob2YOffset = useTransform(blob2Y, (y) => y - 100)
  
  const blob3XOffset = useTransform(blob3X, (x) => x - 50)
  const blob3YOffset = useTransform(blob3Y, (y) => y + 150)
  
  useEffect(() => {
    const handleMouseMove = (e) => {
      mouseX.set(e.clientX)
      mouseY.set(e.clientY)
    }
    
    // Set initial position to center
    mouseX.set(window.innerWidth / 2)
    mouseY.set(window.innerHeight / 2)
    
    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [mouseX, mouseY])
  
  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 overflow-hidden"
      style={{ 
        background: '#000000',
        zIndex: 0 
      }}
    >
      {/* Ambient floating blobs - always drifting */}
      <motion.div
        className="absolute w-[600px] h-[600px] rounded-full opacity-20"
        style={{
          background: 'radial-gradient(circle, #8B5CF6 0%, #4C1D95 40%, transparent 70%)',
          filter: 'blur(80px)',
          x: blob1XOffset,
          y: blob1YOffset,
        }}
        animate={{
          scale: [1, 1.2, 1],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div
        className="absolute w-[500px] h-[500px] rounded-full opacity-15"
        style={{
          background: 'radial-gradient(circle, #6D28D9 0%, #4C1D95 40%, transparent 70%)',
          filter: 'blur(100px)',
          x: blob2XOffset,
          y: blob2YOffset,
        }}
        animate={{
          scale: [1.1, 0.9, 1.1],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      <motion.div
        className="absolute w-[700px] h-[700px] rounded-full opacity-10"
        style={{
          background: 'radial-gradient(circle, #7C3AED 0%, #312E81 40%, transparent 70%)',
          filter: 'blur(120px)',
          x: blob3XOffset,
          y: blob3YOffset,
        }}
        animate={{
          scale: [0.9, 1.15, 0.9],
        }}
        transition={{
          duration: 12,
          repeat: Infinity,
          ease: "easeInOut"
        }}
      />
      
      {/* Static ambient blobs for depth */}
      <div 
        className="absolute top-[10%] left-[20%] w-[400px] h-[400px] rounded-full opacity-10"
        style={{
          background: 'radial-gradient(circle, #8B5CF6 0%, transparent 70%)',
          filter: 'blur(80px)',
          animation: 'pulse 15s ease-in-out infinite',
        }}
      />
      
      <div 
        className="absolute bottom-[20%] right-[15%] w-[350px] h-[350px] rounded-full opacity-8"
        style={{
          background: 'radial-gradient(circle, #6D28D9 0%, transparent 70%)',
          filter: 'blur(90px)',
          animation: 'pulse 18s ease-in-out infinite reverse',
        }}
      />
      
      <div 
        className="absolute top-[60%] left-[60%] w-[300px] h-[300px] rounded-full opacity-5"
        style={{
          background: 'radial-gradient(circle, #A78BFA 0%, transparent 70%)',
          filter: 'blur(70px)',
          animation: 'pulse 20s ease-in-out infinite',
        }}
      />
      
      {/* Cursor glow - immediate follow */}
      <motion.div
        className="absolute w-[300px] h-[300px] rounded-full pointer-events-none"
        style={{
          background: 'radial-gradient(circle, rgba(139, 92, 246, 0.3) 0%, rgba(139, 92, 246, 0.1) 30%, transparent 60%)',
          filter: 'blur(40px)',
          x: useTransform(mouseX, (x) => x - 150),
          y: useTransform(mouseY, (y) => y - 150),
        }}
      />
      
      {/* Noise overlay for texture */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
        }}
      />
      
      {/* Vignette effect */}
      <div 
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.4) 100%)',
        }}
      />
      
      {/* Subtle grid pattern */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(139, 92, 246, 0.3) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(139, 92, 246, 0.3) 1px, transparent 1px)`,
          backgroundSize: '50px 50px',
        }}
      />
      
      {/* CSS Keyframes */}
      <style>{`
        @keyframes pulse {
          0%, 100% { transform: scale(1); opacity: 0.1; }
          50% { transform: scale(1.2); opacity: 0.15; }
        }
      `}</style>
    </div>
  )
}

export default AnimatedBackground
