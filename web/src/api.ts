export type ApiError = {
  status: number;
  message: string;
  details?: unknown;
};

let cachedBaseUrl: string | null = null;

function apiBaseUrl(): string {
  if (cachedBaseUrl) return cachedBaseUrl;

  const url = import.meta.env.VITE_API_BASE_URL as string | undefined;
  if (!url) throw new Error("Missing VITE_API_BASE_URL. Set it in web/.env");
  cachedBaseUrl = url.replace(/\/+$/, "");
  return cachedBaseUrl;
}

async function parseJsonSafe(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function apiPost<TResponse>(
  path: string,
  body: unknown,
  opts?: { timeoutMs?: number }
): Promise<TResponse> {
  const controller = new AbortController();
  const timeoutMs = opts?.timeoutMs ?? 180_000;
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${apiBaseUrl()}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    const data = await parseJsonSafe(res);

    if (!res.ok) {
      const err: ApiError = {
        status: res.status,
        message: typeof data === "string" ? data : "Request failed",
        details: typeof data === "string" ? undefined : data,
      };
      throw err;
    }

    return data as TResponse;
  } catch (e: any) {
    if (e?.name === "AbortError") {
      const err: ApiError = { status: 0, message: `Request timed out after ${timeoutMs}ms` };
      throw err;
    }
    throw e;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

