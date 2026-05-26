import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { TagModule } from 'primeng/tag';
import { SelectModule } from 'primeng/select';
import { FormsModule } from '@angular/forms';
import { SkeletonModule } from 'primeng/skeleton';

@Component({
  selector: 'app-estadisticas',
  standalone: true,
  imports: [CommonModule, FormsModule, ChartModule, TagModule, SelectModule, SkeletonModule],
  templateUrl: './estadisticas.component.html',
  styleUrls: ['./estadisticas.component.scss']
})
export class EstadisticasComponent implements OnInit {
  selectedPeriodo = 'Primavera 2026';
  readonly periodoOptions = ['Primavera 2026', 'Otoño 2025', 'Primavera 2025', 'Otoño 2024'];

  summaryCards = [
    { label: 'Promedio acumulado', value: '8.4', icon: 'pi-star',        color: '#F59E0B', trend: '+0.3 vs semestre ant.',  trendUp: true  },
    { label: 'Materias cursadas',  value: '22',  icon: 'pi-book',        color: '#4338CA', trend: '+5 este año',            trendUp: true  },
    { label: '% Asistencia global', value: '91%',icon: 'pi-check-circle',color: '#22C55E', trend: '+2% vs otoño 2025',     trendUp: true  },
    { label: 'Créditos totales',   value: '148', icon: 'pi-verified',    color: '#06B6D4', trend: '92 restantes',           trendUp: false },
  ];

  legendItems = [
    { label: 'Aprobadas',    value: '18', color: '#22C55E' },
    { label: 'En curso',     value: '5',  color: '#F59E0B' },
    { label: 'Reprobadas',   value: '1',  color: '#EF4444' },
  ];

  lineData = {
    labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4', 'Sem 5', 'Sem 6 (actual)'],
    datasets: [{
      label: 'Promedio semestral',
      data: [7.8, 8.1, 7.9, 8.5, 8.2, 8.7],
      borderColor: '#F59E0B',
      backgroundColor: 'rgba(245, 158, 11, 0.1)',
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#F59E0B',
      pointRadius: 5,
      pointHoverRadius: 8,
      borderWidth: 2.5,
    }]
  };

  lineOptions = {
    plugins: {
      legend: { display: false },
      tooltip: { backgroundColor: '#1E293B', titleColor: '#F8FAFC', bodyColor: '#94A3B8' }
    },
    scales: {
      x: { ticks: { font: { family: 'Inter', size: 12 }, color: '#94A3B8' }, grid: { display: false } },
      y: { min: 6, max: 10, ticks: { font: { family: 'Inter', size: 12 }, color: '#94A3B8', stepSize: 1 }, grid: { color: '#F1F5F9' } }
    },
    animation: { duration: 700, easing: 'easeInOutQuart' }
  };

  barData = {
    labels: ['Serv. Web', 'Redes', 'Ing. SW', 'Base de Datos', 'Cálculo'],
    datasets: [{
      label: '% Asistencia',
      data: [96, 88, 93, 97, 84],
      backgroundColor: [
        'rgba(34,197,94,0.8)', 'rgba(245,158,11,0.8)', 'rgba(34,197,94,0.8)',
        'rgba(34,197,94,0.8)', 'rgba(239,68,68,0.8)'
      ],
      borderRadius: 8,
      borderSkipped: false,
    }]
  };

  barOptions = {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { font: { family: 'Inter', size: 11 }, color: '#94A3B8' }, grid: { display: false } },
      y: { min: 60, max: 100, ticks: { font: { family: 'Inter', size: 11 }, color: '#94A3B8' }, grid: { color: '#F1F5F9' } }
    },
    animation: { duration: 600 }
  };

  doughnutData = {
    labels: ['Aprobadas', 'En curso', 'Reprobadas'],
    datasets: [{
      data: [18, 5, 1],
      backgroundColor: ['#22C55E', '#F59E0B', '#EF4444'],
      borderWidth: 0,
      cutout: '68%',
      hoverOffset: 6
    }]
  };

  doughnutOptions = {
    plugins: { legend: { display: false } },
    animation: { duration: 700 }
  };

  ngOnInit() {}
}
