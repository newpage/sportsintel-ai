import { ReactNode } from "react";

export function Widget({ title, eyebrow, action, children, className = "" }: { title: string; eyebrow?: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`widget ${className}`}><header><div>{eyebrow && <span>{eyebrow}</span>}<h2>{title}</h2></div>{action}</header><div className="widget-body">{children}</div></section>;
}
