import { Routes } from '@angular/router';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./admin-layout.component').then(c => c.AdminLayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/dashboard.component').then(c => c.DashboardComponent)
      },
      {
        path: 'periodos',
        loadComponent: () =>
          import('./periodos/periodos/periodos.component').then(m => m.PeriodosComponent)
      },
      {
        path: 'periodos/:id',
        loadComponent: () =>
          import('./periodos/periodos-detail/periodos-detail.component').then(m => m.PeriodosDetailComponent)
      },
      {
        path: 'materias',
        loadComponent: () =>
          import('./materias/materias.component').then(c => c.MateriasComponent)
      },
      {
        path: 'docentes',
        loadComponent: () =>
          import('./docentes/docentes.component').then(c => c.DocentesComponent)
      },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  }
];
