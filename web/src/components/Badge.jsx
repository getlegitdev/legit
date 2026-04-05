const tierConfig = {
  Platinum: { bg: '#E8E0F0', text: '#4a3d6b' },
  Gold: { bg: '#FAEEDA', text: '#6b5a2e' },
  Silver: { bg: '#F1EFE8', text: '#5a5a5a' },
  Bronze: { bg: '#FAECE7', text: '#6b3d2e' },
  Unranked: { bg: '#374151', text: '#9ca3af' },
};

export default function Badge({ tier = 'Unranked' }) {
  const config = tierConfig[tier] || tierConfig.Unranked;
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
      style={{ backgroundColor: config.bg, color: config.text }}
    >
      {tier}
    </span>
  );
}
