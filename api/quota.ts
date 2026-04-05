/**
 * GET /api/quota/:username
 *
 * Returns the current submission quota usage and limits for a GitHub user.
 */

export interface Env {
  QUOTA_KV: KVNamespace;
}

interface QuotaRecord {
  used: number;
  period_start: string;
}

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

const FREE_LIMIT = 3;
const CONTRIBUTOR_LIMIT = 10;

function currentPeriodStart(): string {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), 1))
    .toISOString()
    .slice(0, 10);
}

function nextPeriodStart(): string {
  const now = new Date();
  return new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + 1, 1))
    .toISOString()
    .slice(0, 10);
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

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...CORS_HEADERS },
  });
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (request.method !== "GET") {
      return jsonResponse({ error: "Method not allowed" }, 405);
    }

    // Extract username from URL: /api/quota/:username
    const url = new URL(request.url);
    const segments = url.pathname.replace(/^\/+|\/+$/g, "").split("/");
    const username = segments[2] ? decodeURIComponent(segments[2]) : null;

    if (!username) {
      return jsonResponse({ error: "Missing username parameter" }, 400);
    }

    const period = currentPeriodStart();
    const quotaKey = `quota:${username}`;
    const raw = await env.QUOTA_KV.get(quotaKey);
    let quota: QuotaRecord = raw
      ? JSON.parse(raw)
      : { used: 0, period_start: period };

    // Reset if we've rolled into a new month
    if (quota.period_start !== period) {
      quota = { used: 0, period_start: period };
    }

    const contributor = await isContributor(username);
    const limit = contributor ? CONTRIBUTOR_LIMIT : FREE_LIMIT;

    return jsonResponse({
      username,
      plan: contributor ? "Contributor" : "Free",
      used: quota.used,
      limit,
      remaining: Math.max(0, limit - quota.used),
      resets_at: nextPeriodStart(),
    });
  },
};
