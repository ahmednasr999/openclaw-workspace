"use client";

export function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      {/* Simple "MC" text - matching the clean sidebar icon style */}
      <text
        x="12"
        y="17"
        textAnchor="middle"
        fontSize="14"
        fontWeight="600"
        fill="currentColor"
        style={{ fontFamily: 'Inter, sans-serif', letterSpacing: '-0.5px' }}
      >
        MC
      </text>
    </svg>
  );
}
