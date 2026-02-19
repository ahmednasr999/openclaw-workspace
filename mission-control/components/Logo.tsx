"use client";

interface LogoProps {
  size?: number;
}

export function Logo({ size = 34 }: LogoProps) {
  return (
    <svg width={size} height={size} viewBox="0 0 34 34" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="mc-grad" x1="0" y1="0" x2="34" y2="34" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#7c5cfc" />
          <stop offset="100%" stopColor="#ec4899" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="32" height="32" rx="8" stroke="url(#mc-grad)" strokeWidth="2" fill="none" />
      <path
        d="M8 24V10l5 10 4-10v14"
        stroke="url(#mc-grad)"
        strokeWidth="2.2"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M22 24V14a4 4 0 0 1 4-4"
        stroke="url(#mc-grad)"
        strokeWidth="2.2"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
