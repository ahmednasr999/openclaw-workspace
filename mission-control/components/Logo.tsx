"use client";

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c5cfc" />
          <stop offset="1" stopColor="#ec4899" />
        </linearGradient>
        <linearGradient id="ring-grad" x1="0" y1="0" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#7c5cfc" stopOpacity="0.3" />
          <stop offset="1" stopColor="#ec4899" stopOpacity="0.3" />
        </linearGradient>
      </defs>
      {/* Outer ring */}
      <circle cx="16" cy="16" r="14" stroke="url(#ring-grad)" strokeWidth="1.5" fill="none" />
      {/* Inner ring */}
      <circle cx="16" cy="16" r="9" stroke="url(#logo-grad)" strokeWidth="1.5" fill="none" opacity="0.6" />
      {/* Crosshair lines */}
      <line x1="16" y1="2" x2="16" y2="8" stroke="url(#logo-grad)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="16" y1="24" x2="16" y2="30" stroke="url(#logo-grad)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="2" y1="16" x2="8" y2="16" stroke="url(#logo-grad)" strokeWidth="1.5" strokeLinecap="round" />
      <line x1="24" y1="16" x2="30" y2="16" stroke="url(#logo-grad)" strokeWidth="1.5" strokeLinecap="round" />
      {/* Center dot */}
      <circle cx="16" cy="16" r="3" fill="url(#logo-grad)" />
      {/* Pulse ring */}
      <circle cx="16" cy="16" r="5.5" stroke="url(#logo-grad)" strokeWidth="1" fill="none" opacity="0.4">
        <animate attributeName="r" values="5;8;5" dur="3s" repeatCount="indefinite" />
        <animate attributeName="opacity" values="0.4;0.1;0.4" dur="3s" repeatCount="indefinite" />
      </circle>
    </svg>
  );
}
