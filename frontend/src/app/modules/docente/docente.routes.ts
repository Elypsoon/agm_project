import { Routes } from '@angular/router';

export const DOCENTE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./docente-layout.component').then(m => m.DocenteLayoutComponent),
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
        path: 'asistencia-qr',
        loadComponent: () =>
          import('./asistencia-qr/asistencia-qr.component').then(m => m.AsistenciaQrComponent)
      },
      {
        path: 'historial',
        loadComponent: () =>
          import('./historial/historial.component').then(m => m.HistorialComponent)
      },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  }
];
