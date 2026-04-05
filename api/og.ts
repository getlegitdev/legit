/**
 * GET /api/og/:agent_name
 *
 * Generates a stunning Open Graph Protocol image (1200x630 SVG) for social sharing.
 * "Spotify Wrapped" style score card with dark gradient background, circular score
 * badge, tier display, category bars, percentile, Elo rating, and Legit branding.
 */

export interface Env {
  LEADERBOARD_KV: KVNamespace;
}

interface LeaderboardEntry {
  agent_name: string;
  score: number;
  tier: string;
  elo: number;
  percentile: number;
  category_scores: Record<string, number>;
  benchmark_version: string;
  scored_at: string;
}

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};

const TIER_COLORS: Record<string, string> = {
  Platinum: "#b0b0b0",
  Gold: "#daa520",
  Silver: "#8a8a8a",
  Bronze: "#cd7f32",
  Unranked: "#9d9d9d",
};

const CATEGORY_ORDER = ["Research", "Extract", "Analyze", "Code", "Write", "Operate"];

function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function renderCategoryBar(
  name: string,
  score: number,
  y: number,
): string {
  const maxBarWidth = 380;
  const barWidth = Math.max(0, Math.min(maxBarWidth, (score / 100) * maxBarWidth));
  const labelX = 80;
  const barX = 210;
  const scoreX = barX + maxBarWidth + 18;

  return `
    <text x="${labelX}" y="${y + 15}" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="15" fill="#9ca3af" letter-spacing="0.3">${escapeXml(name)}</text>
    <rect x="${barX}" y="${y}" width="${maxBarWidth}" height="20" rx="4" fill="#1a1a2e"/>
    <rect x="${barX}" y="${y}" width="${barWidth}" height="20" rx="4" fill="#7F77DD" opacity="0.85"/>
    <rect x="${barX}" y="${y}" width="${barWidth}" height="10" rx="4" fill="#7F77DD"/>
    <text x="${scoreX}" y="${y + 15}" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="15" font-weight="600" fill="#e5e7eb">${score}</text>
  `;
}

