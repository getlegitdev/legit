// Tier thresholds based on score (consistent with CLI + API: 90/75/60/40)
export function getTierFromScore(score: number): string {
  if (score >= 90) return 'Platinum';
  if (score >= 75) return 'Gold';
  if (score >= 60) return 'Silver';
  if (score >= 40) return 'Bronze';
  return 'Unranked';
}

// Tier badge background colors
export const TIER_COLORS: Record<string, { bg: string; text: string }> = {
  Platinum: { bg: '#E8E0F0', text: '#4a3d6b' },
  Gold: { bg: '#FAEEDA', text: '#6b5a2e' },
  Silver: { bg: '#F1EFE8', text: '#5a5a5a' },
  Bronze: { bg: '#FAECE7', text: '#6b3d2e' },
  Unranked: { bg: '#374151', text: '#9ca3af' },
};

// Get tier color config
export function getTierColor(tier: string) {
  return TIER_COLORS[tier] ?? TIER_COLORS.Unranked;
}

// Format score with leading zero for single digits
export function formatScore(score: number): string {
  return Math.round(Math.max(0, Math.min(100, score))).toString();
}

// Calculate percentile from rank and total count
export function getPercentile(rank: number, total: number): number {
  if (total <= 0) return 100;
  return Math.max(1, Math.round((rank / total) * 100));
}

// Category labels
export const CATEGORIES = [
  'Research',
  'Extract',
  'Analyze',
  'Code',
  'Write',
  'Operate',
] as const;

export type Category = (typeof CATEGORIES)[number];
