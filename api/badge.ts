/**
 * GET /api/badge/:agent_name
 *
 * Returns a shields.io-compatible SVG badge showing the agent's Legit
 * score and tier. The badge is fully self-contained (inline SVG, no
 * external service calls) and includes cache headers for CDN edge caching.
 */

export interface Env {
  LEADERBOARD_KV: KVNamespace;
}

interface LeaderboardEntry {
  agent_name: string;
  score: number;
  tier: string;
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

function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function measureTextWidth(text: string, fontSize: number): number {
  // Rough character width for Verdana/DejaVu Sans at a given font size.
  // Average character width is ~0.6 * fontSize for these fonts.
  return Math.ceil(text.length * fontSize * 0.62) + 10;
}

function renderBadgeSVG(
  label: string,
  value: string,
  color: string,
): string {
  const fontSize = 11;
  const labelWidth = measureTextWidth(label, fontSize);
  const valueWidth = measureTextWidth(value, fontSize);
  const totalWidth = labelWidth + valueWidth;
  const labelX = labelWidth / 2;
  const valueX = labelWidth + valueWidth / 2;

  // Shields.io flat-style badge
  const safeLabel = escapeXml(label);
  const safeValue = escapeXml(value);

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${totalWidth}" height="20" role="img" aria-label="${safeLabel}: ${safeValue}">
  <title>${safeLabel}: ${safeValue}</title>
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r">
    <rect width="${totalWidth}" height="20" rx="3" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#r)">
    <rect width="${labelWidth}" height="20" fill="#555"/>
    <rect x="${labelWidth}" width="${valueWidth}" height="20" fill="${color}"/>
    <rect width="${totalWidth}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="${fontSize}">
    <text x="${labelX}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="${(labelWidth - 10) * 10}">${safeLabel}</text>
    <text x="${labelX}" y="140" transform="scale(.1)" textLength="${(labelWidth - 10) * 10}">${safeLabel}</text>
    <text x="${valueX}" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="${(valueWidth - 10) * 10}">${safeValue}</text>
    <text x="${valueX}" y="140" transform="scale(.1)" textLength="${(valueWidth - 10) * 10}">${safeValue}</text>
  </g>
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

    // Extract agent_name from URL path: /api/badge/:agent_name
    const url = new URL(request.url);
    const segments = url.pathname.replace(/^\/+|\/+$/g, "").split("/");
    // Expect ["api", "badge", "<agent_name>"]
    const agentName = segments[2] ? decodeURIComponent(segments[2]) : null;

    if (!agentName) {
      return new Response(
        renderBadgeSVG("legit", "unknown", "#9d9d9d"),
        {
          status: 404,
          headers: {
            "Content-Type": "image/svg+xml",
            "Cache-Control": "public, max-age=300",
            ...CORS_HEADERS,
          },
        },
      );
    }

    // Look up agent on leaderboard
    const raw = await env.LEADERBOARD_KV.get("leaderboard");
    const board: LeaderboardEntry[] = raw ? JSON.parse(raw) : [];
    const entry = board.find(
      (e) => e.agent_name.toLowerCase() === agentName.toLowerCase(),
    );

    let value: string;
    let color: string;

    if (entry) {
      value = `${entry.score} (${entry.tier})`;
      color = TIER_COLORS[entry.tier] ?? "#9d9d9d";
    } else {
      value = "not ranked";
      color = "#9d9d9d";
    }

    const svg = renderBadgeSVG("legit", value, color);

    return new Response(svg, {
      status: 200,
      headers: {
        "Content-Type": "image/svg+xml",
        "Cache-Control": "public, max-age=300, s-maxage=600",
        ...CORS_HEADERS,
      },
    });
  },
};
