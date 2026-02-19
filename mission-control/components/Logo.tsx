"use client";

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Background */}
      <rect width="32" height="32" rx="8" fill="url(#logoGradient)" opacity="0.1"/>
      
      {/* M letter - clean geometric */}
      <path 
        d="M8 22V10L12 6L16 14L20 6L24 10V22H20V14L16 20L12 14V22H8Z" 
        fill="url(#logoGradient)"
      />
      
      {/* C letter - subtle accent */}
      <circle cx="26" cy="20" r="3" fill="url(#logoGradient)" opacity="0.6"/>
      
      <defs>
        <linearGradient id="logoGradient" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c5cfc"/>
          <stop offset="1" stopColor="#ec4899"/>
        </linearGradient>
      </defs>
    </svg>
  );
}
