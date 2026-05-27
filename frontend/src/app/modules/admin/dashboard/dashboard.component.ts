import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { SkeletonModule } from 'primeng/skeleton';
import { TagModule } from 'primeng/tag';
import { firstValueFrom } from 'rxjs';

import { PeriodosService } from '../periodos/periodos.service';
import { DocentesService } from '../../../core/services/docentes.service';
import { AlumnosService } from '../../../core/services/alumnos.service';

@Component({
  selector: 'app-admin-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, CardModule, ChartModule, SkeletonModule, TagModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  loading = true;

  metrics: { label: string; value: string; icon: string; color: string; bg: string }[] = [];

  // Donut — Distribución de alumnos por carrera
  donutData: any;
  donutOptions: any;

  // Bar horizontal — Materias por periodo
  barData: any;
  barOptions: any;

  constructor(
    private periodosService: PeriodosService,
    private docentesService: DocentesService,
    private alumnosService: AlumnosService
  ) {}

  ngOnInit() {
    this.loadData();
  }

  async loadData() {
    this.loading = true;
    try {
      // 1. Fetch active period (with 404 catch)
      let activePeriod: any = null;
      try {
        activePeriod = await firstValueFrom(this.periodosService.getActivePeriodo());
      } catch (err) {
        console.warn('No hay periodo activo actualmente.');
      }

      // 2. Fetch all periodos, materias, docentes total, and students
      const [periodos, materias, resDocentes, resAlumnos] = await Promise.all([
        firstValueFrom(this.periodosService.getPeriodos()),
        this.periodosService.getAllMaterias(),
        firstValueFrom(this.docentesService.getDocentes({ limit: 1 })),
        firstValueFrom(this.alumnosService.getAlumnos({ limit: 1000 }))
      ]);

      // Calculate active subjects count
      const activeMateriasCount = activePeriod 
        ? materias.filter(m => m.periodo === activePeriod.id).length
        : 0;

      // Populate Metric Cards
      this.metrics = [
        { 
          label: 'Periodo Activo', 
          value: activePeriod ? activePeriod.nombre : 'Ninguno activo', 
          icon: 'pi-calendar', 
          color: '#4338CA', 
          bg: 'rgba(67,56,202,0.10)' 
        },
        { 
          label: 'Materias Activas', 
          value: String(activeMateriasCount), 
          icon: 'pi-book', 
          color: '#06B6D4', 
          bg: 'rgba(6,182,212,0.10)' 
        },
        { 
          label: 'Docentes Registrados', 
          value: String(resDocentes.data?.total ?? 0), 
          icon: 'pi-users', 
          color: '#F59E0B', 
          bg: 'rgba(245,158,11,0.10)' 
        },
        { 
          label: 'Alumnos Registrados', 
          value: String(resAlumnos.data?.total ?? 0), 
          icon: 'pi-graduation-cap', 
          color: '#22C55E', 
          bg: 'rgba(34,197,94,0.10)' 
        },
      ];

      // Calculate career distribution from students
      const careerCounts: Record<string, number> = {};
      const alumnos = resAlumnos.data?.alumnos || [];
      
      alumnos.forEach(a => {
        const rawCarrera = a.carrera || 'OTRO';
        let careerName = rawCarrera.toUpperCase().trim();
        if (careerName === 'ITI') careerName = 'Ing. Tecnologías de la Inf. (ITI)';
        else if (careerName === 'LCC') careerName = 'Lic. Ciencias de la Comp. (LCC)';
        else if (careerName === 'ICC') careerName = 'Ing. Ciencias de la Comp. (ICC)';
        
        careerCounts[careerName] = (careerCounts[careerName] || 0) + 1;
      });

      const careerLabels = Object.keys(careerCounts);
      const careerValues = Object.values(careerCounts);

      // Donut Chart
      this.donutData = {
        labels: careerLabels.length > 0 ? careerLabels : ['Sin alumnos'],
        datasets: [{
          data: careerValues.length > 0 ? careerValues : [0],
          backgroundColor: ['#4338CA', '#06B6D4', '#F59E0B', '#10B981', '#6366F1', '#EC4899'],
          borderWidth: 0,
          cutout: '70%'
        }]
      };

      this.donutOptions = {
        plugins: {
          legend: {
            position: 'bottom',
            labels: { font: { family: 'Inter', size: 12 }, color: '#64748B', padding: 12 }
          }
        },
        responsive: true,
        maintainAspectRatio: false
      };

      // Bar Chart — materias count per period for the last 3 periods
      const last3Periods = periodos.slice(0, 3);
      const barLabels = last3Periods.map(p => p.nombre);
      const barValues = last3Periods.map(p => {
        return materias.filter(m => m.periodo === p.id).length;
      });

      this.barData = {
        labels: barLabels,
        datasets: [{
          label: 'Materias cargadas',
          data: barValues,
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
            ticks: { font: { family: 'Inter' }, color: '#94A3B8', stepSize: 1 },
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

      this.loading = false;
    } catch (error) {
      console.error('Error loading dashboard metrics:', error);
      this.loading = false;
    }
  }
}
