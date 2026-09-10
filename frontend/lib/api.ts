// Typed API client for the Wealth Intelligence AI backend.
// Mirrors the three-layer envelope contract (see backend docs/02-data-model.md).

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
const V1 = `${BASE}/v1`;

export type Lang = "en" | "ar";

export interface Observed {
  field: string;
  value: unknown;
  source: string;
  as_of: string;
  unit?: string | null;
}
export interface Derived {
  metric: string;
  value: unknown;
  methodology: string;
  parameters: Record<string, unknown>;
  model_version: string;
  confidence?: number | null;
}
export interface Narrative {
  text: string;
  citations: string[];
  kind: "interpretation" | "scenario";
  speculative: boolean;
  section?: string | null;
}
export interface Envelope {
  observed: Observed[];
  derived: Derived[];
  narrative: Narrative[];
  disclaimers: string[];
  language: Lang;
  audit_record_id?: string | null;
}

export interface Asset {
  id: string;
  symbol: string;
  name: string;
  asset_class: string;
  currency: string;
  country?: string | null;
  sector?: string | null;
}

export interface Portfolio {
  id: string;
  name: string;
  base_currency: string;
  kind: string;
  constraints: Record<string, unknown>;
  positions: { asset_id: string; quantity: number }[];
}

// --- token storage (per-browser convenience; wrapped in try/catch) ---------
const TOKEN_KEY = "wia_token";
export function getToken(): string | null {
  try {
    return typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_KEY) : null;
  } catch {
    return null;
  }
}
export function setToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${V1}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

export const api = {
  async login(email: string, password: string): Promise<string> {
    const form = new URLSearchParams({ username: email, password, grant_type: "password" });
    const res = await fetch(`${V1}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
    if (!res.ok) throw new Error("login failed");
    const data = (await res.json()) as { access_token: string };
    setToken(data.access_token);
    return data.access_token;
  },

  searchAssets: (q = ""): Promise<Asset[]> => req(`/assets?q=${encodeURIComponent(q)}`),
  getAsset: (id: string): Promise<Asset> => req(`/assets/${id}`),
  deepDive: (symbol: string, language: Lang): Promise<Envelope> =>
    req(`/assets/${symbol}/deep-dive`, { method: "POST", body: JSON.stringify({ language }) }),

  listPortfolios: (): Promise<Portfolio[]> => req(`/portfolios`),
  analyzePortfolio: (
    id: string,
    language: Lang,
    scenarios: { name: string; shocks: Record<string, number> }[] = [],
  ): Promise<Envelope> =>
    req(`/portfolios/${id}/analyze`, {
      method: "POST",
      body: JSON.stringify({ language, scenarios }),
    }),

  generateSignal: (symbol: string, language: Lang) =>
    req(`/signals/generate`, {
      method: "POST",
      body: JSON.stringify({ symbol, horizon: "swing", language }),
    }),

  requestReport: (body: {
    kind: string;
    subject_type: string;
    subject_id: string;
    language: Lang;
  }) => req(`/reports`, { method: "POST", body: JSON.stringify(body) }),
  listReports: () => req(`/reports`),
  getReport: (id: string) => req(`/reports/${id}`),

  usage: () => req(`/usage`),
};
