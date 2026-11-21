"""
Plantilla del correo de aviso a administradores (S3 de pending-request-insight).

Correo transaccional en español, misma convención visual que el correo de
aprobación: HTML tabular con estilos inline + versión texto plano.

El aviso NO autoriza nada por sí mismo: sólo informa que hay solicitudes sin
revisar y enlaza al panel. La decisión sigue siendo del administrador.
"""

from datetime import datetime, timezone
from html import escape
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

BRAND = "RINCOM.ES"
BRAND_URL = "https://www.rincom.es"
LOCAL_TZ = ZoneInfo("Europe/Madrid")
NO_LOCATION = "sin ubicación"
NO_DATE = "sin fecha"


def _brand_link(style: str) -> str:
    """Marca envuelta en un <a> explícito a www (el apex devuelve 526)."""
    return f'<a href="{BRAND_URL}" style="{style}">{BRAND}</a>'


def format_request_date(created_at: Optional[datetime]) -> str:
    """Fecha de la solicitud en es-ES y hora de Madrid; nunca lanza."""
    if created_at is None:
        return NO_DATE
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    try:
        return created_at.astimezone(LOCAL_TZ).strftime("%d/%m/%Y %H:%M")
    except (OverflowError, ValueError):
        return NO_DATE


def format_location(country: Optional[str], city: Optional[str]) -> str:
    """'Ciudad, PAÍS', sólo el país, o 'sin ubicación'. Nunca aproxima."""
    parts = [part for part in (city, country) if part]
    return ", ".join(parts) if parts else NO_LOCATION


def pending_request_subject(count: int) -> str:
    """Asunto que dice cuántas solicitudes hay esperando."""
    if count == 1:
        return "1 solicitud de acceso esperando autorización"
    return f"{count} solicitudes de acceso esperando autorización"


def _user_rows(requests: Sequence) -> list:
    """(nombre, email, origen, fecha, ubicación) por solicitud."""
    rows = []
    for user in requests:
        name = getattr(user, "full_name", None) or getattr(user, "username", "")
        rows.append(
            (
                name or "sin nombre",
                getattr(user, "email", "") or "",
                getattr(user, "origin", None) or "Sistema",
                format_request_date(getattr(user, "created_at", None)),
                format_location(
                    getattr(user, "request_country", None),
                    getattr(user, "request_city", None),
                ),
            )
        )
    return rows


def _cta(dashboard_url: Optional[str]) -> str:
    return dashboard_url or ""


def pending_request_html(requests: Sequence, dashboard_url: Optional[str]) -> str:
    """Cuerpo HTML con una fila por solicitud sin revisar."""
    rows = _user_rows(requests)
    body_rows = "".join(
        f"""
            <tr>
              <td style="padding:12px 0;border-bottom:1px solid #2D3148;">
                <div style="color:#F9FAFB;font-size:15px;font-weight:600;">{escape(name)}</div>
                <div style="color:#9CA3AF;font-size:13px;">{escape(email)}</div>
                <div style="color:#9CA3AF;font-size:12px;margin-top:4px;">
                  {escape(origin)} &middot; {escape(date)} &middot; {escape(location)}
                </div>
              </td>
            </tr>"""
        for name, email, origin, date, location in rows
    )
    url = _cta(dashboard_url)
    button = (
        f"""
      <tr>
        <td style="padding:24px 0 8px;">
          <a href="{escape(url, quote=True)}"
             style="background:#6366F1;color:#FFFFFF;text-decoration:none;padding:12px 20px;
                    border-radius:8px;font-weight:700;font-size:14px;display:inline-block;">
            Revisar en el panel
          </a>
        </td>
      </tr>"""
        if url
        else ""
    )
    total = len(rows)
    intro = (
        "Hay una solicitud de acceso esperando autorización."
        if total == 1
        else f"Hay {total} solicitudes de acceso esperando autorización."
    )
    return f"""<!DOCTYPE html>
<html lang="es">
  <body style="margin:0;padding:0;background:#111318;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#111318;">
      <tr>
        <td align="center" style="padding:32px 16px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
                 style="max-width:560px;background:#1E2130;border:1px solid #2D3148;border-radius:12px;">
            <tr>
              <td style="padding:28px;">
                <div style="color:#6366F1;font-size:12px;font-weight:700;letter-spacing:1px;">
                  {escape(BRAND)} &middot; AUTHCORE
                </div>
                <h1 style="color:#F9FAFB;font-size:20px;margin:12px 0 8px;">
                  Solicitudes pendientes
                </h1>
                <p style="color:#9CA3AF;font-size:14px;margin:0 0 8px;">{escape(intro)}</p>
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                  {body_rows}
                </table>
                {button}
                <p style="color:#6B7280;font-size:12px;margin:24px 0 0;">
                  Aviso automático de {_brand_link("color:#9CA3AF;text-decoration:underline;")}.
                  No responde a este correo.
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""


def pending_request_text(requests: Sequence, dashboard_url: Optional[str]) -> str:
    """Versión texto plano del aviso."""
    rows = _user_rows(requests)
    total = len(rows)
    intro = (
        "Hay una solicitud de acceso esperando autorización."
        if total == 1
        else f"Hay {total} solicitudes de acceso esperando autorización."
    )
    lines = [intro, ""]
    for name, email, origin, date, location in rows:
        lines.append(f"- {name} ({email})")
        lines.append(f"  {origin} · {date} · {location}")
    url = _cta(dashboard_url)
    if url:
        lines.extend(["", f"Revisar en el panel: {url}"])
    lines.extend(["", f"Aviso automático de {BRAND}."])
    return "\n".join(lines)
