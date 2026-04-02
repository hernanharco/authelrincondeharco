export const prerender = false;

import type { APIRoute } from "astro";
import { apiUrl } from "../../../config/api.config";

export const PATCH: APIRoute = async ({ request, cookies }) => {
  const token = cookies.get("session")?.value;
  if (!token) {
    return new Response(JSON.stringify({ error: "No autorizado" }), { status: 401 });
  }

  try {
    const body = await request.json();
    const { userId, action } = body;

    let url: string;
    let payload: object;

    if (action === "approve" || action === "role") {
      url = apiUrl(`/api/v1/users/${userId}/role`);
      payload = { role: body.role || "USER" };
    } else if (action === "status" || action === "reject") {
      url = apiUrl(`/api/v1/users/${userId}/status`);
      payload = { status: body.status || "SUSPENDED" };
    } else if (action === "lock") {
      url = apiUrl(`/api/v1/users/${userId}/lock`);
      payload = { is_locked: body.is_locked };
    } else {
      return new Response(JSON.stringify({ error: "Acción inválida" }), { status: 400 });
    }

    const res = await fetch(url, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify(payload),
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
