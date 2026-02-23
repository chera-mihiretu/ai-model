/**
 * Animated Background Component with tsParticles + Logo Particles
 * ================================================================
 * Interactive particle animation with golden particles
 * Logo formed by particles that scatter on mouse hover
 * Full-screen luxurious background animation
 */

import { useCallback, useMemo, useState, useEffect, useRef } from 'react';
import Particles, { initParticlesEngine } from '@tsparticles/react';
import { loadSlim } from '@tsparticles/slim';

// Import the logo SVG directly - Vite handles this properly for both dev and production
import logoSvgUrl from '/assets/logo.svg?url';

// Custom hook to create logo particles from SVG
function useLogoParticles(svgUrl, particleCount = 800, scale = 1) {
  const [points, setPoints] = useState([]);

  useEffect(() => {
    const extractPointsFromSVG = async () => {
      try {
        // Use imported URL for proper bundling, with fallback for dynamic URLs
        const urlToFetch = svgUrl === 'assets/logo.svg' ? logoSvgUrl : svgUrl;
        const response = await fetch(urlToFetch);
        const svgText = await response.text();
        
        // Create a temporary canvas to render the SVG at high resolution
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        // Parse SVG dimensions - use higher resolution for precision
        const widthMatch = svgText.match(/width="([^"]+)"/);
        const heightMatch = svgText.match(/height="([^"]+)"/);
        const baseWidth = widthMatch ? parseFloat(widthMatch[1]) : 500;
        const baseHeight = heightMatch ? parseFloat(heightMatch[1]) : 500;
        
        // Render at higher resolution for more precise sampling
        canvas.width = baseWidth * scale * 2;
        canvas.height = baseHeight * scale * 2;
        
        // Create an image from the SVG
        const img = new Image();
        const svgBlob = new Blob([svgText], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(svgBlob);
        
        img.onload = () => {
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const data = imageData.data;
          
          // Sample points from non-transparent pixels with finer step
          const extractedPoints = [];
          // Calculate step to get enough points - smaller step = more precision
          const targetPoints = particleCount * 3; // Over-sample for better selection
          const step = Math.max(1, Math.floor(Math.sqrt((canvas.width * canvas.height) / targetPoints)));
          
          for (let y = 0; y < canvas.height; y += step) {
            for (let x = 0; x < canvas.width; x += step) {
              const i = (y * canvas.width + x) * 4;
              const alpha = data[i + 3];
              
              // If pixel is not transparent (part of logo)
              if (alpha > 30) {
                extractedPoints.push({
                  x: (x / canvas.width) * 100,
                  y: (y / canvas.height) * 100,
                });
              }
            }
          }
          
          // Randomly shuffle and select points to match desired count
          const shuffled = extractedPoints.sort(() => Math.random() - 0.5);
          setPoints(shuffled.slice(0, particleCount));
          
          URL.revokeObjectURL(url);
        };
        
        img.src = url;
      } catch (error) {
        console.error('Error extracting points from SVG:', error);
      }
    };

    extractPointsFromSVG();
  }, [svgUrl, particleCount, scale]);

  return points;
}

