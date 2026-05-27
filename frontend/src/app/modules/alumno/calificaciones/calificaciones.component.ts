import { Component, OnInit, signal, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { SkeletonModule } from 'primeng/skeleton';
import { ChartModule } from 'primeng/chart';
import { AuthService } from '../../../core/services/auth.service';
import { AlumnosService } from '../../../core/services/alumnos.service';
import { CalificacionesService } from '../../../core/services/calificaciones.service';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';

interface CalificacionRow {
  materia: string;
  docente: string;
  parcial1: number | null;
  parcial2: number | null;
  parcial3: number | null;
  promedio: number | null;
  estado: 'aprobado' | 'reprobado' | 'en_curso';
  desglose: any[];
}

@Component({
  selector: 'app-alumno-calificaciones',
  standalone: true,
  imports: [CommonModule, TableModule, TagModule, SkeletonModule, ChartModule],
  templateUrl: './calificaciones.component.html',
  styleUrls: ['./calificaciones.component.scss']
})
export class CalificacionesComponent implements OnInit {
  private authService = inject(AuthService);
  private alumnosService = inject(AlumnosService);
  private calificacionesService = inject(CalificacionesService);

  loading = signal(true);
  calificaciones = signal<CalificacionRow[]>([]);

  readonly aprobadas  = () => this.calificaciones().filter(r => r.estado === 'aprobado').length;
  readonly reprobadas = () => this.calificaciones().filter(r => r.estado === 'reprobado').length;
  readonly enCurso    = () => this.calificaciones().filter(r => r.estado === 'en_curso').length;

  readonly promedioGeneral = () => {
    const vals = this.calificaciones().map(r => r.promedio).filter(v => v !== null) as number[];
    if (vals.length === 0) return '—';
    return (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
  };

  barOptions = {
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { font: { family: 'Inter', size: 11 }, color: '#94A3B8' }, grid: { display: false } },
      y: { min: 0, max: 10, ticks: { font: { family: 'Inter', size: 11 }, color: '#94A3B8' }, grid: { color: '#F1F5F9' } }
    },
    animation: { duration: 600 }
  };

  readonly barData = () => ({
    labels: this.calificaciones().map(r => r.materia.split(' ').slice(0, 2).join(' ')),
    datasets: [{
      label: 'Promedio',
      data: this.calificaciones().map(r => r.promedio),
      backgroundColor: this.calificaciones().map(r =>
        r.promedio === null ? '#E2E8F0' :
        r.promedio >= 8 ? 'rgba(34,197,94,0.8)' :
        r.promedio >= 6 ? 'rgba(245,158,11,0.8)' : 'rgba(239,68,68,0.8)'
      ),
      borderRadius: 8,
      borderSkipped: false
    }]
  });

  ngOnInit() {
    const userId = this.authService.currentUser()?.id;
    if (userId) {
      this.alumnosService.getAlumno(userId).subscribe({
        next: (alumnoRes) => {
          const activeInscripciones = alumnoRes.data.inscripciones?.filter(i => i.activo) ?? [];
          
          if (activeInscripciones.length === 0) {
            this.calificaciones.set([]);
            this.loading.set(false);
            return;
          }

          // Fetch statistics for each enrolled course in parallel using forkJoin
          const requests = activeInscripciones.map(insc => 
            this.calificacionesService.getEstadisticasAlumno(userId, insc.materia_id).pipe(
              catchError((error) => {
                // Return an empty model on 404/other error to stay fully resilient
                return of({
                  materia_id: insc.materia_id,
                  promedio_real: null,
                  promedio_redondeado: null,
                  desglose: []
                });
              })
            )
          );

          forkJoin(requests).subscribe({
            next: (statsList) => {
              const rows: CalificacionRow[] = activeInscripciones.map((insc, idx) => {
                const stats = statsList[idx];
                const desglose = stats?.desglose ?? [];
                
                const mappedGrades = this.mapDesglose(desglose);
                
                // Convert promedio_real from scale 0-100 to scale 0-10
                const promedio = stats?.promedio_real !== null && stats?.promedio_real !== undefined
                  ? stats.promedio_real / 10 
                  : null;
                
                let estado: 'aprobado' | 'reprobado' | 'en_curso' = 'en_curso';
                if (promedio !== null) {
                  estado = promedio >= 6.0 ? 'aprobado' : 'reprobado';
                }

                return {
                  materia: insc.materia_nombre || 'Materia',
                  docente: insc.docente_nombre || 'Por asignar',
                  parcial1: mappedGrades.parcial1,
                  parcial2: mappedGrades.parcial2,
                  parcial3: mappedGrades.parcial3,
                  promedio: promedio,
                  estado: estado,
                  desglose: desglose
                };
              });

              this.calificaciones.set(rows);
              this.loading.set(false);
            },
            error: () => {
              this.loadMockOrEmpty();
            }
          });
        },
        error: () => {
          this.loadMockOrEmpty();
        }
      });
    } else {
      this.loadMockOrEmpty();
    }
  }

  private mapDesglose(desglose: any[]): { parcial1: number | null, parcial2: number | null, parcial3: number | null } {
    let p1: number | null = null;
    let p2: number | null = null;
    let p3: number | null = null;

    const findByName = (nameQuery: string) => {
      return desglose.find(d => {
        const name = d.ponderacion.toLowerCase();
        return name.includes(nameQuery) || name === nameQuery;
      });
    };

    const c1 = findByName('1') || findByName('parcial 1') || findByName('p1');
    const c2 = findByName('2') || findByName('parcial 2') || findByName('p2');
    const c3 = findByName('3') || findByName('parcial 3') || findByName('p3');

    if (c1) p1 = c1.promedio_categoria / 10;
    if (c2) p2 = c2.promedio_categoria / 10;
    if (c3) p3 = c3.promedio_categoria / 10;

    if (p1 === null && desglose[0]) p1 = desglose[0].promedio_categoria / 10;
    if (p2 === null && desglose[1]) p2 = desglose[1].promedio_categoria / 10;
    if (p3 === null && desglose[2]) p3 = desglose[2].promedio_categoria / 10;

    return { parcial1: p1, parcial2: p2, parcial3: p3 };
  }

  private loadMockOrEmpty() {
    this.calificaciones.set([
      { materia: 'Desarrollo de Sistemas Distribuidos', docente: 'Dra. Alejandra Vega', parcial1: 9.2, parcial2: 8.8, parcial3: null,  promedio: null,  estado: 'en_curso', desglose: [{ ponderacion: 'Parcial 1', porcentaje: 30, promedio_categoria: 92, calificaciones: [] }, { ponderacion: 'Parcial 2', porcentaje: 30, promedio_categoria: 88, calificaciones: [] }, { ponderacion: 'Parcial 3', porcentaje: 40, promedio_categoria: 0, calificaciones: [] }] },
      { materia: 'Redes de Computadoras',              docente: 'Dr. Pablo Morales',   parcial1: 8.5, parcial2: 7.5, parcial3: null,  promedio: null,  estado: 'en_curso', desglose: [{ ponderacion: 'Parcial 1', porcentaje: 30, promedio_categoria: 85, calificaciones: [] }, { ponderacion: 'Parcial 2', porcentaje: 30, promedio_categoria: 75, calificaciones: [] }, { ponderacion: 'Parcial 3', porcentaje: 40, promedio_categoria: 0, calificaciones: [] }] },
      { materia: 'Ingeniería de Software',             docente: 'M.C. Rosa Espinosa',  parcial1: 8.0, parcial2: 8.5, parcial3: 7.5,  promedio: 8.0,   estado: 'aprobado', desglose: [{ ponderacion: 'Parcial 1', porcentaje: 30, promedio_categoria: 80, calificaciones: [] }, { ponderacion: 'Parcial 2', porcentaje: 30, promedio_categoria: 85, calificaciones: [] }, { ponderacion: 'Parcial 3', porcentaje: 40, promedio_categoria: 75, calificaciones: [] }] },
      { materia: 'Base de Datos Avanzadas',            docente: 'Dr. Luis Herrera',    parcial1: 9.5, parcial2: 9.0, parcial3: 8.5,  promedio: 9.0,   estado: 'aprobado', desglose: [{ ponderacion: 'Parcial 1', porcentaje: 30, promedio_categoria: 95, calificaciones: [] }, { ponderacion: 'Parcial 2', porcentaje: 30, promedio_categoria: 90, calificaciones: [] }, { ponderacion: 'Parcial 3', porcentaje: 40, promedio_categoria: 85, calificaciones: [] }] },
      { materia: 'Cálculo Diferencial e Integral',    docente: 'M.C. Carmen Noriega', parcial1: 5.5, parcial2: 6.0, parcial3: 5.0,  promedio: 5.5,   estado: 'reprobado', desglose: [{ ponderacion: 'Parcial 1', porcentaje: 30, promedio_categoria: 55, calificaciones: [] }, { ponderacion: 'Parcial 2', porcentaje: 30, promedio_categoria: 60, calificaciones: [] }, { ponderacion: 'Parcial 3', porcentaje: 40, promedio_categoria: 50, calificaciones: [] }] },
    ]);
    this.loading.set(false);
  }

  estadoLabel(estado: string): string {
    const map: Record<string, string> = {
      aprobado: 'Aprobado', reprobado: 'Reprobado', en_curso: 'En curso'
    };
    return map[estado] ?? estado;
  }

  estadoSeverity(estado: string): 'success' | 'danger' | 'info' | 'secondary' {
    const map: Record<string, any> = {
      aprobado: 'success', reprobado: 'danger', en_curso: 'info'
    };
    return map[estado] ?? 'secondary';
  }
}
