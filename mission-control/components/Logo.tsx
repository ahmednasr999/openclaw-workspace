"use client";

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Outer ring - subtle glow */}
      <circle cx="18" cy="18" r="17" stroke="url(#logoGradient)" strokeWidth="1.5" opacity="0.4" />
      {/* Inner ring */}
      <circle cx="18" cy="18" r="13" stroke="url(#logoGradient)" strokeWidth="1" opacity="0.2" />
      {/* Center diamond / compass */}
      <path
        d="M18 6L22 18L18 30L14 18Z"
        fill="url(#logoGradient)"
        opacity="0.15"
      />
      <path
        d="M6 18L18 14L30 18L18 22Z"
        fill="url(#logoGradient)"
        opacity="0.15"
      />
      {/* Center crosshair lines */}
      <line x1="18" y1="8" x2="18" y2="14" stroke="url(#logoGradient)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="18" y1="22" x2="18" y2="28" stroke="url(#logoGradient)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="8" y1="18" x2="14" y2="18" stroke="url(#logoGradient)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="22" y1="18" x2="28" y2="18" stroke="url(#logoGradient)" strokeWidth="1.5" strokeLinecap="round" />
      {/* Center dot */}
      <circle cx="18" cy="18" r="2.5" fill="url(#logoGradient)" />
      {/* Corner markers */}
      <circle cx="18" cy="8" r="1.5" fill="url(#logoGradient)" opacity="0.6" />
      <circle cx="18" cy="28" r="1.5" fill="url(#logoGradient)" opacity="0.6" />
      <circle cx="8" cy="18" r="1.5" fill="url(#logoGradient)" opacity="0.6" />
      <circle cx="28" cy="18" r="1.5" fill="url(#logoGradient)" opacity="0.6" />
      <defs>
        <linearGradient id="logoGradient" x1="6" y1="6" x2="30" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#a78bfa" />
          <stop offset="1" stopColor="#7c5cfc" />
        </linearGradient>
      </defs>
    </svg>
  );
}
