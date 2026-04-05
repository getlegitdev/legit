export default function CategoryBar({ name, score }) {
  const clampedScore = Math.max(0, Math.min(100, Math.round(score)));
  const displayName = name.charAt(0).toUpperCase() + name.slice(1);
  return (
    <div className="flex items-center gap-3">
      <span className="w-20 shrink-0 text-[13px] text-gray-400">{displayName}</span>
      <div className="relative h-2 flex-1 overflow-hidden rounded-full bg-white/10">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-[#7F77DD] transition-all duration-700 ease-out"
          style={{ width: `${clampedScore}%` }}
        />
      </div>
      <span className="w-8 shrink-0 text-right font-mono text-[13px] text-white">
        {clampedScore}
      </span>
    </div>
  );
}
