import { HttpErrorResponse } from '@angular/common/http';

/**
 * Extrae y traduce los mensajes de error del backend a textos amigables.
 * Evita que el usuario vea mensajes técnicos como "Http failure response 401".
 */
export function extractErrorMessage(err: HttpErrorResponse | any, defaultMessage: string = 'Ocurrió un error inesperado.'): string {
  if (err instanceof HttpErrorResponse) {
    // 1. Intentar extraer mensajes estructurados del JSON del backend
    if (err.error) {
      if (typeof err.error === 'string') return err.error;
      
      // Errores de Django / DRF
      if (err.error.detail) {
        // Traducciones comunes de SimpleJWT o DRF
        const detailStr = String(err.error.detail).toLowerCase();
        if (detailStr.includes('no active account found')) {
          return 'Correo electrónico o contraseña incorrectos.';
        }
        if (detailStr.includes('given token not valid')) {
          return 'Tu sesión ha expirado. Por favor, inicia sesión de nuevo.';
        }
        return err.error.detail;
      }
      
      if (err.error.error) return err.error.error;
      if (err.error.message) return err.error.message;

      // Errores de validación de campos (ej. {"email": ["Este campo es requerido."]})
      if (typeof err.error === 'object') {
        const firstKey = Object.keys(err.error)[0];
        if (firstKey && Array.isArray(err.error[firstKey])) {
          const keyName = firstKey.charAt(0).toUpperCase() + firstKey.slice(1);
          return `${keyName}: ${err.error[firstKey][0]}`;
        }
      }
    }

    // 2. Si no hay body estructurado, mapear códigos HTTP generales a mensajes amigables
    switch (err.status) {
      case 400: return 'Los datos enviados son incorrectos o están incompletos.';
      case 401: return 'Correo electrónico o contraseña incorrectos.';
      case 403: return 'No tienes permiso para realizar esta acción.';
      case 404: return 'No se encontró la información solicitada.';
      case 500: return 'Error interno del servidor. Inténtalo más tarde.';
      case 0: return 'No hay conexión con el servidor. Verifica tu internet.';
    }
  }

  return defaultMessage;
}
