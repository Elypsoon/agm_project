import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';

/**
 * SECURITY (VULN-07): Guard para la ruta `reset-password/:uid/:token`.
 *
 * Valida que los parámetros requeridos en la URL estén presentes y no vacíos
 * antes de cargar el componente. Sin este guard, un usuario puede navegar
 * directamente a la ruta con parámetros malformados o vacíos, provocando
 * errores no manejados o abriendo superficie para fuerza bruta.
 *
 * Si los parámetros son inválidos, redirige a `/auth/forgot-password`
 * para que el usuario reinicie el flujo de recuperación correctamente.
 */
export const resetPasswordGuard: CanActivateFn = (route) => {
  const router = inject(Router);

  const uid = route.params['uid'];
  const token = route.params['token'];

  // Verificar que ambos parámetros existan y no estén vacíos
  const isValid = !!uid && uid.trim().length > 0
               && !!token && token.trim().length > 0;

  if (!isValid) {
    // Redirigir al inicio del flujo de recuperación con mensaje de contexto
    router.navigate(['/auth/forgot-password'], {
      queryParams: { error: 'invalid_link' }
    });
    return false;
  }

  return true;
};
