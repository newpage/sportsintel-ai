export function ConfidenceBar({ value }: { value: number }) {
  return <div className="confidence-block"><div><span>Confidence</span><strong>{value}%</strong></div><div className="confidence-track"><span style={{ width: `${value}%` }} /></div></div>;
}
