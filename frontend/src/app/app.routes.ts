import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./modules/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },
  {
    path: 'docente',
    loadChildren: () => import('./modules/docente/docente.routes').then(m => m.DOCENTE_ROUTES),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['DOCENTE'] }
  },
  {
    path: 'alumno',
    loadChildren: () => import('./modules/alumno/alumno.routes').then(m => m.ALUMNO_ROUTES),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ALUMNO'] }
  },
  { path: '', redirectTo: '/auth/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/auth/login' }
];
