// Constantes de la aplicación
export const APP_CONFIG = {
  API_TIMEOUT: 30000, // 30 segundos
  RETRY_ATTEMPTS: 3,
  TOKEN_REFRESH_THRESHOLD: 5 * 60 * 1000, // 5 minutos antes de expirar
} as const;

export const AUTH_MESSAGES = {
  LOGIN_SUCCESS: 'Inicio de sesión exitoso',
  LOGIN_ERROR: 'Credenciales incorrectas',
  GOOGLE_SUCCESS: 'Conectado con Google con éxito',
  GOOGLE_ERROR: 'Error en autenticación con Google',
  LOGOUT_SUCCESS: 'Sesión cerrada correctamente',
  FORGOT_PASSWORD_SENT: 'Correo de recuperación enviado',
  PASSWORD_RESET_SUCCESS: 'Contraseña restablecida correctamente',
} as const;

export const VALIDATION_RULES = {
  PASSWORD_MIN_LENGTH: 6,
  USERNAME_MIN_LENGTH: 3,
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
} as const;
