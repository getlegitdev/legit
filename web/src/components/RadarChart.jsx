const AXES = ['accuracy', 'completeness', 'quality', 'speed', 'robustness'];
const LABELS = ['Accuracy', 'Completeness', 'Quality', 'Speed', 'Robustness'];
const SIZE = 300;
const CENTER = SIZE / 2;
const RADIUS = 110;
const GRID_LEVELS = [0.2, 0.4, 0.6, 0.8, 1.0];

function polarToXY(angleDeg, r) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return [CENTER + r * Math.cos(rad), CENTER + r * Math.sin(rad)];
}

function getAngle(i) {
  return (360 / AXES.length) * i;
}

export default function RadarChart({ data = {} }) {
  const gridPolygons = GRID_LEVELS.map((level) => {
    const points = AXES.map((_, i) => polarToXY(getAngle(i), RADIUS * level));
    return points.map((p) => p.join(',')).join(' ');
  });

  const dataPoints = AXES.map((key, i) => {
    const val = Math.max(0, Math.min(100, data[key] || 0)) / 100;
    return polarToXY(getAngle(i), RADIUS * val);
  });
  const dataPolygon = dataPoints.map((p) => p.join(',')).join(' ');

  return (
    <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="mx-auto w-full max-w-[300px]">
      {/* Grid lines */}
      {gridPolygons.map((points, i) => (
        <polygon
          key={i}
          points={points}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth="1"
        />
      ))}

      {/* Axis lines */}
      {AXES.map((_, i) => {
        const [x, y] = polarToXY(getAngle(i), RADIUS);
        return (
          <line
            key={i}
            x1={CENTER}
            y1={CENTER}
            x2={x}
            y2={y}
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="1"
          />
        );
      })}

      {/* Data polygon */}
      <polygon
        points={dataPolygon}
        fill="rgba(127,119,221,0.25)"
        stroke="#7F77DD"
        strokeWidth="2"
      />

      {/* Data dots */}
      {dataPoints.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="3" fill="#7F77DD" />
      ))}

      {/* Labels */}
      {AXES.map((_, i) => {
        const [x, y] = polarToXY(getAngle(i), RADIUS + 20);
        return (
          <text
            key={i}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            fill="#9ca3af"
            fontSize="10"
            fontFamily="system-ui, sans-serif"
          >
            {LABELS[i]}
          </text>
        );
      })}
    </svg>
  );
}
