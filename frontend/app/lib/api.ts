"use client";

const API = process.env.NEXT_PUBLIC_API_URL || "";

export const api = {
  get: async (path: string) => {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },
  post: async (path: string, body?: any) => {
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },
  put: async (path: string, body?: any) => {
    const res = await fetch(`${API}${path}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },
  del: async (path: string) => {
    const res = await fetch(`${API}${path}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },
  postForm: async (path: string, params: Record<string, string> = {}) => {
    const qs = new URLSearchParams(params).toString();
    const url = qs ? `${API}${path}?${qs}` : `${API}${path}`;
    const res = await fetch(url, { method: "POST" });
    if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
    return res.json();
  },
};

export const API_URL = API;
