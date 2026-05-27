import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { SkeletonModule } from 'primeng/skeleton';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../../../core/services/auth.service';
import { AlumnosService } from '../../../core/services/alumnos.service';

@Component({
  selector: 'app-docente-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, CardModule, ChartModule, SkeletonModule, TagModule, ButtonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  private authService = inject(AuthService);

  readonly userName = computed(() => this.authService.currentUser()?.nombre ?? 'Docente');

  readonly todayLabel = new Date().toLocaleDateString('es-MX', {
    weekday: 'long', day: 'numeric', month: 'long'
  });

  metricCards = [
    { label: 'Materias activas', value: '3',    icon: 'pi-book',     color: '#06B6D4', trend: 0,  trendLabel: 'Este semestre' },
    { label: 'Alumnos totales', value: '87',    icon: 'pi-users',    color: '#4338CA', trend: 5,  trendLabel: '+5 este mes' },
    { label: '% Asistencia',    value: '91%',   icon: 'pi-check-circle', color: '#22C55E', trend: 3, trendLabel: '+3% vs semana ant.' },
    { label: 'Calificaciones',  value: '68',    icon: 'pi-pencil',   color: '#F59E0B', trend: -2, trendLabel: 'Pendientes' },
  ];

  quickActions = [
    { label: 'Mis Materias',  icon: 'pi-book',    route: '/docente/materias',      color: '#06B6D4', bg: 'rgba(6,182,212,0.1)'   },
    { label: 'Calificaciones',icon: 'pi-pencil',  route: '/docente/calificaciones',color: '#4338CA', bg: 'rgba(67,56,202,0.1)'   },
    { label: 'Asistencia QR', icon: 'pi-qrcode',  route: '/docente/asistencia-qr', color: '#22C55E', bg: 'rgba(34,197,94,0.1)'   },
    { label: 'Historial',     icon: 'pi-history', route: '/docente/historial',     color: '#F59E0B', bg: 'rgba(245,158,11,0.1)'  },
  ];

  barData = {
    labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'],
    datasets: [{
      label: '% Asistencia',
      data: [95, 88, 92, 96, 90],
      backgroundColor: 'rgba(6, 182, 212, 0.8)',
      borderColor: '#06B6D4',
      borderRadius: 8,
      borderSkipped: false,
    }]
  };

  barOptions = {
    plugins: {
      legend: { display: false },
    },
    scales: {
      x: { ticks: { font: { family: 'Inter', size: 12 }, color: '#94A3B8' }, grid: { display: false } },
      y: { min: 60, max: 100, ticks: { font: { family: 'Inter', size: 12 }, color: '#94A3B8' }, grid: { color: '#F1F5F9' } }
    },
    animation: { duration: 600, easing: 'easeInOutQuart' }
  };

  doughnutData = {
    labels: ['Servicios Web', 'Redes', 'Base de Datos'],
    datasets: [{
      data: [32, 28, 27],
      backgroundColor: ['#06B6D4', '#4338CA', '#F59E0B'],
      borderWidth: 0,
      cutout: '70%',
      hoverOffset: 8
    }]
  };

  doughnutOptions = {
    plugins: {
      legend: {
        position: 'bottom',
        labels: { font: { family: 'Inter', size: 12 }, color: '#64748B', padding: 16, usePointStyle: true }
      }
    },
    animation: { duration: 600 }
  };

  ngOnInit() {}
}
