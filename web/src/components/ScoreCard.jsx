import Badge from './Badge';
import CategoryBar from './CategoryBar';

export default function ScoreCard({ agent = {} }) {
  const {
    name = 'Agent',
    score = 0,
    elo,
    tier = 'Unranked',
    categories = {},
    percentile,
  } = agent;

  const categoryEntries = Object.entries(categories);

  return (
    <div
      className="relative overflow-hidden rounded-2xl border border-white/10"
      style={{
        width: '100%',
        maxWidth: '600px',
        aspectRatio: '1200 / 630',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #2d1b69 50%, #1a1a2e 100%)',
      }}
    >
      <div className="flex h-full flex-col justify-between p-6 sm:p-8">
        {/* Top row */}
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold text-white sm:text-xl">{name}</span>
              <Badge tier={tier} />
            </div>
            {percentile != null && (
              <p className="mt-1 text-[12px] text-gray-400">
                Top {percentile}%
              </p>
            )}
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-white sm:text-4xl">{score}</div>
            <div className="text-[11px] uppercase tracking-wider text-gray-400">
              Score
            </div>
            {elo != null && (
              <div className="mt-1 text-[12px] text-gray-500">Elo {elo}</div>
            )}
          </div>
        </div>

        {/* Category bars */}
        {categoryEntries.length > 0 && (
          <div className="mt-4 space-y-2">
            {categoryEntries.map(([catName, catScore]) => (
              <CategoryBar key={catName} name={catName} score={catScore} />
            ))}
          </div>
        )}

        {/* Bottom branding */}
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo.png" alt="Legit" className="h-4 w-4 opacity-60" />
            <span className="text-[11px] font-medium text-gray-500">getlegit.dev</span>
          </div>
          <span className="text-[11px] text-gray-600">The trust layer for AI agents</span>
        </div>
      </div>
    </div>
  );
}
