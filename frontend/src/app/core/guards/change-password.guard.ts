import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * SECURITY (VULN-06): Guard para la ruta `change-password`.
 *
 * El cambio de contraseña obligatorio es un flujo de un solo uso: solo debe
 * ser accesible cuando el usuario está autenticado Y tiene la bandera
 * `requires_password_change=true` en su perfil.
 *
 * Casos cubiertos:
 * - No autenticado         → redirige a /auth/login
 * - Autenticado, sin flag  → redirige al dashboard correspondiente a su rol
 * - Autenticado, con flag  → permite el acceso (caso legítimo)
 */
export const changePasswordGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  // Caso 1: usuario no autenticado → debe iniciar sesión primero
  if (!authService.isAuthenticated()) {
    router.navigate(['/auth/login']);
    return false;
  }

  const user = authService.currentUser();

  // Caso 2: autenticado pero NO tiene cambio pendiente → enviar a su dashboard
  // Evita que cualquier usuario con token activo acceda a esta pantalla directamente
  if (!user?.requires_password_change) {
    router.navigate([authService.getDashboardRoute()]);
    return false;
  }

  // Caso 3: autenticado Y tiene cambio pendiente → acceso permitido
  return true;
};
