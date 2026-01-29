/**
 * Animated Background Component
 * ==============================
 * Beautiful warm gradient background like Sudowrite
 * Peachy/salmon transitioning to lavender/pink
 */

function AnimatedBackground() {
  return (
    <div 
      className="fixed inset-0 overflow-hidden"
      style={{ 
        background: 'linear-gradient(135deg, #FAD4C0 0%, #F8C8B8 20%, #F5B8C8 40%, #E8C4D8 60%, #D4C4E8 80%, #C8B8E8 100%)',
        zIndex: 0 
      }}
    >
      {/* Subtle noise overlay for texture */}
      <div 
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
          backgroundRepeat: 'repeat',
        }}
      />
    </div>
  )
}

export default AnimatedBackground
