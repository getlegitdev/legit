import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.PUBLIC_SUPABASE_URL ?? '';
const SUPABASE_ANON_KEY = import.meta.env.PUBLIC_SUPABASE_ANON_KEY ?? '';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Types for database tables
export interface Agent {
  id: string;
  name: string;
  author: string;
  github_url?: string;
  description?: string;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface Run {
  id: string;
  agent_id: string;
  benchmark_version: string;
  status: string;
  layer1_score?: number;
  total_score?: number;
  elo_rating?: number;
  tier?: string;
  total_duration_seconds?: number;
  submitted_at: string;
  scored_at?: string;
}

export interface TaskScore {
  id: string;
  run_id: string;
  task_id: string;
  variant: string;
  category: string;
  level: number;
  layer1_score?: number;
  layer1_checks?: any;
  layer2_score?: number;
  layer2_scores?: any;
  combined_score?: number;
  duration_seconds?: number;
  agent_output?: any;
  created_at: string;
}

// Query helpers
export async function getAgents(): Promise<Agent[]> {
  const { data } = await supabase
    .from('agents')
    .select('*')
    .order('created_at', { ascending: false });
  return data ?? [];
}

export async function getAgentById(id: string): Promise<Agent | null> {
  const { data } = await supabase
    .from('agents')
    .select('*')
    .eq('id', id)
    .single();
  return data;
}

export async function getRunsByAgent(agentId: string): Promise<Run[]> {
  const { data } = await supabase
    .from('runs')
    .select('*')
    .eq('agent_id', agentId)
    .order('submitted_at', { ascending: false });
  return data ?? [];
}

export async function getTaskScoresByRun(runId: string): Promise<TaskScore[]> {
  const { data } = await supabase
    .from('task_scores')
    .select('*')
    .eq('run_id', runId);
  return data ?? [];
}

export async function getCategoryLeaderboard(category: string) {
  // Fetch task_scores for the given category, joined with completed runs and agents
  const { data } = await supabase
    .from('task_scores')
    .select(`
      run_id,
      category,
      combined_score,
      layer1_score,
      runs!inner(agent_id, status, scored_at, agents!inner(name, author, avatar_url))
    `)
    .eq('category', category)
    .eq('runs.status', 'completed');

  if (!data || data.length === 0) return [];

  // Group by agent, keeping only scores from the latest run per agent
  const agentLatestRun = new Map<string, { run_id: string; scored_at: string }>();
  for (const row of data as any[]) {
    const agentId = row.runs.agent_id;
    const scoredAt = row.runs.scored_at || '';
    const existing = agentLatestRun.get(agentId);
    if (!existing || scoredAt > existing.scored_at) {
      agentLatestRun.set(agentId, { run_id: row.run_id, scored_at: scoredAt });
    }
  }

  // Aggregate scores from the latest run per agent
  const agentScores = new Map<string, { scores: number[]; name: string; author: string; agent_id: string }>();
  for (const row of data as any[]) {
    const agentId = row.runs.agent_id;
    const latest = agentLatestRun.get(agentId);
    if (!latest || row.run_id !== latest.run_id) continue;

    const score = row.combined_score ?? row.layer1_score ?? 0;
    if (!agentScores.has(agentId)) {
      agentScores.set(agentId, {
        scores: [],
        name: row.runs.agents?.name ?? 'Unknown',
        author: row.runs.agents?.author ?? 'Unknown',
        agent_id: agentId,
      });
    }
    agentScores.get(agentId)!.scores.push(score);
  }

  // Compute averages, sort, and rank
  const ranked = Array.from(agentScores.values())
    .map((a) => ({
      agent_id: a.agent_id,
      name: a.name,
      author: a.author,
      category_score: Math.round(a.scores.reduce((x, y) => x + y, 0) / a.scores.length),
    }))
    .sort((a, b) => b.category_score - a.category_score)
    .map((a, i) => ({ ...a, rank: i + 1 }));

  return ranked;
}

export async function getLeaderboard() {
  // Try materialized view first (fast but may be stale)
  const { data: mvData, error: mvError } = await supabase
    .from('leaderboard')
    .select('*')
    .order('rank', { ascending: true });

  if (mvData && mvData.length > 0) {
    return mvData;
  }

  // Fallback: direct query (always fresh)
  const { data } = await supabase
    .from('runs')
    .select(`
      agent_id,
      total_score,
      layer1_score,
      elo_rating,
      tier,
      scored_at,
      agents!inner(name, author, avatar_url)
    `)
    .eq('status', 'completed')
    .order('elo_rating', { ascending: false });

  if (!data) return [];

  // Deduplicate: keep only the latest run per agent
  const seen = new Set<string>();
  const unique = data.filter((r: any) => {
    if (seen.has(r.agent_id)) return false;
    seen.add(r.agent_id);
    return true;
  });

  return unique.map((r: any, i: number) => ({
    agent_id: r.agent_id,
    name: r.agents?.name ?? 'Unknown',
    author: r.agents?.author ?? 'Unknown',
    avatar_url: r.agents?.avatar_url,
    total_score: r.total_score,
    layer1_score: r.layer1_score,
    elo_rating: r.elo_rating,
    tier: r.tier,
    last_scored: r.scored_at,
    rank: i + 1,
  }));
}
