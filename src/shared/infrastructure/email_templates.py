"""
Plantillas de correo transaccional — paleta SANTI (design-system/tecnimotos-santi/MASTER.md).
HTML con estilos inline y layout de tablas (compatibilidad Outlook/Gmail/Apple
Mail) — nunca depende de background-clip:text ni de imágenes remotas, para
que se vea bien incluso con imágenes bloqueadas por defecto.
"""
from __future__ import annotations

TEAL = "#0D9488"
ELECTRIC = "#8B5CF6"
COBALT_DARK = "#0F172A"
SURFACE_MUTED = "#1E293B"
TEXT_MUTED = "#94A3B8"

_FONT_STACK = "'Quicksand', 'Nunito Sans', -apple-system, Segoe UI, Arial, sans-serif"
_FONT_MONO = "'Fira Code', 'Courier New', monospace"


def plantilla_codigo_mfa(codigo: str, minutos_expira: int) -> str:
    """Retorna el HTML completo del correo de verificación MFA (ADR-011)."""
    return f"""\
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Código de verificación Tecnimotos</title>
</head>
<body style="margin:0; padding:0; background-color:#F1F5F9; font-family:{_FONT_STACK};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F1F5F9; padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px; width:100%; background-color:{COBALT_DARK}; border-radius:16px; overflow:hidden;">

          <tr>
            <td style="padding:28px 32px 20px 32px; border-bottom:1px solid #1E293B;">
              <span style="font-size:18px; font-weight:800; letter-spacing:-0.3px; color:{TEAL};">TECNIMOTOS</span>
              <span style="font-size:18px; font-weight:800; letter-spacing:-0.3px; color:{ELECTRIC};"> SANTI</span>
            </td>
          </tr>

          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 4px 0; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:{TEXT_MUTED};">
                Verificación de seguridad
              </p>
              <h1 style="margin:0 0 20px 0; font-size:20px; font-weight:700; color:#F8FAFC;">
                Tu código de acceso
              </h1>

              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  <td align="center" style="background-color:{SURFACE_MUTED}; border:1px solid {TEAL}; border-radius:12px; padding:20px;">
                    <span style="font-family:{_FONT_MONO}; font-size:36px; font-weight:700; letter-spacing:10px; color:{TEAL};">
                      {codigo}
                    </span>
                  </td>
                </tr>
              </table>

              <p style="margin:20px 0 0 0; font-size:13px; color:{TEXT_MUTED}; line-height:1.5;">
                Este código expira en <strong style="color:#CBD5E1;">{minutos_expira} minutos</strong>.
                Ingresa a Tecnimotos con tu correo y contraseña, y cuando te lo pida, escribe este código.
              </p>

              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:24px;">
                <tr>
                  <td style="background-color:rgba(139,92,246,0.08); border:1px solid rgba(139,92,246,0.25); border-radius:10px; padding:14px 16px;">
                    <p style="margin:0; font-size:12px; color:#C4B5FD; line-height:1.5;">
                      Si no fuiste tú quien intentó ingresar, ignora este correo — tu cuenta sigue segura.
                      Nunca compartas este código con nadie, ni siquiera con alguien que diga ser de Tecnimotos.
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding:18px 32px; border-top:1px solid #1E293B;">
              <p style="margin:0; font-size:11px; color:#475569;">
                Tecnimotos Santi — correo automático, no respondas a este mensaje.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
