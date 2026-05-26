import { Routes } from '@angular/router';

export const ALUMNO_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./alumno-layout.component').then(m => m.AlumnoLayoutComponent),
    children: [
      {
        path: 'dashboard',
        loadComponent: () =>
          import('./dashboard/dashboard.component').then(m => m.DashboardComponent)
      },
      {
        path: 'materias',
        loadComponent: () =>
          import('./materias/materias.component').then(m => m.MateriasComponent)
      },
      {
        path: 'calificaciones',
        loadComponent: () =>
          import('./calificaciones/calificaciones.component').then(m => m.CalificacionesComponent)
      },
      {
        path: 'qr-code',
        loadComponent: () =>
          import('./qr-code/qr-code.component').then(m => m.QrCodeComponent)
      },
      {
        path: 'estadisticas',
        loadComponent: () =>
          import('./estadisticas/estadisticas.component').then(m => m.EstadisticasComponent)
      },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  }
];
