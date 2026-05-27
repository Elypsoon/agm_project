import { Routes } from '@angular/router';
import { roleGuard } from '../../core/guards/role.guard';

export const ADMIN_ROUTES: Routes = [
  {
    path: 'periodos',
    children: [
      {
        path: '',
        loadComponent: () => import('./periodos/periodos.component').then(m => m.PeriodosComponent)
      },
      {
        path: ':id',
        loadComponent: () => import('./periodos/periodos-detail.component').then(m => m.PeriodosDetailComponent)
      }
    ]
  },
  {
    path: 'dashboard',
    redirectTo: 'periodos',
    pathMatch: 'full'
  },
  {
    path: '',
    redirectTo: 'periodos',
    pathMatch: 'full'
  }
];
