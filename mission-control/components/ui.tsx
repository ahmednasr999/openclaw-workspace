import { ReactNode } from "react";

export function Panel({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) {
  return (
    <section className={`glass rounded-[10px] p-4 card-glow ${className}`}>
      <h3 className="mb-3 text-xs font-semibold uppercase tracking-widest text-[#4B6A9B]">{title}</h3>
      {children}
    </section>
  );
}
