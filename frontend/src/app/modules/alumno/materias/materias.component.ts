import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AlumnosService, Inscripcion } from '../../../core/services/alumnos.service';
import { AuthService } from '../../../core/services/auth.service';
import { PeriodosService, Materia } from '../../admin/periodos/periodos.service';

interface MateriaCard {
  id: string;
  nombre: string;
  docente: string;
  horario: string;
  aula: string;
  estado: 'activa' | 'cerrada';
  progreso: number;
  color: string;
}

@Component({
  selector: 'app-alumno-materias',
  standalone: true,
  imports: [CommonModule, CardModule, TagModule, ButtonModule, SkeletonModule, ToastModule, RouterLink],
  providers: [MessageService],
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.scss']
})
export class MateriasComponent implements OnInit {
  private authService = inject(AuthService);
  private alumnosService = inject(AlumnosService);
  private periodosService = inject(PeriodosService);
  private messageService = inject(MessageService);

  loading = signal(true);
  materias = signal<MateriaCard[]>([]);

  private readonly COLORS = ['#F59E0B', '#06B6D4', '#4338CA', '#22C55E', '#8B5CF6'];

  ngOnInit() {
    const user = this.authService.currentUser();
    const email = user?.email;
    
    if (email) {
      this.alumnosService.getAlumnos({ search: email, limit: 1 }).subscribe({
        next: (searchRes) => {
          if (searchRes.success && searchRes.data.alumnos.length > 0) {
            const realId = searchRes.data.alumnos[0].id;
            this.alumnosService.getAlumno(realId).subscribe({
              next: (res) => {
                const inscripciones = res.data.inscripciones?.filter(i => i.activo) ?? [];
                
                // Consultar todas las materias en MS-2 para rellenar detalles (docente, horarios)
                this.periodosService.getMaterias(1, 300).subscribe({
                  next: (periodosRes) => {
                    const listMaterias: Materia[] = periodosRes.results || periodosRes || [];
                    this.materias.set(this.mapToCards(inscripciones, listMaterias));
                    this.loading.set(false);
                  },
                  error: () => {
                    this.materias.set(this.mapToCards(inscripciones, []));
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
    } else {
      this.loading.set(false);
    }
  }

  private mapToCards(inscripciones: Inscripcion[], allMaterias: Materia[]): MateriaCard[] {
    return inscripciones.map((insc, i) => {
      const match = allMaterias.find(m => m.id === insc.materia_id);
      return {
        id: insc.materia_id || insc.id,
        nombre: insc.materia_nombre,
        docente: match?.docente_nombre || 'Por asignar',
        horario: match ? this.formatHorarios(match.horarios) : 'Consulta con tu docente',
        aula: match?.horarios && match.horarios.length > 0 ? match.horarios[0].salon : '—',
        estado: match?.estado === 'abierta' ? 'activa' : (match?.estado === 'cerrada' ? 'cerrada' : 'activa'),
        progreso: 100, // Progreso del curso o avance escolar
        color: this.COLORS[i % this.COLORS.length]
      };
    });
  }

  formatHorarios(horarios: any[] | undefined): string {
    if (!horarios || horarios.length === 0) {
      return 'POR ASIGNAR';
    }
    const rangeMap = new Map<string, string[]>();
    horarios.forEach(h => {
      if (!h.hora_inicio || !h.hora_fin) return;
      const start = this.formatTime(h.hora_inicio);
      const end = this.formatTime(h.hora_fin);
      const timeRange = `${start}-${end}${h.es_virtual ? ' (V)' : ''}`;
      
      if (!rangeMap.has(timeRange)) {
        rangeMap.set(timeRange, []);
      }
      rangeMap.get(timeRange)!.push(this.formatDay(h.dia));
    });
    
    if (rangeMap.size === 0) {
      return 'POR ASIGNAR';
    }
    const parts: string[] = [];
    rangeMap.forEach((days, timeRange) => {
      parts.push(`${days.join(', ')} ${timeRange}`);
    });
    return parts.join(' | ');
  }

  formatTime(raw: string): string {
    if (!raw || raw.length < 4) return raw;
    return `${raw.substring(0, 2)}:${raw.substring(2, 4)}`;
  }

  formatDay(dia: string): string {
    const days: Record<string, string> = {
      'L': 'Lun', 'A': 'Mar', 'M': 'Mié', 'J': 'Jue', 'V': 'Vie', 'S': 'Sáb'
    };
    return days[dia.toUpperCase()] || dia;
  }
}
