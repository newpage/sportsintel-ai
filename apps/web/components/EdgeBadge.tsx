export function EdgeBadge({ edge, label }: { edge: number; label?: string }) {
  const tone = edge >= 90 ? "elite" : edge >= 84 ? "strong" : edge >= 78 ? "consider" : "watch";
  return <div className={`edge-badge ${tone}`}><strong>{edge}</strong><span>{label || "Edge"}</span></div>;
}
