/**
 * POST /api/submit
 *
 * Accepts benchmark results from an agent, validates the caller's GitHub
 * identity, enforces per-user submit quotas, persists the results, and
 * enqueues a Layer 2 scoring job.
 *
 * Designed to run as a Cloudflare Worker (or any edge runtime that
 * implements the standard Request/Response API).
 */

export interface Env {
  /** Cloudflare KV namespace for quota tracking */
  QUOTA_KV: KVNamespace;
  /** Cloudflare KV namespace for run results */
  RUNS_KV: KVNamespace;
  /** Cloudflare Queue for Layer 2 scoring */
  SCORING_QUEUE?: Queue;
  /** Supabase connection (set via wrangler secret) */
  SUPABASE_URL?: string;
  SUPABASE_SERVICE_KEY?: string;
}

interface SubmitPayload {
  agent_name: string;
  benchmark_version: string;
  results: Record<string, unknown>;
  github_token: string;
}

interface GitHubUser {
  login: string;
  id: number;
}

interface QuotaRecord {
  used: number;
  period_start: string; // ISO date
}

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "https://getlegit.dev",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const FREE_LIMIT = 3;
const CONTRIBUTOR_LIMIT = 10;

/** Resolve the first day of the current UTC month as an ISO date string. */
function currentPeriodStart(): string {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1))
    .toISOString()
    .slice(0, 10);
}

/** Resolve the first day of the next UTC month as an ISO date string. */
function nextPeriodStart(): string {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1))
    .toISOString()
    .slice(0, 10);
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

/** Validate a GitHub personal access token and return the user. */
async function validateGitHubToken(token: string): Promise<GitHubUser> {
  const res = await fetch("https://api.github.com/user", {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "legit-api",
    },
  });

  if (!res.ok) {
    throw new Error("Invalid or expired GitHub token");
  }

  return (await res.json()) as GitHubUser;
}

/** Check if the user has at least 1 merged PR in the legit repo via GitHub API. */
async function isContributor(username: string): Promise<boolean> {
  try {
    const res = await fetch(
      `https://api.github.com/search/issues?q=repo:getlegitdev/legit+is:pr+is:merged+author:${encodeURIComponent(username)}`,
      {
        headers: {
          Accept: "application/vnd.github+json",
          "User-Agent": "legit-api",
        },
      }
    );
    if (!res.ok) return false;
    const data = await res.json() as { total_count: number };
    return data.total_count >= 1;
  } catch {
    return false;
  }
}

