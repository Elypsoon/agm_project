import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { ToastModule } from 'primeng/toast';
import { SkeletonModule } from 'primeng/skeleton';
import { MessageService } from 'primeng/api';
import { AlumnosService, Alumno } from '../../../core/services/alumnos.service';

interface Calificacion {
  alumnoId: string;
  nombre: string;
  matricula: string;
  parcial1: number | null;
  parcial2: number | null;
  parcial3: number | null;
  promedio: number | null;
  estado: 'aprobado' | 'reprobado' | 'sin_calificar';
}

interface MateriaOption {
  id: string;
  nombre: string;
}

@Component({
  selector: 'app-docente-calificaciones',
  standalone: true,
  imports: [
    CommonModule, FormsModule, TableModule, SelectModule, TagModule,
    ButtonModule, InputNumberModule, ToastModule, SkeletonModule
  ],
  providers: [MessageService],
  templateUrl: './calificaciones.component.html',
  styleUrls: ['./calificaciones.component.scss']
})
export class CalificacionesComponent implements OnInit {
  private messageService = inject(MessageService);

  loading = signal(false);
  editedRows = signal<Set<string>>(new Set());

  selectedMateriaId: string | null = null;

  readonly materiaOptions: MateriaOption[] = [
    { id: '1', nombre: 'Desarrollo de Sistemas Distribuidos (NRC 12345)' },
    { id: '2', nombre: 'Redes de Computadoras (NRC 12346)' },
    { id: '3', nombre: 'Base de Datos Avanzadas (NRC 12347)' }
  ];

  calificaciones = signal<Calificacion[]>([]);

  readonly aprobados = () => this.calificaciones().filter(c => c.estado === 'aprobado').length;
  readonly reprobados = () => this.calificaciones().filter(c => c.estado === 'reprobado').length;
  readonly sinCalificar = () => this.calificaciones().filter(c => c.estado === 'sin_calificar').length;

  ngOnInit() {}

  onMateriaChange() {
    if (!this.selectedMateriaId) return;
    this.loading.set(true);
    this.editedRows.set(new Set());

    setTimeout(() => {
      this.calificaciones.set(this.generateMockData());
      this.loading.set(false);
    }, 600);
  }

  private generateMockData(): Calificacion[] {
    const names = [
      'Ana García López', 'Carlos Pérez Ruiz', 'María Hernández', 'José Martínez',
      'Laura Sánchez', 'Roberto Torres', 'Claudia Ramírez', 'Miguel Ángel Cruz',
      'Sofía Morales', 'Daniel Flores', 'Valentina López', 'Andrés Jiménez'
    ];
    return names.map((n, i) => {
      const p1 = 5 + Math.round(Math.random() * 5 * 10) / 10;
      const p2 = 5 + Math.round(Math.random() * 5 * 10) / 10;
      const p3 = i < 2 ? null : 5 + Math.round(Math.random() * 5 * 10) / 10;
      const promedio = p3 !== null ? Math.round(((p1 + p2 + p3) / 3) * 10) / 10 : null;
      return {
        alumnoId: `alumno-${i}`,
        nombre: n,
        matricula: `2022${String(10 + i).padStart(7, '0')}`,
        parcial1: p1,
        parcial2: p2,
        parcial3: p3,
        promedio,
        estado: promedio === null ? 'sin_calificar' : promedio >= 6 ? 'aprobado' : 'reprobado'
      };
    });
  }

  onCalChange(row: Calificacion) {
    const p = [row.parcial1, row.parcial2, row.parcial3].filter(v => v !== null) as number[];
    row.promedio = p.length > 0 ? Math.round((p.reduce((a, b) => a + b, 0) / p.length) * 10) / 10 : null;
    if (p.length === 3) {
      row.estado = row.promedio! >= 6 ? 'aprobado' : 'reprobado';
    } else {
      row.estado = 'sin_calificar';
    }
    const s = new Set(this.editedRows());
    s.add(row.alumnoId);
    this.editedRows.set(s);
  }

  onRowEditInit(row: Calificacion) {}

  onRowEditSave(row: Calificacion) {
    const s = new Set(this.editedRows());
    s.add(row.alumnoId);
    this.editedRows.set(s);
  }

  onRowEditCancel(row: Calificacion) {}

  guardarCambios() {
    this.messageService.add({
      severity: 'success',
      summary: 'Guardado',
      detail: `${this.editedRows().size} registro(s) actualizado(s) correctamente`,
      life: 3000
    });
    this.editedRows.set(new Set());
  }

  estadoLabel(estado: string): string {
    const map: Record<string, string> = {
      aprobado: 'Aprobado', reprobado: 'Reprobado', sin_calificar: 'Sin calificar'
    };
    return map[estado] ?? estado;
  }

  estadoSeverity(estado: string): 'success' | 'danger' | 'warn' | 'info' | 'secondary' {
    const map: Record<string, any> = {
      aprobado: 'success', reprobado: 'danger', sin_calificar: 'secondary'
    };
    return map[estado] ?? 'secondary';
  }
}
