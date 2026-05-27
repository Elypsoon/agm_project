import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AlumnosService, Inscripcion } from '../../../core/services/alumnos.service';
import { AuthService } from '../../../core/services/auth.service';

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
  imports: [CommonModule, CardModule, TagModule, ButtonModule, SkeletonModule, ToastModule],
  providers: [MessageService],
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.scss']
})
export class MateriasComponent implements OnInit {
  private authService = inject(AuthService);
  private alumnosService = inject(AlumnosService);
  private messageService = inject(MessageService);

  loading = signal(true);
  materias = signal<MateriaCard[]>([]);

  private readonly COLORS = ['#F59E0B', '#06B6D4', '#4338CA', '#22C55E', '#8B5CF6'];

  ngOnInit() {
    const userId = this.authService.currentUser()?.id;
    if (userId) {
      this.alumnosService.getAlumno(userId).subscribe({
        next: (res) => {
          const inscripciones = res.data.inscripciones?.filter(i => i.activo) ?? [];
          this.materias.set(this.mapToCards(inscripciones));
          this.loading.set(false);
        },
        error: () => {
          this.materias.set(this.mockMaterias());
          this.loading.set(false);
        }
      });
    } else {
      this.materias.set(this.mockMaterias());
      setTimeout(() => this.loading.set(false), 600);
    }
  }

  private mapToCards(inscripciones: Inscripcion[]): MateriaCard[] {
    return inscripciones.map((insc, i) => ({
      id: insc.id,
      nombre: insc.materia_nombre,
      docente: 'Por asignar',
      horario: 'Consulta con tu docente',
      aula: '—',
      estado: 'activa',
      progreso: 60,
      color: this.COLORS[i % this.COLORS.length]
    }));
  }

  private mockMaterias(): MateriaCard[] {
    return [
      { id: '1', nombre: 'Desarrollo de Sistemas Distribuidos', docente: 'Dra. Alejandra Vega', horario: 'Lun/Mié/Vie 08:00–09:30', aula: 'Lab. 3-A', estado: 'activa', progreso: 65, color: '#F59E0B' },
      { id: '2', nombre: 'Redes de Computadoras',              docente: 'Dr. Pablo Morales',   horario: 'Mar/Jue 10:00–11:30',     aula: 'Aula 2-B', estado: 'activa', progreso: 70, color: '#06B6D4' },
      { id: '3', nombre: 'Ingeniería de Software',             docente: 'M.C. Rosa Espinosa',  horario: 'Lun/Jue 12:00–13:30',    aula: 'Aula 1-A', estado: 'activa', progreso: 55, color: '#4338CA' },
      { id: '4', nombre: 'Base de Datos Avanzadas',            docente: 'Dr. Luis Herrera',    horario: 'Mar/Vie 14:00–15:30',     aula: 'Lab. 1-C', estado: 'activa', progreso: 72, color: '#22C55E' },
      { id: '5', nombre: 'Cálculo Diferencial e Integral',    docente: 'M.C. Carmen Noriega', horario: 'Mié/Vie 07:00–08:30',     aula: 'Aula 3-C', estado: 'activa', progreso: 48, color: '#8B5CF6' },
    ];
  }
}
