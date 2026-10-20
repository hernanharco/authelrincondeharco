"""
Plantilla del correo de aprobación de acceso.

Correo transaccional en español (audiencia final hispanohablante, misma
convención que la UI). HTML tabular con estilos inline para compatibilidad
con clientes de correo + versión texto plano. El CTA lleva al usuario a
la aplicación que solicitó (tenant.website_url, con fallback al login).
"""
from html import escape

BRAND = "RINCOM.ES"


def approval_subject(app_name: str) -> str:
    """Asunto profesional que nombra la aplicación aprobada."""
    return f"Tu acceso a {app_name} ha sido aprobado"


def approval_html(full_name: str, app_name: str, cta_url: str) -> str:
    """Cuerpo HTML con saludo personalizado y botón 'Ingresar a la aplicación'."""
    name = escape(full_name)
    app = escape(app_name)
    url = escape(cta_url, quote=True)
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background-color:#F1F5F9;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F1F5F9;padding:32px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background-color:#FFFFFF;border-radius:12px;border:1px solid #E2E8F0;">
          <tr>
            <td style="background-color:#0F172A;padding:24px 32px;">
              <span style="font-size:20px;font-weight:bold;color:#FFFFFF;">{BRAND}</span>
              <span style="font-size:12px;color:#94A3B8;display:block;margin-top:4px;">Gestión de accesos</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <h1 style="margin:0 0 16px;font-size:24px;line-height:32px;color:#0F172A;">&iexcl;Hola, {name}!</h1>
              <p style="margin:0 0 16px;font-size:16px;line-height:24px;color:#334155;">
                Tu cuenta ha sido <strong>aprobada</strong>. Ya tienes acceso a
                <strong>{app}</strong>: puedes ingresar a la aplicación y conocerla.
              </p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:24px 0;">
                <tr>
                  <td style="background-color:#10B981;border-radius:8px;">
                    <a href="{url}" style="display:inline-block;padding:14px 28px;font-size:16px;font-weight:bold;color:#FFFFFF;text-decoration:none;">Ingresar a la aplicación</a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 4px;font-size:14px;line-height:20px;color:#64748B;">
                Si el botón no funciona, copia y pega este enlace en tu navegador:
              </p>
              <p style="margin:0;font-size:14px;line-height:20px;color:#2563EB;word-break:break-all;">{url}</p>
            </td>
          </tr>
          <tr>
            <td style="background-color:#F8FAFC;padding:20px 32px;border-top:1px solid #E2E8F0;">
              <p style="margin:0;font-size:12px;line-height:18px;color:#94A3B8;">
                Este mensaje es automático; no respondas a este correo.<br>
                {BRAND} &mdash; Enviado porque tu acceso fue aprobado por un administrador.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def approval_text(full_name: str, app_name: str, cta_url: str) -> str:
    """Versión texto plano para clientes sin soporte HTML."""
    return (
        f"¡Hola, {full_name}!\n\n"
        f"Tu cuenta ha sido aprobada. Ya tienes acceso a {app_name}: "
        "puedes ingresar a la aplicación y conocerla.\n\n"
        f"Ingresar a la aplicación: {cta_url}\n\n"
        f"—\n{BRAND} — Enviado porque tu acceso fue aprobado por un administrador.\n"
    )
