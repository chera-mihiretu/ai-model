/**
 * Animated Background Component
 * ==============================
 * Beautiful dark background with golden accents
 * Elegant, luxurious feel inspired by premium apps
 */

function AnimatedBackground() {
  return (
    <div 
      className="fixed inset-0 overflow-hidden"
      style={{ 
        background: 'linear-gradient(145deg, #0A0A0F 0%, #0F0F14 30%, #121218 60%, #0F0F14 80%, #0A0A0F 100%)',
        zIndex: 0 
      }}
    >
      {/* Radial gold glow from top */}
      <div 
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px]"
        style={{
          background: 'radial-gradient(ellipse at center top, rgba(212, 175, 55, 0.08) 0%, rgba(212, 175, 55, 0.02) 40%, transparent 70%)',
        }}
      />
      
      {/* Subtle bottom gold accent */}
      <div 
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[1000px] h-[300px]"
        style={{
          background: 'radial-gradient(ellipse at center bottom, rgba(184, 134, 11, 0.05) 0%, transparent 60%)',
        }}
      />
      
      {/* Corner gold accents */}
      <div 
        className="absolute top-0 right-0 w-[400px] h-[400px]"
        style={{
          background: 'radial-gradient(circle at top right, rgba(212, 175, 55, 0.04) 0%, transparent 60%)',
        }}
      />
      <div 
        className="absolute bottom-0 left-0 w-[400px] h-[400px]"
        style={{
          background: 'radial-gradient(circle at bottom left, rgba(212, 175, 55, 0.03) 0%, transparent 60%)',
        }}
      />
      
      {/* Animated gold particles (subtle) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating gold particles */}
        <div 
          className="absolute w-1 h-1 rounded-full animate-float"
          style={{
            background: 'rgba(212, 175, 55, 0.4)',
            top: '20%',
            left: '15%',
            animationDelay: '0s',
            animationDuration: '8s',
          }}
        />
        <div 
          className="absolute w-1.5 h-1.5 rounded-full animate-float"
          style={{
            background: 'rgba(212, 175, 55, 0.3)',
            top: '60%',
            left: '80%',
            animationDelay: '2s',
            animationDuration: '10s',
          }}
        />
        <div 
          className="absolute w-1 h-1 rounded-full animate-float"
          style={{
            background: 'rgba(212, 175, 55, 0.35)',
            top: '40%',
            left: '90%',
            animationDelay: '4s',
            animationDuration: '7s',
          }}
        />
        <div 
          className="absolute w-0.5 h-0.5 rounded-full animate-float"
          style={{
            background: 'rgba(212, 175, 55, 0.5)',
            top: '80%',
            left: '10%',
            animationDelay: '1s',
            animationDuration: '9s',
          }}
        />
        <div 
          className="absolute w-1 h-1 rounded-full animate-float"
          style={{
            background: 'rgba(212, 175, 55, 0.25)',
            top: '30%',
            left: '50%',
            animationDelay: '3s',
            animationDuration: '11s',
          }}
        />
      </div>
      
      {/* Subtle noise overlay for texture */}
      <div 
        className="absolute inset-0 opacity-[0.015]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
        }}
      />
      
      {/* Elegant gold line decorations */}
      <div 
        className="absolute top-0 left-0 right-0 h-px"
        style={{
          background: 'linear-gradient(90deg, transparent 0%, rgba(212, 175, 55, 0.3) 50%, transparent 100%)',
        }}
      />
    </div>
  )
}

export default AnimatedBackground