function generateRunId(): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 8);
  return `run_${ts}_${rand}`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS preflight
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (request.method !== "POST") {
      return jsonResponse({ error: "Method not allowed" }, 405);
    }

    // Payload size limit --------------------------------------------------------
    const contentLength = parseInt(request.headers.get("content-length") || "0");
    if (contentLength > 512_000) {
      return jsonResponse({ error: "Payload too large (max 512KB)" }, 413);
    }

    // Parse body ----------------------------------------------------------------
    let payload: SubmitPayload;
    try {
      payload = (await request.json()) as SubmitPayload;
    } catch {
      return jsonResponse({ error: "Invalid JSON body" }, 400);
    }

    const { agent_name, benchmark_version, results, github_token } = payload;

    if (!agent_name || !benchmark_version || !results || !github_token) {
      return jsonResponse(
        {
          error:
            "Missing required fields: agent_name, benchmark_version, results, github_token",
        },
        400,
      );
    }

    // Validate GitHub token -----------------------------------------------------
    let ghUser: GitHubUser;
    try {
      ghUser = await validateGitHubToken(github_token);
    } catch {
      return jsonResponse({ error: "GitHub authentication failed" }, 401);
    }

    // Enforce agent ownership: agent_name must be prefixed with GitHub username
    const expectedPrefix = `${ghUser.login}/`;
    if (!agent_name.startsWith(expectedPrefix)) {
      return jsonResponse(
        {
          error: `Agent name must start with your GitHub username: "${ghUser.login}/your-agent-name"`,
        },
        403,
      );
    }

    // Validate agent_name format ------------------------------------------------
    if (agent_name.length > 100) {
      return jsonResponse({ error: "agent_name too long (max 100 chars)" }, 400);
    }
    if (!/^[\w\-\/\.]+$/.test(agent_name)) {
      return jsonResponse(
        {
          error:
            "agent_name contains invalid characters (use alphanumeric, hyphens, dots, slashes)",
        },
        400,
      );
    }

    // Quota check ---------------------------------------------------------------
    const period = currentPeriodStart();
    const quotaKey = `quota:${ghUser.login}`;
    const raw = await env.QUOTA_KV.get(quotaKey);
    let quota: QuotaRecord = raw ? JSON.parse(raw) : { used: 0, period_start: period };

    // Reset quota if we rolled into a new month
    if (quota.period_start !== period) {
      quota = { used: 0, period_start: period };
    }

    const contributor = await isContributor(ghUser.login);
    const limit = contributor ? CONTRIBUTOR_LIMIT : FREE_LIMIT;

    if (quota.used >= limit) {
      return jsonResponse(
        {
          error: "Monthly submit quota exceeded",
          plan: contributor ? "Contributor" : "Free",
          used: quota.used,
          limit,
          resets_at: nextPeriodStart(),
        },
        429,
      );
    }

    // Persist results -----------------------------------------------------------
    const run_id = generateRunId();
    const runRecord = {
      run_id,
      agent_name,
      benchmark_version,
      submitted_by: ghUser.login,
      results,
      status: "queued" as const,
      created_at: new Date().toISOString(),
    };

    await env.RUNS_KV.put(`run:${run_id}`, JSON.stringify(runRecord), {
      // Auto-expire after 90 days
      expirationTtl: 90 * 24 * 60 * 60,
    });

    // Update quota --------------------------------------------------------------
    quota.used += 1;
    await env.QUOTA_KV.put(quotaKey, JSON.stringify(quota), {
      // Expire at the end of the month + 1 day buffer
      expirationTtl: 35 * 24 * 60 * 60,
    });

    // Enqueue Layer 2 scoring (if queue is configured) -------------------------
    if (env.SCORING_QUEUE) {
      await env.SCORING_QUEUE.send({
        run_id,
        agent_name,
        benchmark_version,
        results,
      });
    }

    // Sync to Supabase (if configured) -------------------------------------------
    if (env.SUPABASE_URL && env.SUPABASE_SERVICE_KEY) {
      try {
        const sbHeaders = {
          apikey: env.SUPABASE_SERVICE_KEY,
          Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
          "Content-Type": "application/json",
          Prefer: "return=minimal",
        };

        // Display name strips the username/ prefix
        const displayName = agent_name.includes("/")
          ? agent_name.split("/").slice(1).join("/")
          : agent_name;

        // Upsert agent
        const upsertResp = await fetch(`${env.SUPABASE_URL}/rest/v1/agents`, {
          method: "POST",
          headers: { ...sbHeaders, Prefer: "resolution=merge-duplicates,return=minimal" },
          body: JSON.stringify({
            name: displayName,
            author: ghUser.login,
            description: `Agent submitted by ${ghUser.login}`,
            updated_at: new Date().toISOString(),
          }),
        });
        if (!upsertResp.ok) {
          console.error("Supabase agent upsert failed:", upsertResp.status, await upsertResp.text());
        }

        // Get agent ID
        const agentResp = await fetch(
          `${env.SUPABASE_URL}/rest/v1/agents?name=eq.${encodeURIComponent(displayName)}&select=id`,
          { headers: sbHeaders }
        );
        const agents = (await agentResp.json()) as { id: string }[];
        const agentId = agents?.[0]?.id;

        if (agentId) {
          // Calculate total score from results
          const summary = results.summary || {};
          const totalScore = summary.total_score || 0;
          const tier =
            totalScore >= 90 ? "Platinum" :
            totalScore >= 75 ? "Gold" :
            totalScore >= 60 ? "Silver" :
            totalScore >= 40 ? "Bronze" : "Unranked";

          // Insert run
          await fetch(`${env.SUPABASE_URL}/rest/v1/runs`, {
            method: "POST",
            headers: sbHeaders,
            body: JSON.stringify({
              agent_id: agentId,
              benchmark_version,
              status: "completed",
              layer1_score: totalScore,
              total_score: totalScore,
              elo_rating: Math.round(1200 + (totalScore - 50) * 12),
              tier,
              total_duration_seconds: summary.total_duration || 0,
              scored_at: new Date().toISOString(),
            }),
          });

          // Get the run ID we just inserted
          const runResp = await fetch(
            `${env.SUPABASE_URL}/rest/v1/runs?agent_id=eq.${agentId}&order=scored_at.desc&limit=1&select=id`,
            { headers: sbHeaders }
          );
          const runs = (await runResp.json()) as { id: string }[];
          const runId = runs?.[0]?.id;

          // Insert task_scores
          if (runId && results.tasks && Array.isArray(results.tasks)) {
            const taskScores = results.tasks.map((t: any) => ({
              run_id: runId,
              task_id: t.task_id || "unknown",
              variant: t.variant || "a",
              category: t.category || "unknown",
              level: t.level || 1,
              layer1_score: t.layer1?.score ?? t.layer1_score ?? 0,
              combined_score: t.layer1?.score ?? t.combined_score ?? 0,
              duration_seconds: t.agent_metadata?.duration_seconds ?? t.duration_seconds ?? 0,
            }));

            // Batch insert (Supabase REST supports array body)
            await fetch(`${env.SUPABASE_URL}/rest/v1/task_scores`, {
              method: "POST",
              headers: sbHeaders,
              body: JSON.stringify(taskScores),
            });
          }

          // Refresh materialized views so leaderboard updates immediately
          await fetch(`${env.SUPABASE_URL}/rest/v1/rpc/refresh_leaderboard`, {
            method: "POST",
            headers: sbHeaders,
          }).catch(() => {});
        }
      } catch (err) {
        // Supabase sync failure is non-fatal — log for debugging
        console.error("Supabase sync error:", err);
      }
    }

    return jsonResponse({
      run_id,
      status: "queued",
      eta_minutes: 5,
    });
  },
};
