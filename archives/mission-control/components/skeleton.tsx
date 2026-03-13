"use client";

interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
  width?: string | number;
  height?: string | number;
}

export function Skeleton({ className = "", variant = "rectangular", width, height }: SkeletonProps) {
  const baseClasses = "animate-pulse bg-[var(--border)] opacity-50";
  
  const variantClasses = {
    text: "rounded",
    circular: "rounded-full",
    rectangular: "rounded-[8px]",
  };

  const style: React.CSSProperties = {
    width: width ?? "100%",
    height: height ?? (variant === "text" ? "1em" : "100%"),
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="glass rounded-[10px] p-5 space-y-3">
      <Skeleton height={14} width="40%" />
      <Skeleton height={40} width="60%" />
      <Skeleton height={12} width="30%" />
    </div>
  );
}

export function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-3 p-3 rounded-[8px] border border-[var(--border)]">
      <Skeleton variant="circular" width={32} height={32} />
      <div className="flex-1 space-y-2">
        <Skeleton height={14} width="60%" />
        <Skeleton height={10} width="40%" />
      </div>
    </div>
  );
}

export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <div className="flex items-center gap-4 p-4 border-b border-[var(--border)]">
      {Array.from({ length: columns }).map((_, i) => (
        <Skeleton key={i} height={12} width={`${80 / columns}%`} />
      ))}
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="glass rounded-[10px] p-5">
      <Skeleton height={12} width="40%" />
      <Skeleton height={48} width="60%" className="mt-3" />
      <Skeleton height={10} width="50%" className="mt-3" />
    </div>
  );
}
