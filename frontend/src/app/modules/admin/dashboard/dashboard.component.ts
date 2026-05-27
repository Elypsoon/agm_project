import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { SkeletonModule } from 'primeng/skeleton';
import { TagModule } from 'primeng/tag';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, CardModule, ChartModule, SkeletonModule, TagModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  loading = true;

  metrics = [
    { label: 'Periodo Activo',   value: 'Primavera 2026', icon: 'pi-calendar',   color: '#4338CA', bg: 'rgba(67,56,202,0.10)' },
    { label: 'Materias Activas', value: '48',             icon: 'pi-book',       color: '#06B6D4', bg: 'rgba(6,182,212,0.10)' },
    { label: 'Docentes',         value: '32',             icon: 'pi-users',      color: '#F59E0B', bg: 'rgba(245,158,11,0.10)' },
    { label: 'Alumnos Inscritos',value: '840',            icon: 'pi-graduation-cap', color: '#22C55E', bg: 'rgba(34,197,94,0.10)' },
  ];

  // Donut — Distribución de alumnos por carrera
  donutData: any;
  donutOptions: any;

  // Bar horizontal — Materias por periodo
  barData: any;
  barOptions: any;

  ngOnInit() {
    setTimeout(() => {
      this.loading = false;
      this.initCharts();
    }, 600);
  }

  initCharts() {
    this.donutData = {
      labels: ['Ing. Computación', 'Ing. Software', 'Matemáticas', 'Física'],
      datasets: [{
        data: [320, 280, 150, 90],
        backgroundColor: ['#4338CA', '#6366F1', '#06B6D4', '#F59E0B'],
        borderWidth: 0,
        cutout: '70%'
      }]
    };

    this.donutOptions = {
      plugins: {
        legend: {
          position: 'bottom',
          labels: { font: { family: 'Inter', size: 13 }, color: '#64748B', padding: 16 }
        }
      },
      responsive: true,
      maintainAspectRatio: false
    };

    this.barData = {
      labels: ['Otoño 2026', 'Primavera 2026', 'Verano 2025'],
      datasets: [{
        label: 'Materias activas',
        data: [48, 52, 12],
        backgroundColor: ['#4338CA', '#6366F1', '#A5B4FC'],
        borderRadius: 6,
        borderSkipped: false
      }]
    };

    this.barOptions = {
      indexAxis: 'y',
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: { font: { family: 'Inter' }, color: '#94A3B8' },
          grid: { color: '#E2E8F0' }
        },
        y: {
          ticks: { font: { family: 'Inter', weight: '500' }, color: '#475569' },
          grid: { display: false }
        }
      },
      responsive: true,
      maintainAspectRatio: false
    };
  }
}
