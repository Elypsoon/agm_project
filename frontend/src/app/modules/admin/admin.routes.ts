import { Routes } from '@angular/router';
import { roleGuard } from '../../core/guards/role.guard';

export const ADMIN_ROUTES: Routes = [
  {
    path: 'periodos',
    loadComponent: () => import('./periodos/periodos.component').then(m => m.PeriodosComponent)
  }
];
