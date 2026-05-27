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
import { DialogModule } from 'primeng/dialog';
import { ProgressBarModule } from 'primeng/progressbar';
import { MessageService } from 'primeng/api';

import { AlumnosService } from '../../../core/services/alumnos.service';
import { AuthService } from '../../../core/services/auth.service';
import { DocentesService } from '../../../core/services/docentes.service';
import { PeriodosService } from '../../admin/periodos/periodos.service';

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
    SkeletonModule, ToastModule, DialogModule, ProgressBarModule
  ],
  providers: [MessageService],
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.scss']
})
export class MateriasComponent implements OnInit {
  private authService = inject(AuthService);
  private messageService = inject(MessageService);
  private docentesService = inject(DocentesService);
  private periodosService = inject(PeriodosService);
  private alumnosService = inject(AlumnosService);

  loading = signal(true);
  periodoActual = 'Cargando...';
  materias = signal<MateriaCard[]>([]);

  // Variables para la importación de alumnos
  showImportDialog = false;
  importLoading = false;
  selectedFile: File | null = null;
  uploadError = '';
  uploadSuccess = '';
  materiaParaImportar: MateriaCard | null = null;

  readonly totalAlumnos = () => this.materias().reduce((sum, m) => sum + m.totalAlumnos, 0);

  ngOnInit() {
    this.cargarMaterias();
  }

  cargarMaterias() {
    this.loading.set(true);
    const email = this.authService.currentUser()?.email;
    if (!email) {
      this.loading.set(false);
      return;
    }

    // 1. Buscar docente por su correo en ms-alumnos
    this.docentesService.getDocentes({ search: email }).subscribe({
      next: (docentesRes) => {
        const docente = docentesRes.data?.docentes?.find(d => d.correo_institucional === email);
        if (!docente) {
          this.loading.set(false);
          this.messageService.add({
            severity: 'error',
            summary: 'Error de Perfil',
            detail: 'No se encontró el perfil de docente correspondiente en la base de datos.'
          });
          return;
        }

        // 2. Obtener el periodo activo
        this.periodosService.getActivePeriodo().subscribe({
          next: (periodo) => {
            this.periodoActual = periodo.nombre;

            // 3. Consultar materias asociadas al docente en el periodo activo
            this.periodosService.getMaterias(1, 200).subscribe({
              next: (materiasRes) => {
                const materiasFiltradas = (materiasRes.results || materiasRes || []).filter(
                  (m: any) => m.docente_id === docente.id && m.periodo === periodo.id
                );

                if (materiasFiltradas.length === 0) {
                  this.materias.set([]);
                  this.loading.set(false);
                  return;
                }

                const colors = ['#06B6D4', '#4338CA', '#F59E0B', '#10B981', '#8B5CF6', '#EC4899'];
                
                const requests = materiasFiltradas.map((m: any, index: number) => {
                  return new Promise<MateriaCard>((resolve) => {
                    this.alumnosService.getAlumnosByMateria(m.id, { limit: 1 }).subscribe({
                      next: (alumnosRes) => {
                        resolve({
                          id: m.id,
                          nombre: m.nombre,
                          nrc: m.nrc,
                          horario: this.formatHorarios(m.horarios),
                          aula: m.horarios && m.horarios.length > 0 ? m.horarios[0].salon : 'POR ASIGNAR',
                          totalAlumnos: alumnosRes.data?.total ?? 0,
                          color: colors[index % colors.length]
                        });
                      },
                      error: () => {
                        resolve({
                          id: m.id,
                          nombre: m.nombre,
                          nrc: m.nrc,
                          horario: this.formatHorarios(m.horarios),
                          aula: m.horarios && m.horarios.length > 0 ? m.horarios[0].salon : 'POR ASIGNAR',
                          totalAlumnos: 0,
                          color: colors[index % colors.length]
                        });
                      }
                    });
                  });
                });

                Promise.all(requests).then((cards) => {
                  this.materias.set(cards);
                  this.loading.set(false);
                });
              },
              error: (err) => {
                console.error(err);
                this.loading.set(false);
                this.messageService.add({
                  severity: 'error',
                  summary: 'Error',
                  detail: 'Error al cargar las materias del servidor.'
                });
              }
            });
          },
          error: (err) => {
            console.error(err);
            this.loading.set(false);
            this.messageService.add({
              severity: 'warn',
              summary: 'Aviso',
              detail: 'No hay un periodo académico activo.'
            });
          }
        });
      },
      error: (err) => {
        console.error(err);
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo obtener el perfil del docente.'
        });
      }
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

  openImportDialog(materia: MateriaCard) {
    this.materiaParaImportar = materia;
    this.selectedFile = null;
    this.uploadError = '';
    this.uploadSuccess = '';
    this.showImportDialog = true;
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    if (file) {
      if (!file.name.toLowerCase().endsWith('.pdf')) {
        this.uploadError = 'El archivo debe ser un PDF.';
        this.selectedFile = null;
        return;
      }
      this.selectedFile = file;
      this.uploadError = '';
      this.uploadSuccess = '';
    }
  }

  uploadPdf() {
    if (!this.selectedFile || !this.materiaParaImportar) {
      this.uploadError = 'Por favor selecciona un archivo PDF.';
      return;
    }

    this.importLoading = true;
    this.uploadError = '';
    this.uploadSuccess = '';

    this.alumnosService.importarAlumnos(this.materiaParaImportar.id, this.selectedFile).subscribe({
      next: (res) => {
        this.importLoading = false;
        if (res.success) {
          const nuevos = res.data?.nuevos ?? 0;
          const actualizados = res.data?.actualizados ?? 0;
          this.uploadSuccess = `Importación exitosa. Nuevos alumnos: ${nuevos}, actualizados: ${actualizados}.`;
          this.messageService.add({
            severity: 'success',
            summary: 'Alumnos importados',
            detail: `Se procesaron correctamente los alumnos para la materia.`
          });
          this.cargarMaterias();
        } else {
          this.uploadError = res.message || 'Error al procesar el archivo.';
        }
      },
      error: (err) => {
        this.importLoading = false;
        console.error(err);
        this.uploadError = err.error?.detail || err.error?.message || 'Error de red o del servidor al importar alumnos.';
      }
    });
  }
}
