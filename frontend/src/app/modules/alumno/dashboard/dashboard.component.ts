import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { AuthService } from '../../../core/services/auth.service';
import { AlumnosService, AlumnoDetalle } from '../../../core/services/alumnos.service';

@Component({
  selector: 'app-alumno-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, CardModule, ChartModule, TagModule, ButtonModule, SkeletonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private alumnosService = inject(AlumnosService);

  loading = signal(true);

  readonly firstName = computed(() => {
    const nombre = this.authService.currentUser()?.nombre ?? 'Alumno';
    return nombre.split(' ')[0];
  });

  readonly todayLabel = new Date().toLocaleDateString('es-MX', {
    weekday: 'long', day: 'numeric', month: 'long'
  });

  metricCards = [
    { label: 'Materias inscritas', value: '5',    icon: 'pi-book',      color: '#F59E0B', badge: 'Activas',   badgeBg: 'rgba(245,158,11,0.1)' },
    { label: 'Promedio general',   value: '8.7',  icon: 'pi-star',      color: '#22C55E', badge: 'Aprobado',  badgeBg: 'rgba(34,197,94,0.1)'  },
    { label: '% Asistencia',       value: '93%',  icon: 'pi-check-circle', color: '#06B6D4', badge: 'Excelente', badgeBg: 'rgba(6,182,212,0.1)' },
    { label: 'Créditos cursados',  value: '148',  icon: 'pi-verified',  color: '#4338CA', badge: '/ 240 total',badgeBg: 'rgba(67,56,202,0.1)'  },
  ];

  semesterInfo = [
    { label: 'Periodo actual', value: 'Primavera 2026', icon: 'pi-calendar', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' },
    { label: 'Materias',       value: '5 materias',     icon: 'pi-book',     color: '#4338CA', bg: 'rgba(67,56,202,0.1)'  },
    { label: 'Carrera',        value: 'Ing. en Software',icon: 'pi-building', color: '#06B6D4', bg: 'rgba(6,182,212,0.1)'  },
    { label: 'Semestre',       value: '6° semestre',    icon: 'pi-users',    color: '#22C55E', bg: 'rgba(34,197,94,0.1)'  },
  ];

  activities = [
    { title: 'Examen — Redes de Computadoras',    meta: 'Jue 29 May, 10:00–12:00',   type: 'Examen',  severity: 'danger'    as any, color: '#EF4444' },
    { title: 'Entrega proyecto — Servicios Web',  meta: 'Vie 30 May, 23:59',          type: 'Tarea',   severity: 'warn'      as any, color: '#F59E0B' },
    { title: 'Clase — Base de Datos',             meta: 'Lun 2 Jun, 13:00–14:30',     type: 'Clase',   severity: 'info'      as any, color: '#06B6D4' },
    { title: 'Revisión de calificaciones',        meta: 'Mié 4 Jun, 09:00',           type: 'Admin',   severity: 'secondary' as any, color: '#94A3B8' },
  ];

  radarData = {
    labels: ['Servicios Web', 'Redes', 'Ing. Software', 'Base de Datos', 'Cálculo'],
    datasets: [{
      label: 'Mi rendimiento',
      data: [9.2, 8.5, 7.8, 9.0, 8.7],
      fill: true,
      backgroundColor: 'rgba(245, 158, 11, 0.15)',
      borderColor: '#F59E0B',
      pointBackgroundColor: '#F59E0B',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: '#F59E0B',
      borderWidth: 2,
    }]
  };

  radarOptions = {
    plugins: {
      legend: { display: false }
    },
    scales: {
      r: {
        min: 0, max: 10,
        ticks: { stepSize: 2, font: { family: 'Inter', size: 11 }, color: '#94A3B8' },
        grid: { color: '#E2E8F0' },
        pointLabels: { font: { family: 'Inter', size: 12 }, color: '#475569' }
      }
    },
    animation: { duration: 700 }
  };

  ngOnInit() {
    const userId = this.authService.currentUser()?.id;
    if (userId) {
      this.alumnosService.getAlumno(userId).subscribe({
        next: (res) => {
          // Actualizar métricas con datos reales
          const inscripciones = res.data.inscripciones?.filter(i => i.activo) ?? [];
          this.metricCards[0].value = String(inscripciones.length);
          this.loading.set(false);
        },
        error: () => {
          // Falla silenciosa: usar datos mock
          this.loading.set(false);
        }
      });
    } else {
      setTimeout(() => this.loading.set(false), 600);
    }
  }
}
