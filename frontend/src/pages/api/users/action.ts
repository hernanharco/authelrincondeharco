export const prerender = false;

import type { APIRoute } from "astro";
import { apiUrl } from "../../../config/api.config";

export const PATCH: APIRoute = async ({ request, cookies, params }) => {
  const token = cookies.get("session")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "No autorizado" }), { status: 401 });
  }

  try {
    const { userId, action } = await request.json();

    let url: string;
    let body: object;

    if (action === "approve") {
      url = apiUrl(`/api/v1/users/${userId}/role`);
      body = { role: "USER" };
    } else {
      url = apiUrl(`/api/v1/users/${userId}/status`);
      body = { status: "SUSPENDED" };
    }

    const res = await fetch(url, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return new Response(JSON.stringify(data), {
      status: res.status,
      headers: { "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: "Error interno" }), { status: 500 });
  }
};
