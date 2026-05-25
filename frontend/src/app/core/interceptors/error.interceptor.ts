import { type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err) => {
      if ([401, 403].includes(err.status)) {
        authService.logout();
        router.navigate(['/auth/login']);
      }
      const message = err.error?.message || err.error?.error || err.statusText || 'Error desconocido';
      return throwError(() => new Error(message));
    })
  );
};
