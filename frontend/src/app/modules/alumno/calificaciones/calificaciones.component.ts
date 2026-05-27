import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { SkeletonModule } from 'primeng/skeleton';
import { ChartModule } from 'primeng/chart';

interface CalificacionRow {
  materia: string;
  docente: string;
  parcial1: number | null;
  parcial2: number | null;
  parcial3: number | null;
  promedio: number | null;
  estado: 'aprobado' | 'reprobado' | 'en_curso';
}

@Component({
  selector: 'app-alumno-calificaciones',
  standalone: true,
  imports: [CommonModule, TableModule, TagModule, SkeletonModule, ChartModule],
  templateUrl: './calificaciones.component.html',
  styleUrls: ['./calificaciones.component.scss']
})
export class CalificacionesComponent implements OnInit {
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
    setTimeout(() => {
      this.calificaciones.set([
        { materia: 'Desarrollo de Sistemas Distribuidos', docente: 'Dra. Alejandra Vega', parcial1: 9.2, parcial2: 8.8, parcial3: null,  promedio: null,  estado: 'en_curso' },
        { materia: 'Redes de Computadoras',              docente: 'Dr. Pablo Morales',   parcial1: 8.5, parcial2: 7.5, parcial3: null,  promedio: null,  estado: 'en_curso' },
        { materia: 'Ingeniería de Software',             docente: 'M.C. Rosa Espinosa',  parcial1: 8.0, parcial2: 8.5, parcial3: 7.5,  promedio: 8.0,   estado: 'aprobado' },
        { materia: 'Base de Datos Avanzadas',            docente: 'Dr. Luis Herrera',    parcial1: 9.5, parcial2: 9.0, parcial3: 8.5,  promedio: 9.0,   estado: 'aprobado' },
        { materia: 'Cálculo Diferencial e Integral',    docente: 'M.C. Carmen Noriega', parcial1: 5.5, parcial2: 6.0, parcial3: 5.0,  promedio: 5.5,   estado: 'reprobado'},
      ]);
      this.loading.set(false);
    }, 600);
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