// Logo Particle Canvas Component
function LogoParticleCanvas({ logoPoints }) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const animationRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const parent = canvas.parentElement;

    // Calculate logo bounds within the canvas (centered, much larger)
    const getLogoBounds = () => {
      // Use 90% of the smaller dimension for a much bigger logo
      const logoSize = Math.min(canvas.width, canvas.height) * 0.9;
      // Always center perfectly in the middle of the screen
      return {
        x: (canvas.width - logoSize) / 2,
        y: (canvas.height - logoSize) / 2,
        width: logoSize,
        height: logoSize,
      };
    };

    // Initialize/update particles from logo points
    const initParticles = () => {
      const bounds = getLogoBounds();
      particlesRef.current = logoPoints.map((point, i) => {
        const existing = particlesRef.current[i];
        return {
          id: i,
          // Original position (percentage) converted to canvas position
          originX: bounds.x + (point.x / 100) * bounds.width,
          originY: bounds.y + (point.y / 100) * bounds.height,
          x: bounds.x + (point.x / 100) * bounds.width,
          y: bounds.y + (point.y / 100) * bounds.height,
          vx: 0,
          vy: 0,
          // Preserve particle appearance if already exists, otherwise create new
          baseSize: existing?.baseSize ?? (Math.random() * 0.6 + 0.5),
          size: existing?.size ?? (Math.random() * 0.6 + 0.5),
          baseOpacity: existing?.baseOpacity ?? (Math.random() * 0.4 + 0.5),
          opacity: existing?.opacity ?? (Math.random() * 0.4 + 0.5),
          color: existing?.color ?? [
            '#FFD700', '#D4AF37', '#B8860B', '#DAA520', 
            '#F0E68C', '#FFDF00', '#FFC125', '#CD950C',
            '#FFFACD', '#FFE4B5', '#FFF8DC'
          ][Math.floor(Math.random() * 11)],
          // Sparkle properties
          sparkleSpeed: Math.random() * 3 + 1,
          sparkleOffset: Math.random() * Math.PI * 2,
          sparkleIntensity: Math.random() * 0.5 + 0.3,
          isSparkler: Math.random() < 0.15, // 15% of particles are extra sparkly
        };
      });
    };

    // Resize canvas and reinitialize particles to keep logo centered
    const resizeCanvas = () => {
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
      // Reinitialize particles with new bounds to keep logo centered
      if (logoPoints.length > 0) {
        initParticles();
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    if (logoPoints.length > 0) {
      initParticles();
    }

    // Mouse tracking
    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      };
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('mousemove', handleMouseMove);

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const repulseDistance = 180;
      const repulseForce = 8;
      const returnSpeed = 0.05;
      const friction = 0.92;
      const time = Date.now() * 0.001;

      particlesRef.current.forEach((particle) => {
        // Calculate distance from mouse
        const dx = particle.x - mouseRef.current.x;
        const dy = particle.y - mouseRef.current.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // Repulse from mouse
        if (distance < repulseDistance && distance > 0) {
          const force = (repulseDistance - distance) / repulseDistance;
          const angle = Math.atan2(dy, dx);
          particle.vx += Math.cos(angle) * force * repulseForce;
          particle.vy += Math.sin(angle) * force * repulseForce;
        }

        // Return to original position
        const originDx = particle.originX - particle.x;
        const originDy = particle.originY - particle.y;
        particle.vx += originDx * returnSpeed;
        particle.vy += originDy * returnSpeed;

        // Apply friction
        particle.vx *= friction;
        particle.vy *= friction;

        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Add very subtle idle movement
        const idleX = Math.sin(time + particle.id * 0.05) * 0.12;
        const idleY = Math.cos(time * 0.8 + particle.id * 0.08) * 0.12;
        particle.x += idleX;
        particle.y += idleY;

        // Calculate sparkle effect
        const sparkleWave = Math.sin(time * particle.sparkleSpeed + particle.sparkleOffset);
        const sparkle = (sparkleWave + 1) / 2; // Normalize to 0-1
        
        // Apply sparkle to size and opacity
        let currentSize = particle.baseSize;
        let currentOpacity = particle.baseOpacity;
        let currentShadowBlur = 3;
        
        if (particle.isSparkler) {
          // Extra sparkly particles get more dramatic effect
          currentSize = particle.baseSize * (1 + sparkle * 0.8);
          currentOpacity = particle.baseOpacity + sparkle * 0.5;
          currentShadowBlur = 6 + sparkle * 10;
        } else {
          // Normal particles get subtle sparkle
          currentSize = particle.baseSize * (1 + sparkle * particle.sparkleIntensity * 0.3);
          currentOpacity = particle.baseOpacity + sparkle * particle.sparkleIntensity * 0.3;
          currentShadowBlur = 3 + sparkle * 4;
        }
        
        // Clamp opacity
        currentOpacity = Math.min(1, currentOpacity);

        // Draw particle with sparkle glow
        ctx.save();
        ctx.beginPath();
        ctx.arc(particle.x, particle.y, currentSize, 0, Math.PI * 2);
        ctx.fillStyle = particle.color;
        ctx.globalAlpha = currentOpacity;
        ctx.shadowColor = particle.isSparkler ? '#FFFFFF' : particle.color;
        ctx.shadowBlur = currentShadowBlur;
        ctx.fill();
        
        // Add extra bright core for sparklers at peak
        if (particle.isSparkler && sparkle > 0.7) {
          ctx.beginPath();
          ctx.arc(particle.x, particle.y, currentSize * 0.5, 0, Math.PI * 2);
          ctx.fillStyle = '#FFFFFF';
          ctx.globalAlpha = (sparkle - 0.7) * 2;
          ctx.fill();
        }
        
        ctx.restore();
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    if (logoPoints.length > 0) {
      animate();
    }

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('mousemove', handleMouseMove);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [logoPoints]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 pointer-events-auto"
      style={{ zIndex: 1 }}
    />
  );
}

function AnimatedBackground() {
  const [init, setInit] = useState(false);
  const containerRef = useRef(null);
  
  // Extract logo particle positions - reduced from 8000 to 2000 for lower memory usage
  // Use imported logo URL for proper production support
  const logoPoints = useLogoParticles(logoSvgUrl, 2000, 1.5);

  // Initialize tsParticles engine
  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setInit(true);
    });
  }, []);

  const particlesLoaded = useCallback((container) => {
    containerRef.current = container;
  }, []);

  // Background particle configuration - subtle ambient particles
  const options = useMemo(
    () => ({
      fullScreen: {
        enable: false,
        zIndex: 0,
      },
      background: {
        color: {
          value: 'transparent',
        },
      },
      fpsLimit: 30,
      detectRetina: true,
      interactivity: {
        detectsOn: 'window',
        events: {
          onHover: {
            enable: true,
            mode: 'repulse',
          },
          onClick: {
            enable: false,
          },
          resize: {
            enable: true,
          },
        },
        modes: {
          repulse: {
            distance: 120,
            duration: 0.4,
            speed: 0.5,
            factor: 50,
            maxSpeed: 25,
            easing: 'ease-out-quad',
          },
        },
      },
      particles: {
        color: {
          value: ['#D4AF37', '#FFD700', '#B8860B', '#DAA520'],
        },
        move: {
          enable: true,
          speed: { min: 0.2, max: 0.6 },
          direction: 'none',
          random: true,
          straight: false,
          outModes: {
            default: 'bounce',
          },
        },
        number: {
          value: 60,
          density: {
            enable: true,
            width: 1920,
            height: 1080,
          },
        },
        opacity: {
          value: {
            min: 0.1,
            max: 0.4,
          },
          animation: {
            enable: true,
            speed: 0.5,
            sync: false,
          },
        },
        shape: {
          type: 'circle',
        },
        size: {
          value: {
            min: 0.5,
            max: 2,
          },
          animation: {
            enable: true,
            speed: 1,
            sync: false,
          },
        },
        links: {
          enable: false,
        },
        twinkle: {
          particles: {
            enable: true,
            frequency: 0.02,
            opacity: 0.8,
            color: {
              value: '#FFD700',
            },
          },
        },
      },
      smooth: true,
    }),
    []
  );

  return (
    <div
      className="fixed inset-0 overflow-hidden"
      style={{
        background:
          'linear-gradient(145deg, #0A0A0F 0%, #0F0F14 30%, #121218 60%, #0F0F14 80%, #0A0A0F 100%)',
        zIndex: 0,
      }}
    >
      {/* Radial gold glow from center for logo area */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1200px] h-[1200px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at center, rgba(212, 175, 55, 0.08) 0%, rgba(212, 175, 55, 0.03) 40%, transparent 70%)',
          zIndex: 0,
        }}
      />

      {/* Radial gold glow from top */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at center top, rgba(212, 175, 55, 0.06) 0%, rgba(212, 175, 55, 0.02) 40%, transparent 70%)',
        }}
      />

      {/* Subtle bottom gold accent */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[1000px] h-[300px] pointer-events-none"
        style={{
          background:
            'radial-gradient(ellipse at center bottom, rgba(184, 134, 11, 0.04) 0%, transparent 60%)',
        }}
      />

      {/* Corner gold accents */}
      <div
        className="absolute top-0 right-0 w-[400px] h-[400px] pointer-events-none"
        style={{
          background:
            'radial-gradient(circle at top right, rgba(212, 175, 55, 0.03) 0%, transparent 60%)',
        }}
      />
      <div
        className="absolute bottom-0 left-0 w-[400px] h-[400px] pointer-events-none"
        style={{
          background:
            'radial-gradient(circle at bottom left, rgba(212, 175, 55, 0.025) 0%, transparent 60%)',
        }}
      />

      {/* Background ambient particles */}
      {init && (
        <div className="absolute inset-0" style={{ zIndex: 0 }}>
          <Particles
            id="tsparticles-ambient"
            particlesLoaded={particlesLoaded}
            options={options}
            className="absolute inset-0"
          />
        </div>
      )}

      {/* Logo Particle Canvas - Main interactive element */}
      {logoPoints.length > 0 && (
        <LogoParticleCanvas logoPoints={logoPoints} />
      )}

      {/* Loading indicator */}
      {(!init || logoPoints.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="flex space-x-2">
            {[0, 1, 2].map((i) => (
              <div
                key={i}
                className="w-2 h-2 rounded-full animate-pulse"
                style={{
                  background: 'rgba(212, 175, 55, 0.6)',
                  boxShadow: '0 0 10px rgba(212, 175, 55, 0.4)',
                  animationDelay: `${i * 0.2}s`,
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Subtle noise overlay for texture */}
      <div
        className="absolute inset-0 opacity-[0.012] pointer-events-none"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
          zIndex: 5,
        }}
      />

      {/* Elegant gold line decorations */}
      <div
        className="absolute top-0 left-0 right-0 h-px pointer-events-none"
        style={{
          background:
            'linear-gradient(90deg, transparent 0%, rgba(212, 175, 55, 0.25) 50%, transparent 100%)',
          zIndex: 5,
        }}
      />
      <div
        className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
        style={{
          background:
            'linear-gradient(90deg, transparent 0%, rgba(212, 175, 55, 0.12) 50%, transparent 100%)',
          zIndex: 5,
        }}
      />
    </div>
  );
}

export default AnimatedBackground;
