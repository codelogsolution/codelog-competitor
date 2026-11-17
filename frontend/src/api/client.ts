const DEFAULT_API_BASE_URL = import.meta.env.DEV ? "http://127.0.0.1:8000/api/v1" : "/api/v1";
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL).replace(/\/$/, "");
const SERVER_UNAVAILABLE_MESSAGE = "The server is temporarily unavailable. Please try again in a moment.";

type RequestOptions = RequestInit & { params?: Record<string, string | number | undefined> };

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...init } = options;
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  });

  const timeoutMs = init.body instanceof FormData ? 120_000 : init.method === "GET" || !init.method ? 12_000 : 30_000;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  let response: Response;
  try {
    response = await fetch(url.toString(), {
      ...init,
      signal: controller.signal,
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...headers,
      },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`KOMP API is unavailable or did not respond within ${Math.round(timeoutMs / 1000)} seconds. Check that the backend started successfully and DATABASE_URL points to PostgreSQL.`, { cause: error });
    }
    throw new Error("KOMP API is unavailable. Start the FastAPI backend at http://127.0.0.1:8000 and refresh.", { cause: error });
  } finally {
    window.clearTimeout(timeout);
  }

  if (!response.ok) {
    if (response.status >= 500) throw new Error(SERVER_UNAVAILABLE_MESSAGE);

    let message = `${response.status} ${response.statusText}`;
    try {
      const body: unknown = await response.json();
      if (body && typeof body === "object") {
        const payload = body as { detail?: unknown; message?: string };
        const detail = payload.detail;
        message = Array.isArray(detail)
          ? detail.map((item) => typeof item === "object" && item && "msg" in item ? String((item as {msg: unknown}).msg) : JSON.stringify(item)).join(", ")
          : typeof detail === "string" ? detail : payload.message ?? message;
      }
    } catch { /* Keep HTTP status message. */ }
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("application/json")) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiGet = <T,>(path: string, params?: RequestOptions["params"]) =>
  request<T>(path, { method: "GET", params });

export const apiPost = <T,>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body instanceof FormData ? body : JSON.stringify(body ?? {}) });

export const apiDelete = <T,>(path: string) => request<T>(path, { method: "DELETE" });

export async function apiStreamPost<T, E extends { type?: string; result?: T; message?: string }>(
  path: string,
  body: unknown,
  onEvent: (event: E) => void,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new Error("KOMP API is unavailable. Start the FastAPI backend and refresh.");
  }

  if (!response.ok) {
    if (response.status >= 500) throw new Error(SERVER_UNAVAILABLE_MESSAGE);

    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json() as { detail?: unknown; message?: string };
      message = typeof payload.detail === "string" ? payload.detail : payload.message ?? message;
    } catch { /* Keep the HTTP status message. */ }
    throw new Error(message);
  }
  if (!response.body) throw new Error("KOMP returned an empty analysis stream.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: T | undefined;
  const consume = (block: string) => {
    const data = block.split(/\r?\n/)
      .filter(line => line.startsWith("data:"))
      .map(line => line.slice(5).trimStart())
      .join("\n");
    if (!data) return;
    const event = JSON.parse(data) as E;
    onEvent(event);
    if (event.type === "failed") throw new Error(event.message || "Analysis failed.");
    if (event.type === "completed") result = event.result;
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() ?? "";
    blocks.forEach(consume);
    if (done) break;
  }
  if (buffer.trim()) consume(buffer);
  if (result === undefined) throw new Error("The analysis stream ended before KOMP returned results.");
  return result;
}

export default request;