function renderOGSvg(entry: LeaderboardEntry | null, agentName: string): string {
  const width = 1200;
  const height = 630;
  const tierColor = entry ? (TIER_COLORS[entry.tier] ?? "#8a8a8a") : "#8a8a8a";

  let content: string;

  if (!entry) {
    content = `
      <text x="600" y="280" text-anchor="middle" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="42" font-weight="700" fill="#ffffff">${escapeXml(agentName)}</text>
      <text x="600" y="330" text-anchor="middle" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="22" fill="#6b7280">Not yet ranked on Legit</text>
      <text x="600" y="380" text-anchor="middle" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="16" fill="#4b5563">Submit your agent at getlegit.dev</text>
    `;
  } else {
    const categories = CATEGORY_ORDER.filter((c) => c in entry.category_scores);
    const categoryBars = categories
      .map((name, i) => renderCategoryBar(name, entry.category_scores[name], 260 + i * 38))
      .join("");

    const tierBadge = entry.tier;
    const percentileText = entry.percentile != null ? `Top ${entry.percentile}%` : "";

    // Score circle (right side, top area)
    const cx = 960;
    const cy = 130;
    const r = 72;
    const circumference = 2 * Math.PI * r;
    const dashOffset = circumference - (entry.score / 100) * circumference;

    content = `
      <!-- Agent name -->
      <text x="80" y="90" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="38" font-weight="700" fill="#ffffff" letter-spacing="-0.5">${escapeXml(entry.agent_name)}</text>

      <!-- Tier badge -->
      <rect x="80" y="110" width="${tierBadge.length * 14 + 28}" height="32" rx="6" fill="${tierColor}" opacity="0.15"/>
      <circle cx="98" cy="126" r="4" fill="${tierColor}"/>
      <text x="110" y="131" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="15" font-weight="600" fill="${tierColor}">${escapeXml(tierBadge)}</text>

      <!-- Percentile -->
      ${percentileText ? `<text x="${80 + tierBadge.length * 14 + 44}" y="131" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="14" fill="#6b7280">${escapeXml(percentileText)}</text>` : ""}

      <!-- Elo rating -->
      ${entry.elo ? `
        <text x="80" y="170" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="14" fill="#6b7280">Elo</text>
        <text x="112" y="170" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="14" font-weight="600" fill="#9ca3af">${entry.elo}</text>
      ` : ""}

      <!-- Score circle -->
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#1a1a2e" stroke-width="8"/>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${tierColor}" stroke-width="8" stroke-linecap="round"
        stroke-dasharray="${circumference}" stroke-dashoffset="${dashOffset}"
        transform="rotate(-90 ${cx} ${cy})" opacity="0.8"/>
      <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="${tierColor}" stroke-width="3" stroke-linecap="round"
        stroke-dasharray="${circumference}" stroke-dashoffset="${dashOffset}"
        transform="rotate(-90 ${cx} ${cy})"/>
      <text x="${cx}" y="${cy - 5}" text-anchor="middle" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="48" font-weight="700" fill="#ffffff">${entry.score}</text>
      <text x="${cx}" y="${cy + 22}" text-anchor="middle" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="16" fill="#6b7280">/ 100</text>

      <!-- Divider -->
      <line x1="80" y1="220" x2="1120" y2="220" stroke="#ffffff" stroke-width="0.5" opacity="0.08"/>

      <!-- Category heading -->
      <text x="80" y="248" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="11" font-weight="600" fill="#4b5563" letter-spacing="1.5">CATEGORY SCORES</text>

      <!-- Category bars -->
      ${categoryBars}

      <!-- Legit logo block (bottom left) -->
      <rect x="80" y="${height - 65}" width="28" height="28" rx="6" fill="#7F77DD"/>
      <text x="88" y="${height - 44}" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="16" font-weight="700" fill="#ffffff">L</text>
      <text x="118" y="${height - 44}" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="15" font-weight="600" fill="#6b7280">getlegit.dev</text>

      <!-- Trust scores tagline (bottom right) -->
      <text x="1120" y="${height - 44}" text-anchor="end" font-family="system-ui, -apple-system, 'Segoe UI', sans-serif" font-size="13" fill="#374151">The trust layer for AI agents</text>
    `;
  }

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0.6" y2="1">
      <stop offset="0%" stop-color="#1a1a2e"/>
      <stop offset="100%" stop-color="#16162a"/>
    </linearGradient>
    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#7F77DD" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="transparent" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="${width}" height="${height}" fill="url(#bg)"/>
  <rect width="${width}" height="${height}" fill="url(#accent)"/>
  <!-- Subtle border -->
  <rect x="0.5" y="0.5" width="${width - 1}" height="${height - 1}" rx="0" fill="none" stroke="#ffffff" stroke-width="1" opacity="0.04"/>
  ${content}
</svg>`;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }

    if (request.method !== "GET") {
      return new Response("Method not allowed", { status: 405 });
    }

    // Extract agent_name from URL: /api/og/:agent_name
    const url = new URL(request.url);
    const segments = url.pathname.replace(/^\/+|\/+$/g, "").split("/");
    const agentName = segments[2] ? decodeURIComponent(segments[2]) : null;

    if (!agentName) {
      return new Response(JSON.stringify({ error: "Missing agent_name" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...CORS_HEADERS },
      });
    }

    // Look up agent on leaderboard
    const raw = await env.LEADERBOARD_KV.get("leaderboard");
    const board: LeaderboardEntry[] = raw ? JSON.parse(raw) : [];
    const entry =
      board.find(
        (e) => e.agent_name.toLowerCase() === agentName.toLowerCase(),
      ) ?? null;

    // Generate SVG
    const svg = renderOGSvg(entry, agentName);

    // In a production environment, this SVG would be converted to PNG using
    // resvg-wasm or a similar library. For now we return the SVG directly.
    //
    // To enable PNG output, add resvg-wasm:
    //   import { Resvg } from "@resvg/resvg-wasm";
    //   const resvg = new Resvg(svg, { fitTo: { mode: "width", value: 1200 } });
    //   const png = resvg.render().asPng();

    return new Response(svg, {
      status: 200,
      headers: {
        "Content-Type": "image/svg+xml",
        "Cache-Control": "public, max-age=3600, s-maxage=86400",
        ...CORS_HEADERS,
      },
    });
  },
};
