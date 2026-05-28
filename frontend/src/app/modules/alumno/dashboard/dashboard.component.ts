import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { ChartModule } from 'primeng/chart';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { AuthService } from '../../../core/services/auth.service';
import { AlumnosService } from '../../../core/services/alumnos.service';
import { ReportesService } from '../../../core/services/reportes.service';
import { CalificacionesService } from '../../../core/services/calificaciones.service';
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
  private calificacionesService = inject(CalificacionesService);
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

  /** Actividades pendientes (sin calificación) del alumno. */
  activities: { title: string; meta: string; type: string; severity: any; color: string }[] = [];

  /** Número de materias en el radar — controla el tipo de gráfico. */
  subjectCount = signal(5);

  /** Usa radar para ≥3 materias, bar horizontal para 1 o 2. */
  readonly chartType = computed(() => this.subjectCount() >= 3 ? 'radar' : 'bar');

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

  barData = {
    labels: ['Servicios Web', 'Redes'],
    datasets: [{
      label: 'Nota Final',
      data: [9.2, 8.5],
      backgroundColor: 'rgba(245, 158, 11, 0.7)',
      borderColor: '#F59E0B',
      borderWidth: 2,
      borderRadius: 8,
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

  barOptions = {
    indexAxis: 'y' as const,
    plugins: {
      legend: { display: false }
    },
    scales: {
      x: {
        min: 0, max: 10,
        ticks: { stepSize: 2, font: { family: 'Inter', size: 11 }, color: '#94A3B8' },
        grid: { color: '#E2E8F0' }
      },
      y: {
        ticks: { font: { family: 'Inter', size: 12 }, color: '#475569' }
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

                    // 4. Consultar estadísticas KPI y desglose de actividades en paralelo
                    const requests = inscripciones.map(insc =>
                      this.reportesService.obtenerEstadisticasAlumno(realId, insc.materia_id).pipe(
                        catchError(() => of(null))
                      )
                    );

                    const desgloseRequests = inscripciones.map(insc =>
                      this.calificacionesService.getEstadisticasAlumno(realId, insc.materia_id).pipe(
                        catchError(() => of(null))
                      )
                    );

                    forkJoin([forkJoin(requests), forkJoin(desgloseRequests)]).subscribe({
                      next: ([statsList, desgloseList]) => {
                        let sumPromedio = 0;
                        let countPromedio = 0;
                        let sumAsistencia = 0;
                        let countAsistencia = 0;
                        let aprobadas = 0;

                        const chartLabels: string[] = [];
                        const chartData: number[] = [];

                        inscripciones.forEach((insc, idx) => {
                          const statsRes = statsList[idx];
                          // Use the real subject name; fallback only if truly absent
                          const rawName = insc.materia_nombre || '';
                          const label = rawName.length > 20
                            ? rawName.substring(0, 18) + '…'
                            : rawName || 'Sin nombre';
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

                        // Calcular créditos — solo los de materias aprobadas del semestre actual
                        // Los semestres anteriores no se conocen con certeza, así que solo
                        // estimamos por el semestre calculado menos los créditos del semestre actual.
                        // Cap estricto en 240.
                        const CREDITOS_POR_SEMESTRE = 32;
                        const CREDITOS_POR_MATERIA  = 8;
                        const creditosPrevios = Math.min((calculatedSemester - 1) * CREDITOS_POR_SEMESTRE, 240);
                        const creditosActuales = aprobadas * CREDITOS_POR_MATERIA;
                        const totalCreditos = Math.min(creditosPrevios + creditosActuales, 240);

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

                        // Actualizar señal de conteo para elegir tipo de gráfico
                        this.subjectCount.set(chartLabels.length);

                        // Dataset compartido
                        const sharedDataset = {
                          label: 'Nota Final',
                          data: chartData,
                          fill: true,
                          backgroundColor: 'rgba(245, 158, 11, 0.15)',
                          borderColor: '#F59E0B',
                          pointBackgroundColor: '#F59E0B',
                          pointHoverBackgroundColor: '#fff',
                          pointHoverBorderColor: '#F59E0B',
                          borderWidth: 2,
                          borderRadius: 8,
                        };

                        // Actualizar gráfico de radar (≥3 materias)
                        this.radarData = {
                          labels: chartLabels,
                          datasets: [sharedDataset]
                        };

                        // Actualizar gráfico de barras (1-2 materias)
                        this.barData = {
                          labels: chartLabels,
                          datasets: [{
                            ...sharedDataset,
                            backgroundColor: 'rgba(245, 158, 11, 0.7)',
                          }]
                        };

                        // ── Actividades pendientes (sin calificación) ─────────────────
                        const CATEGORY_COLORS: Record<string, { severity: any; color: string }> = {
                          'examen':   { severity: 'danger',  color: '#EF4444' },
                          'tarea':    { severity: 'warn',    color: '#F59E0B' },
                          'quiz':     { severity: 'info',    color: '#06B6D4' },
                          'proyecto': { severity: 'success', color: '#22C55E' },
                        };
                        const DEFAULT_ACT_STYLE = { severity: 'secondary' as any, color: '#94A3B8' };
                        const pendingActivities: { title: string; meta: string; type: string; severity: any; color: string }[] = [];

                        desgloseList.forEach((desgloseRes: any, idx: number) => {
                          const materiaName = inscripciones[idx]?.materia_nombre || 'Materia';
                          if (!desgloseRes || !desgloseRes.desglose) return;
                          desgloseRes.desglose.forEach((cat: any) => {
                            const catKey = cat.ponderacion?.toLowerCase() || '';
                            const style = Object.entries(CATEGORY_COLORS)
                              .find(([key]) => catKey.includes(key))?.[1] ?? DEFAULT_ACT_STYLE;
                            (cat.calificaciones || []).forEach((cal: any) => {
                              if (cal.valor === null || cal.valor === undefined) {
                                pendingActivities.push({
                                  title: `${cal.actividad} — ${materiaName}`,
                                  meta: cat.ponderacion,
                                  type: cat.ponderacion,
                                  severity: style.severity,
                                  color: style.color,
                                });
                              }
                            });
                          });
                        });
                        // Limitar a 8 items para no desbordar el dashboard
                        this.activities = pendingActivities.slice(0, 8);

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
