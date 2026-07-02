/**
 * Server-side helper for calling the backend gateway (ADR-0001: public traffic
 * only through the gateway). Never imported by client components.
 */

const DEFAULT_GATEWAY_URL = 'http://localhost:8080';
const DEFAULT_TIMEOUT_MS = 20_000;

export interface GatewayResult<T> {
  ok: boolean;
  status: number;
  data: T | null;
  error: string | null;
}

function gatewayBaseUrl(): string {
  return process.env.GATEWAY_URL ?? DEFAULT_GATEWAY_URL;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unexpected error';
}

export async function gatewayFetch<T>(
  path: string,
  init?: RequestInit & { timeoutMs?: number },
): Promise<GatewayResult<T>> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, ...rest } = init ?? {};
  const url = `${gatewayBaseUrl()}${path}`;
  try {
    const res = await fetch(url, {
      cache: 'no-store',
      signal: AbortSignal.timeout(timeoutMs),
      ...rest,
    });
    const text = await res.text();
    let data: T | null = null;
    if (text) {
      try {
        data = JSON.parse(text) as T;
      } catch {
        data = null;
      }
    }
    if (!res.ok) {
      return {
        ok: false,
        status: res.status,
        data,
        error: `Gateway responded with status ${res.status}`,
      };
    }
    return { ok: true, status: res.status, data, error: null };
  } catch (error: unknown) {
    console.error(`[gateway] ${path} failed:`, getErrorMessage(error));
    return { ok: false, status: 502, data: null, error: 'Backend gateway unreachable' };
  }
}

export function gatewayPostJson<T>(
  path: string,
  body: unknown,
  timeoutMs?: number,
): Promise<GatewayResult<T>> {
  return gatewayFetch<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    timeoutMs,
  });
}
