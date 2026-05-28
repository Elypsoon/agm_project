import { type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, switchMap, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err) => {
      if (err.status === 401) {
        // Intentar renovar el token automáticamente
        return authService.refreshToken().pipe(
          switchMap(() => {
            // Reintentar la petición original con el nuevo token
            const newToken = authService.getToken();
            const retryReq = req.clone({
              setHeaders: { Authorization: `Bearer ${newToken}` }
            });
            return next(retryReq);
          }),
          catchError(() => {
            // Si el refresh también falla, cerrar sesión
            authService.logout();
            router.navigate(['/auth/login']);
            return throwError(() => new Error('Sesión expirada'));
          })
        );
      }

      const message = err.error?.message || err.error?.detail || err.error?.error || err.statusText || 'Error desconocido';
      return throwError(() => new Error(message));
    })
  );
};
