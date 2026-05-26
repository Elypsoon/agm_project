import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { CardModule } from 'primeng/card';
import { DataViewModule } from 'primeng/dataview';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { SkeletonModule } from 'primeng/skeleton';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AlumnosService } from '../../../core/services/alumnos.service';
import { AuthService } from '../../../core/services/auth.service';

interface MateriaCard {
  id: string;
  nombre: string;
  nrc: string;
  horario: string;
  aula: string;
  totalAlumnos: number;
  color: string;
}

@Component({
  selector: 'app-docente-materias',
  standalone: true,
  imports: [
    CommonModule, FormsModule, CardModule, DataViewModule, TagModule,
    ButtonModule, InputTextModule, IconFieldModule, InputIconModule,
    SkeletonModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.scss']
})
export class MateriasComponent implements OnInit {
  private authService = inject(AuthService);
  private messageService = inject(MessageService);

  loading = signal(true);

  readonly periodoActual = 'Primavera 2026';

  // En producción esto vendría del backend. Se usa data mock representativa.
  materias = signal<MateriaCard[]>([]);

  readonly totalAlumnos = () => this.materias().reduce((sum, m) => sum + m.totalAlumnos, 0);

  ngOnInit() {
    // Simula la carga desde el backend (ms-alumnos / ms-periodos)
    setTimeout(() => {
      this.materias.set([
        {
          id: '1',
          nombre: 'Desarrollo de Sistemas Distribuidos',
          nrc: '12345',
          horario: 'Lun/Mié/Vie 08:00–09:30',
          aula: 'Lab. 3-A, Edif. FCCyT',
          totalAlumnos: 32,
          color: '#06B6D4'
        },
        {
          id: '2',
          nombre: 'Redes de Computadoras',
          nrc: '12346',
          horario: 'Mar/Jue 10:00–11:30',
          aula: 'Aula 2-B, Edif. FCCyT',
          totalAlumnos: 28,
          color: '#4338CA'
        },
        {
          id: '3',
          nombre: 'Base de Datos Avanzadas',
          nrc: '12347',
          horario: 'Lun/Mié 13:00–14:30',
          aula: 'Lab. 1-C, Edif. FCCyT',
          totalAlumnos: 27,
          color: '#F59E0B'
        }
      ]);
      this.loading.set(false);
    }, 800);
  }
}
