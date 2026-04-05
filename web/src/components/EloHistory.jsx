const CHART_W = 800;
const CHART_H = 260;
const PAD = { top: 20, right: 20, bottom: 36, left: 48 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

export default function EloHistory({ history = [] }) {
  if (history.length < 2) {
    return (
      <div style={{ display: 'flex', height: 160, alignItems: 'center', justifyContent: 'center', color: '#6b7280', fontSize: 13 }}>
        Not enough data to display chart
      </div>
    );
  }

  const elos = history.map((h) => h.elo);
  const minElo = Math.min(...elos) - 30;
  const maxElo = Math.max(...elos) + 30;
  const eloRange = maxElo - minElo || 1;

  const xScale = (i) => PAD.left + (i / (history.length - 1)) * INNER_W;
  const yScale = (elo) => PAD.top + INNER_H - ((elo - minElo) / eloRange) * INNER_H;

  const pathD = history
    .map((h, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(h.elo)}`)
    .join(' ');

  const yTicks = [];
  const step = Math.ceil(eloRange / 4 / 10) * 10 || 10;
  for (let v = Math.ceil(minElo / step) * step; v <= maxElo; v += step) {
    yTicks.push(v);
  }

  const xLabels = [];
  const labelCount = Math.min(5, history.length);
  for (let i = 0; i < labelCount; i++) {
    const idx = Math.round((i / (labelCount - 1)) * (history.length - 1));
    xLabels.push({ idx, label: history[idx].date });
  }

  return (
    <svg viewBox={`0 0 ${CHART_W} ${CHART_H}`} style={{ width: '100%' }} preserveAspectRatio="xMidYMid meet">
      {yTicks.map((v) => (
        <g key={v}>
          <line x1={PAD.left} y1={yScale(v)} x2={CHART_W - PAD.right} y2={yScale(v)} stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
          <text x={PAD.left - 8} y={yScale(v)} textAnchor="end" dominantBaseline="middle" fill="#6b7280" fontSize="9" fontFamily="system-ui, sans-serif">{v}</text>
        </g>
      ))}
      {xLabels.map(({ idx, label }) => (
        <text key={idx} x={xScale(idx)} y={CHART_H - 8} textAnchor="middle" fill="#6b7280" fontSize="9" fontFamily="system-ui, sans-serif">{label}</text>
      ))}
      <path d={`${pathD} L ${xScale(history.length - 1)} ${PAD.top + INNER_H} L ${PAD.left} ${PAD.top + INNER_H} Z`} fill="url(#elo-gradient)" opacity="0.15" />
      <path d={pathD} fill="none" stroke="#7F77DD" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
      {history.map((h, i) => (
        <circle key={i} cx={xScale(i)} cy={yScale(h.elo)} r="3" fill="#7F77DD" stroke="#16162a" strokeWidth="1.5" />
      ))}
      <defs>
        <linearGradient id="elo-gradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#7F77DD" />
          <stop offset="100%" stopColor="#7F77DD" stopOpacity="0" />
        </linearGradient>
      </defs>
    </svg>
  );
}
