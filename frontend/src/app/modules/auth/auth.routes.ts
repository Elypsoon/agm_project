import { Routes } from '@angular/router';
import { resetPasswordGuard } from '../../core/guards/reset-password.guard';
import { changePasswordGuard } from '../../core/guards/change-password.guard';

export const AUTH_ROUTES: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'change-password',
    // SECURITY (VULN-06): Solo accesible si el usuario está autenticado Y tiene requires_password_change=true.
    // Sin este guard, cualquier usuario puede navegar directamente a esta URL.
    canActivate: [changePasswordGuard],
    loadComponent: () => import('./change-password/change-password.component').then(m => m.ChangePasswordComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
  },
  {
    path: 'reset-password/:uid/:token',
    // SECURITY (VULN-07): Guard valida que uid y token estén presentes antes de cargar el componente.
    canActivate: [resetPasswordGuard],
    loadComponent: () => import('./reset-password/reset-password.component').then(m => m.ResetPasswordComponent)
  },
  { path: '', redirectTo: 'login', pathMatch: 'full' }
];
