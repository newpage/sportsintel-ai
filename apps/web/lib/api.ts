const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8300/api";

export async function apiFetch(path: string, init: RequestInit = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || "Request failed");
  }

  if (response.status === 204) return null;
  return response.json();
}
