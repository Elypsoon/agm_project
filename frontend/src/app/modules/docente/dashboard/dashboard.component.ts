import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { SkeletonModule } from 'primeng/skeleton';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../../../core/services/auth.service';
import { ReportesService, EstadisticasDocenteMateria } from '../../../core/services/reportes.service';

interface MetricCard {
  label: string;
  value: string;
  icon: string;
  color: string;
  trendLabel: string;
  trend: number;
}

@Component({
  selector: 'app-docente-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, CardModule, ChartModule, SkeletonModule, TagModule, ButtonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private reportesService = inject(ReportesService);

  readonly userName = computed(() => this.authService.currentUser()?.nombre ?? 'Docente');

  readonly todayLabel = new Date().toLocaleDateString('es-MX', {
    weekday: 'long', day: 'numeric', month: 'long'
  });

  loading = signal(true);
  hasData = signal(false);

  metricCards: MetricCard[] = [];

  quickActions = [
    { label: 'Mis Materias',  icon: 'pi-book',    route: '/docente/materias',      color: '#06B6D4', bg: 'rgba(6,182,212,0.1)'   },
    { label: 'Calificaciones',icon: 'pi-pencil',  route: '/docente/calificaciones',color: '#4338CA', bg: 'rgba(67,56,202,0.1)'   },
    { label: 'Asistencia QR', icon: 'pi-qrcode',  route: '/docente/asistencia-qr', color: '#22C55E', bg: 'rgba(34,197,94,0.1)'   },
    { label: 'Historial',     icon: 'pi-history', route: '/docente/historial',     color: '#F59E0B', bg: 'rgba(245,158,11,0.1)'  },
  ];

  barData: any = null;
  barOptions = {
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: { ticks: { font: { family: 'Inter', size: 12 }, color: '#94A3B8' }, grid: { display: false } },
      y: { min: 0, max: 100, ticks: { font: { family: 'Inter', size: 12 }, color: '#94A3B8' }, grid: { color: '#F1F5F9' } }
    },
    animation: { duration: 600, easing: 'easeInOutQuart' }
  };

  doughnutData: any = null;
  doughnutOptions = {
    plugins: {
      legend: {
        position: 'bottom',
        labels: { font: { family: 'Inter', size: 12 }, color: '#64748B', padding: 16, usePointStyle: true }
      }
    },
    animation: { duration: 600 }
  };

  ngOnInit() {
    this.cargarEstadisticas();
  }

  cargarEstadisticas() {
    this.loading.set(true);
    const user = this.authService.currentUser();
    if (!user || !user.id) {
      this.loading.set(false);
      this.cargarDefaultEmpty();
      return;
    }

    this.reportesService.obtenerEstadisticasDocente(user.id).subscribe({
      next: (res) => {
        if (res.success && res.data && res.data.length > 0) {
          // Filtrar materias activas
          const materiasActivas = res.data.filter(m => m.periodo_activo);
          const dataset = materiasActivas.length > 0 ? materiasActivas : res.data;

          this.hasData.set(true);
          this.calcularMetricas(dataset);
          this.generarGraficos(dataset);
        } else {
          this.cargarDefaultEmpty();
        }
        this.loading.set(false);
      },
      error: (err) => {
        console.error('Error al cargar estadísticas en dashboard:', err);
        this.cargarDefaultEmpty();
        this.loading.set(false);
      }
    });
  }

  private calcularMetricas(materias: EstadisticasDocenteMateria[]) {
    const totalMaterias = materias.length;
    const totalAlumnos = materias.reduce((sum, m) => sum + m.total_alumnos, 0);
    const avgAsistencia = totalMaterias > 0 
      ? materias.reduce((sum, m) => sum + m.tasa_asistencia, 0) / totalMaterias 
      : 0;
    const avgCalificaciones = totalMaterias > 0 
      ? materias.reduce((sum, m) => sum + m.promedio_grupo, 0) / totalMaterias 
      : 0;

    this.metricCards = [
      { 
        label: 'Materias activas', 
        value: totalMaterias.toString(),    
        icon: 'pi-book',     
        color: '#06B6D4', 
        trend: 0,  
        trendLabel: 'Periodo Activo' 
      },
      { 
        label: 'Alumnos totales', 
        value: totalAlumnos.toString(),    
        icon: 'pi-users',    
        color: '#4338CA', 
        trend: totalAlumnos > 0 ? 1 : 0,  
        trendLabel: 'Inscritos activos' 
      },
      { 
        label: 'Promedio Asistencia',    
        value: `${Math.round(avgAsistencia)}%`,   
        icon: 'pi-check-circle', 
        color: '#22C55E', 
        trend: avgAsistencia >= 80 ? 1 : -1, 
        trendLabel: avgAsistencia >= 80 ? 'Asistencia óptima' : 'Bajo promedio' 
      },
      { 
        label: 'Promedio General',  
        value: (Math.round(avgCalificaciones * 100) / 100).toFixed(2),    
        icon: 'pi-pencil',   
        color: '#F59E0B', 
        trend: avgCalificaciones >= 8.0 ? 1 : 0, 
        trendLabel: 'Escala 0-10' 
      },
    ];
  }

  private generarGraficos(materias: EstadisticasDocenteMateria[]) {
    // 1. Gráfico de Barras: Asistencia por Materia
    this.barData = {
      labels: materias.map(m => m.materia_nombre.substring(0, 15) + (m.materia_nombre.length > 15 ? '...' : '')),
      datasets: [{
        label: '% Asistencia',
        data: materias.map(m => m.tasa_asistencia),
        backgroundColor: 'rgba(6, 182, 212, 0.8)',
        borderColor: '#06B6D4',
        borderRadius: 8,
        borderSkipped: false,
      }]
    };

    // 2. Gráfico de Dona: Distribución de Alumnos
    const colors = ['#06B6D4', '#4338CA', '#F59E0B', '#10B981', '#8B5CF6', '#EC4899'];
    this.doughnutData = {
      labels: materias.map(m => m.materia_nombre),
      datasets: [{
        data: materias.map(m => m.total_alumnos),
        backgroundColor: materias.map((_, i) => colors[i % colors.length]),
        borderWidth: 0,
        cutout: '70%',
        hoverOffset: 8
      }]
    };
  }

  private cargarDefaultEmpty() {
    this.hasData.set(false);
    this.metricCards = [
      { label: 'Materias activas', value: '0', icon: 'pi-book', color: '#64748B', trend: 0, trendLabel: 'Sin materias' },
      { label: 'Alumnos totales', value: '0', icon: 'pi-users', color: '#64748B', trend: 0, trendLabel: 'Sin alumnos' },
      { label: 'Promedio Asistencia', value: '0%', icon: 'pi-check-circle', color: '#64748B', trend: 0, trendLabel: 'Sin registros' },
      { label: 'Promedio General', value: '0.00', icon: 'pi-pencil', color: '#64748B', trend: 0, trendLabel: 'Sin calificaciones' },
    ];

    this.barData = {
      labels: ['Sin datos'],
      datasets: [{
        data: [0],
        backgroundColor: 'rgba(148, 163, 184, 0.2)',
        borderColor: '#94A3B8',
        borderRadius: 8
      }]
    };

    this.doughnutData = {
      labels: ['Sin datos'],
      datasets: [{
        data: [1],
        backgroundColor: ['#E2E8F0'],
        borderWidth: 0,
        cutout: '70%'
      }]
    };
  }
}
