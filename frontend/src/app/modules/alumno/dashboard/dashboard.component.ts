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
import { ReportesService } from '../../../core/services/reportes.service';
import { PeriodosService } from '../../admin/periodos/periodos.service';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

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
  private reportesService = inject(ReportesService);
  private periodosService = inject(PeriodosService);

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
    const user = this.authService.currentUser();
    const email = user?.email;

    if (email) {
      // 1. Obtener periodo activo para "Mi Semestre"
      this.periodosService.getActivePeriodo().pipe(
        catchError(() => of({ nombre: 'Primavera 2026' } as any))
      ).subscribe({
        next: (activePeriod) => {
          const periodoNombre = activePeriod?.nombre || 'Primavera 2026';
          
          // 2. Obtener alumno por correo
          this.alumnosService.getAlumnos({ search: email, limit: 1 }).subscribe({
            next: (searchRes) => {
              if (searchRes.success && searchRes.data.alumnos.length > 0) {
                const realId = searchRes.data.alumnos[0].id;
                
                // 3. Obtener detalle del alumno
                this.alumnosService.getAlumno(realId).subscribe({
                  next: (res) => {
                    const inscripciones = res.data.inscripciones?.filter(i => i.activo) ?? [];
                    
                    // Calcular carrera dinámica
                    const formationMap: Record<string, string> = {
                      'ITI': 'Ing. Tecnologías de la información',
                      'LCC': 'Lic. en Ciencias de la Computación',
                      'ICC': 'Ing. en Ciencias de la Computación',
                      'IAS': 'Ing. en Área de Software'
                    };
                    const rawFormation = res.data.tipo_formacion;
                    const carreraNombre = (rawFormation && formationMap[rawFormation.toUpperCase()])
                      || rawFormation
                      || 'Ing. Tecnologías de la información';

                    // Calcular semestre de forma dinámica usando la matrícula
                    const matricula = res.data.matricula || '';
                    let calculatedSemester = 1;
                    if (matricula.length >= 4) {
                      const entryYear = parseInt(matricula.substring(0, 4), 10);
                      if (!isNaN(entryYear)) {
                        const currentYear = new Date().getFullYear();
                        const currentMonth = new Date().getMonth(); // 0-indexed (e.g. 4 is May)
                        const isSpring = currentMonth < 6; // Ene-Jun es Primavera
                        
                        calculatedSemester = (currentYear - entryYear) * 2 + (isSpring ? 0 : 1);
                        if (calculatedSemester < 1) calculatedSemester = 1;
                        if (calculatedSemester > 10) calculatedSemester = 10;
                      }
                    }

                    // Actualizar info del semestre
                    this.semesterInfo = [
                      { label: 'Periodo actual', value: periodoNombre, icon: 'pi-calendar', color: '#F59E0B', bg: 'rgba(245,158,11,0.1)' },
                      { label: 'Materias',       value: `${inscripciones.length} materias`,     icon: 'pi-book',     color: '#4338CA', bg: 'rgba(67,56,202,0.1)'  },
                      { label: 'Carrera',        value: carreraNombre, icon: 'pi-building', color: '#06B6D4', bg: 'rgba(6,182,212,0.1)'  },
                      { label: 'Semestre',       value: `${calculatedSemester}° semestre`,    icon: 'pi-users',    color: '#22C55E', bg: 'rgba(34,197,94,0.1)'  },
                    ];

                    if (inscripciones.length === 0) {
                      this.metricCards[0].value = '0';
                      this.metricCards[1].value = '—';
                      this.metricCards[2].value = '—';
                      this.metricCards[3].value = '0';
                      this.radarData = { labels: [], datasets: [{ ...this.radarData.datasets[0], data: [] }] };
                      this.loading.set(false);
                      return;
                    }

                    // 4. Consultar estadísticas de materias en paralelo
                    const requests = inscripciones.map(insc => 
                      this.reportesService.obtenerEstadisticasAlumno(realId, insc.materia_id).pipe(
                        catchError(() => of(null))
                      )
                    );

                    forkJoin(requests).subscribe({
                      next: (statsList) => {
                        let sumPromedio = 0;
                        let countPromedio = 0;
                        let sumAsistencia = 0;
                        let countAsistencia = 0;
                        let aprobadas = 0;

                        const chartLabels: string[] = [];
                        const chartData: number[] = [];

                        inscripciones.forEach((insc, idx) => {
                          const statsRes = statsList[idx];
                          const label = insc.materia_nombre.substring(0, 15) + (insc.materia_nombre.length > 15 ? '...' : '');
                          chartLabels.push(label);

                          if (statsRes && statsRes.success && statsRes.data) {
                            const stats = statsRes.data;
                            
                            const promRed = (stats.calificaciones_kpi?.promedio_redondeado !== undefined && stats.calificaciones_kpi?.promedio_redondeado !== null)
                              ? stats.calificaciones_kpi.promedio_redondeado
                              : null;

                            chartData.push(promRed !== null ? promRed : 0);

                            if (promRed !== null) {
                              sumPromedio += promRed;
                              countPromedio++;
                              if (promRed >= 6) {
                                aprobadas++;
                              }
                            }

                            const asist = stats.asistencia_kpi?.porcentaje_asistencia;
                            if (asist !== undefined && asist !== null) {
                              sumAsistencia += asist;
                              countAsistencia++;
                            }
                          } else {
                            chartData.push(0);
                          }
                        });

                        const promGeneral = countPromedio > 0 ? (sumPromedio / countPromedio) : null;
                        const promAsistencia = countAsistencia > 0 ? (sumAsistencia / countAsistencia) : null;

                        // Calcular créditos
                        const creditosPrevios = (calculatedSemester - 1) * 32;
                        const creditosActuales = aprobadas * 8;
                        const totalCreditos = creditosPrevios + creditosActuales;

                        // Actualizar metricCards
                        this.metricCards = [
                          {
                            label: 'Materias inscritas',
                            value: String(inscripciones.length),
                            icon: 'pi-book',
                            color: '#F59E0B',
                            badge: 'Activas',
                            badgeBg: 'rgba(245,158,11,0.1)'
                          },
                          {
                            label: 'Promedio general',
                            value: promGeneral !== null ? promGeneral.toFixed(1) : '—',
                            icon: 'pi-star',
                            color: '#22C55E',
                            badge: promGeneral === null ? 'Sin notas' : (promGeneral >= 6.0 ? 'Aprobado' : 'Reprobado'),
                            badgeBg: promGeneral === null ? 'rgba(148,163,184,0.1)' : (promGeneral >= 6.0 ? 'rgba(34,197,94,0.1)' : 'rgba(239,68,68,0.1)')
                          },
                          {
                            label: '% Asistencia',
                            value: promAsistencia !== null ? `${Math.round(promAsistencia)}%` : '—',
                            icon: 'pi-check-circle',
                            color: '#06B6D4',
                            badge: promAsistencia !== null && promAsistencia >= 80 ? 'Excelente' : 'En riesgo',
                            badgeBg: promAsistencia !== null && promAsistencia >= 80 ? 'rgba(6,182,212,0.1)' : 'rgba(239,68,68,0.1)'
                          },
                          {
                            label: 'Créditos cursados',
                            value: String(totalCreditos),
                            icon: 'pi-verified',
                            color: '#4338CA',
                            badge: '/ 240 total',
                            badgeBg: 'rgba(67,56,202,0.1)'
                          }
                        ];

                        // Actualizar gráfico de radar
                        this.radarData = {
                          labels: chartLabels,
                          datasets: [{
                            ...this.radarData.datasets[0],
                            data: chartData
                          }]
                        };

                        this.loading.set(false);
                      },
                      error: () => {
                        this.loading.set(false);
                      }
                    });
                  },
                  error: () => {
                    this.loading.set(false);
                  }
                });
              } else {
                this.loading.set(false);
              }
            },
            error: () => {
              this.loading.set(false);
            }
          });
        },
        error: () => {
          this.loading.set(false);
        }
      });
    } else {
      setTimeout(() => this.loading.set(false), 600);
    }
  }
}
