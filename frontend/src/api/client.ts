const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1").replace(/\/$/, "");

type RequestOptions = RequestInit & { params?: Record<string, string | number | undefined> };

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...init } = options;
  const url = new URL(`${API_BASE_URL}${path}`, window.location.origin);
  Object.entries(params ?? {}).forEach(([key, value]) => {
    if (value !== undefined && value !== "") url.searchParams.set(key, String(value));
  });

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      ...init,
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...headers,
      },
    });
  } catch {
    throw new Error("KOMP API is unavailable. Start the FastAPI backend at http://127.0.0.1:8000 and refresh.");
  }

  if (!response.ok) {
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

export default request;
