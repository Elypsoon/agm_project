import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { InputNumberModule } from 'primeng/inputnumber';
import { InputTextModule } from 'primeng/inputtext';
import { ToastModule } from 'primeng/toast';
import { SkeletonModule } from 'primeng/skeleton';
import { DialogModule } from 'primeng/dialog';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { forkJoin, Observable } from 'rxjs';
import { ReportesService } from '../../../core/services/reportes.service';

import { AuthService } from '../../../core/services/auth.service';
import { 
  CalificacionesService, 
  ConcentradoResponse, 
  ActividadHeader, 
  AlumnoConcentrado, 
  CategoriaPonderacion,
  PonderacionResponse
} from '../../../core/services/calificaciones.service';

interface MateriaOption {
  id: string;
  nombre: string;
}

@Component({
  selector: 'app-docente-calificaciones',
  standalone: true,
  imports: [
    CommonModule, FormsModule, TableModule, SelectModule, TagModule,
    ButtonModule, InputNumberModule, InputTextModule, ToastModule, 
    SkeletonModule, DialogModule, TooltipModule
  ],
  providers: [MessageService],
  templateUrl: './calificaciones.component.html',
  styleUrls: ['./calificaciones.component.scss']
})
export class CalificacionesComponent implements OnInit {
  private messageService = inject(MessageService);
  private authService = inject(AuthService);
  private calificacionesService = inject(CalificacionesService);
  private reportesService = inject(ReportesService);

  loading = signal(false);
  editedRows = signal<Set<string>>(new Set());

  // Materias y Periodos
  periodoActivo = signal<any>(null);
  selectedMateriaId: string | null = null;
  materiaOptions = signal<MateriaOption[]>([]);

  // Ponderaciones y Concentrado
  hasPonderaciones = signal<boolean>(false);
  ponderaciones = signal<CategoriaPonderacion[]>([]);
  esquemaBloqueado = signal<boolean>(false);
  concentrado = signal<ConcentradoResponse | null>(null);
  allActividades = signal<ActividadHeader[]>([]);

  // Modales
  showPondDialog = signal<boolean>(false);
  showActDialog = signal<boolean>(false);
  showImportDialog = signal<boolean>(false);

  // Formulario Ponderaciones
  newPonderaciones = signal<{ nombre: string; porcentaje: number }[]>([
    { nombre: 'Exámenes', porcentaje: 50 },
    { nombre: 'Tareas', porcentaje: 30 },
    { nombre: 'Proyectos', porcentaje: 20 }
  ]);

  // Formulario Actividades
  nuevaActividad = {
    ponderacion_id: '',
    nombre: '',
    descripcion: ''
  };

  // Formulario Importar
  importSelectedCriterio = signal<string>('');
  importSelectedFile: File | null = null;

  // Control de Modal de Confirmación para Eliminar Actividad
  showConfirmDeleteDialog = signal<boolean>(false);
  actividadAEliminar = signal<{ id: string; nombre: string } | null>(null);

  // Estadísticas locales basadas en los alumnos cargados
  readonly aprobados = computed(() => 
    this.concentrado()?.alumnos.filter(c => this.tieneCalificaciones(c) && c.promedio_redondeado >= 6).length || 0
  );
  readonly reprobados = computed(() => 
    this.concentrado()?.alumnos.filter(c => this.tieneCalificaciones(c) && c.promedio_redondeado < 6).length || 0
  );
  readonly sinCalificar = computed(() => 
    this.concentrado()?.alumnos.filter(c => !this.tieneCalificaciones(c)).length || 0
  );

  readonly totalPonderaciones = computed(() => 
    this.newPonderaciones().reduce((sum, item) => sum + item.porcentaje, 0)
  );

  readonly ponderacionOptions = computed(() => 
    this.ponderaciones().map(p => ({
      id: p.id,
      nombre: `${p.nombre} (${p.porcentaje}%)`
    }))
  );

  ngOnInit() {
    this.cargarPeriodoYMaterias();
  }

  cargarPeriodoYMaterias() {
    this.loading.set(true);
    // 1. Obtener el periodo activo
    this.calificacionesService.getPeriodoActivo().subscribe({
      next: (periodo) => {
        this.periodoActivo.set(periodo);
        const docenteId = this.authService.currentUser()?.id;

        // 2. Obtener materias asociadas a este docente en el periodo activo
        this.calificacionesService.getMaterias({
          periodo_id: periodo.id,
          docente_id: docenteId
        }).subscribe({
          next: (res) => {
            const list = res.results || res || [];
            this.materiaOptions.set(list.map((m: any) => ({
              id: m.id,
              nombre: `${m.nombre} (NRC ${m.nrc})`
            })));
            this.loading.set(false);
          },
          error: () => {
            this.loading.set(false);
            this.messageService.add({
              severity: 'error',
              summary: 'Error',
              detail: 'No se pudieron cargar las materias del docente.',
              life: 4000
            });
          }
        });
      },
      error: () => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'warn',
          summary: 'Aviso',
          detail: 'No hay un periodo académico activo actualmente en el sistema.',
          life: 4000
        });
      }
    });
  }

  onMateriaChange() {
    if (!this.selectedMateriaId) {
      this.concentrado.set(null);
      this.allActividades.set([]);
      this.ponderaciones.set([]);
      this.esquemaBloqueado.set(false);
      return;
    }
    this.loading.set(true);
    this.editedRows.set(new Set());
    this.cargarConcentrado();
  }

  cargarConcentrado() {
    if (!this.selectedMateriaId) return;
    this.loading.set(true);

    forkJoin({
      concentrado: this.calificacionesService.getConcentrado(this.selectedMateriaId),
      ponderaciones: this.calificacionesService.getPonderaciones(this.selectedMateriaId)
    }).subscribe({
      next: (res) => {
        this.concentrado.set(res.concentrado);
        this.ponderaciones.set(res.ponderaciones.categorias || []);
        this.esquemaBloqueado.set(res.ponderaciones.bloqueada || false);

        // Aplanar todas las actividades de las distintas categorías
        const acts: ActividadHeader[] = [];
        res.concentrado.categorias.forEach(cat => {
          acts.push(...cat.actividades);
        });
        this.allActividades.set(acts);
        this.hasPonderaciones.set(true);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        // Si responde 404 es porque no hay ponderaciones o concentrado
        if (err.status === 404 || err.error?.status === 404) {
          this.hasPonderaciones.set(false);
          this.ponderaciones.set([]);
          this.esquemaBloqueado.set(false);
          this.concentrado.set(null);
          this.allActividades.set([]);

          // Mostrar un aviso informativo claro para guiar al docente
          this.messageService.add({
            severity: 'info',
            summary: 'Esquema requerido',
            detail: err.error?.detail || 'Esta materia aún no tiene categorías de ponderación configuradas. Crea los criterios (Exámenes, Tareas, etc.) para comenzar.',
            life: 6000
          });
        } else {
          this.messageService.add({
            severity: 'error',
            summary: 'Error de conexión',
            detail: err.error?.detail || 'Error al obtener el concentrado de calificaciones. Si la materia es nueva, asegúrate de haber configurado sus criterios de evaluación (categorías de ponderación).',
            life: 7000
          });
        }
      }
    });
  }

  // ── Métodos de Ponderaciones ───────────────────────────────────────────────

  abrirPonderacionesModal() {
    this.newPonderaciones.set([
      { nombre: 'Exámenes', porcentaje: 50 },
      { nombre: 'Tareas', porcentaje: 30 },
      { nombre: 'Proyectos', porcentaje: 20 }
    ]);
    this.showPondDialog.set(true);
  }

  abrirEditarPonderacionesModal() {
    const current = this.ponderaciones().map(p => ({
      nombre: p.nombre,
      porcentaje: p.porcentaje
    }));

    if (current.length === 0) {
      this.newPonderaciones.set([
        { nombre: 'Exámenes', porcentaje: 50 },
        { nombre: 'Tareas', porcentaje: 30 },
        { nombre: 'Proyectos', porcentaje: 20 }
      ]);
    } else {
      this.newPonderaciones.set(current);
    }
    this.showPondDialog.set(true);
  }

  addPonderacionRow() {
    this.newPonderaciones.set([
      ...this.newPonderaciones(),
      { nombre: '', porcentaje: 0 }
    ]);
  }

  removePonderacionRow(index: number) {
    const list = [...this.newPonderaciones()];
    list.splice(index, 1);
    this.newPonderaciones.set(list);
  }

  onPorcentajeChange() {
    this.newPonderaciones.set([...this.newPonderaciones()]);
  }

  guardarPonderaciones() {
    const total = this.newPonderaciones().reduce((sum, item) => sum + item.porcentaje, 0);
    if (total !== 100) {
      this.messageService.add({
        severity: 'error',
        summary: 'Esquema Inválido',
        detail: `La suma de las ponderaciones debe ser exactamente 100%. Actualmente es del ${total}%`,
        life: 5000
      });
      return;
    }

    const payload = this.newPonderaciones().map((c, i) => ({
      nombre: c.nombre,
      porcentaje: c.porcentaje,
      orden: i + 1,
      activa: true
    }));

    this.loading.set(true);
    this.calificacionesService.crearPonderaciones(this.selectedMateriaId!, payload).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Esquema Configurado',
          detail: 'Las ponderaciones se configuraron correctamente.',
          life: 3000
        });
        this.showPondDialog.set(false);
        this.cargarConcentrado();
      },
      error: (err) => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.error?.detail || 'No se pudieron registrar las ponderaciones.',
          life: 5000
        });
      }
    });
  }

  // ── Métodos de Actividades ─────────────────────────────────────────────────

  abrirActividadModal() {
    this.nuevaActividad = {
      ponderacion_id: this.ponderaciones().length > 0 ? this.ponderaciones()[0].id : '',
      nombre: '',
      descripcion: ''
    };
    this.showActDialog.set(true);
  }

  guardarActividad() {
    if (!this.nuevaActividad.nombre.trim() || !this.nuevaActividad.ponderacion_id) {
      this.messageService.add({
        severity: 'error',
        summary: 'Campos requeridos',
        detail: 'Por favor ingresa el nombre de la actividad y selecciona una categoría.',
        life: 3000
      });
      return;
    }

    this.loading.set(true);
    this.calificacionesService.crearActividad({
      materia_id: this.selectedMateriaId!,
      ponderacion_id: this.nuevaActividad.ponderacion_id,
      nombre: this.nuevaActividad.nombre,
      descripcion: this.nuevaActividad.descripcion
    }).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Actividad creada',
          detail: 'La actividad se registró correctamente.',
          life: 3000
        });
        this.showActDialog.set(false);
        this.cargarConcentrado();
      },
      error: (err) => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.error?.detail || 'No se pudo registrar la actividad.',
          life: 5000
        });
      }
    });
  }

  solicitarEliminarActividad(actividadId: string, nombre: string) {
    this.actividadAEliminar.set({ id: actividadId, nombre });
    this.showConfirmDeleteDialog.set(true);
  }

  confirmarEliminarActividad() {
    const act = this.actividadAEliminar();
    if (!act) return;

    this.loading.set(true);
    this.calificacionesService.eliminarActividad(act.id).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Actividad eliminada',
          detail: `La actividad "${act.nombre}" se eliminó correctamente.`,
          life: 3000
        });
        this.showConfirmDeleteDialog.set(false);
        this.actividadAEliminar.set(null);
        this.cargarConcentrado();
      },
      error: (err) => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.error?.detail || 'No se pudo eliminar la actividad.',
          life: 5000
        });
      }
    });
  }

  // ── Métodos de Importación ──────────────────────────────────────────────────

  abrirImportarModal() {
    this.importSelectedCriterio.set(this.ponderaciones().length > 0 ? this.ponderaciones()[0].nombre : '');
    this.importSelectedFile = null;
    this.showImportDialog.set(true);
  }

  onFileSelected(event: any) {
    const file = event.target.files[0];
    if (file) {
      this.importSelectedFile = file;
    }
  }

  ejecutarImportacion() {
    if (!this.importSelectedFile || !this.importSelectedCriterio()) {
      this.messageService.add({
        severity: 'error',
        summary: 'Campos requeridos',
        detail: 'Por favor selecciona el criterio e ingresa el archivo Excel.',
        life: 3000
      });
      return;
    }

    this.loading.set(true);
    this.calificacionesService.importarCalificaciones(
      this.selectedMateriaId!,
      this.importSelectedCriterio(),
      this.importSelectedFile
    ).subscribe({
      next: (res) => {
        this.messageService.add({
          severity: 'success',
          summary: 'Importación Completada',
          detail: res.message || 'Se importaron las calificaciones de manera exitosa.',
          life: 5000
        });
        this.showImportDialog.set(false);
        this.cargarConcentrado();
      },
      error: (err) => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error en Importación',
          detail: err.error?.detail || 'Ocurrió un error al procesar el archivo Excel.',
          life: 5000
        });
      }
    });
  }

  // ── Gestión Dinámica del Concentrado de Tabla ───────────────────────────────

  getGrade(row: AlumnoConcentrado, actividadId: string): number | null {
    const calif = row.calificaciones.find(c => c.actividad_id === actividadId);
    return calif ? calif.valor : null;
  }

  setGrade(row: AlumnoConcentrado, actividadId: string, valor: number | null) {
    const val = valor === null ? 0 : valor;
    let calif = row.calificaciones.find(c => c.actividad_id === actividadId);
    if (calif) {
      calif.valor = val;
    } else {
      row.calificaciones.push({ actividad_id: actividadId, valor: val });
    }

    // Recalcular el promedio real y oficial en base a las reglas de redondeo institucionales
    this.recalcularPromedioLocal(row);

    // Trackear que esta fila tiene cambios pendientes
    const s = new Set(this.editedRows());
    s.add(row.alumno_id);
    this.editedRows.set(s);
  }

  recalcularPromedioLocal(row: AlumnoConcentrado) {
    const conf = this.concentrado();
    if (!conf) return;

    let total = 0;
    for (const cat of conf.categorias) {
      const actIds = cat.actividades.map(a => a.actividad_id);
      if (actIds.length === 0) continue;

      let sumCat = 0;
      for (const actId of actIds) {
        sumCat += this.getGrade(row, actId) || 0;
      }
      const promedioCat = sumCat / actIds.length;
      total += promedioCat * (cat.porcentaje / 100);
    }

    row.promedio_real = Math.round(total * 100) / 100;

    // Regla oficial de redondeo institucional
    const enDiez = total / 10;
    const entero = Math.floor(enDiez);
    const fraccion = enDiez - entero;

    if (enDiez < 6.0) {
      row.promedio_redondeado = entero; // Reprobado: truncamiento / función piso
    } else {
      if (fraccion >= 0.5) {
        row.promedio_redondeado = Math.ceil(enDiez); // Aprobado >= 0.5 redondea hacia arriba
      } else {
        row.promedio_redondeado = entero; // Aprobado < 0.5 redondea hacia abajo
      }
    }
  }

  onCalChange(row: AlumnoConcentrado, actividadId: string, valor: number | null) {
    this.setGrade(row, actividadId, valor);
  }

  onRowEditInit(row: AlumnoConcentrado) {}

  onRowEditSave(row: AlumnoConcentrado) {
    const s = new Set(this.editedRows());
    s.add(row.alumno_id);
    this.editedRows.set(s);
  }

  onRowEditCancel(row: AlumnoConcentrado) {
    // Para cancelar, simplemente volvemos a solicitar el concentrado original del servidor
    this.cargarConcentrado();
  }

  guardarCambios() {
    const requests: Observable<any>[] = [];

    for (const alumnoId of this.editedRows()) {
      const student = this.concentrado()?.alumnos.find(a => a.alumno_id === alumnoId);
      if (!student) continue;

      // Iterar sobre las actividades para guardar de forma individual
      this.allActividades().forEach(act => {
        const val = this.getGrade(student, act.actividad_id);
        if (val !== null) {
          requests.push(this.calificacionesService.actualizarCalificacion({
            actividad_id: act.actividad_id,
            alumno_id: student.alumno_id,
            valor: val
          }));
        }
      });
    }

    if (requests.length === 0) {
      this.editedRows.set(new Set());
      return;
    }

    this.loading.set(true);
    forkJoin(requests).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Guardado exitoso',
          detail: `${this.editedRows().size} alumno(s) actualizado(s) correctamente.`,
          life: 3000
        });
        this.editedRows.set(new Set());
        this.cargarConcentrado();
      },
      error: (err) => {
        this.loading.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error al Guardar',
          detail: err.error?.detail || 'No se pudieron actualizar algunas calificaciones.',
          life: 5000
        });
      }
    });
  }

  tieneCalificaciones(row: AlumnoConcentrado): boolean {
    return row.calificaciones.length > 0 && row.calificaciones.some(c => c.valor !== null);
  }

  estadoLabel(row: AlumnoConcentrado): string {
    if (!this.tieneCalificaciones(row)) return 'Sin calificar';
    return row.promedio_redondeado >= 6 ? 'Aprobado' : 'Reprobado';
  }

  estadoSeverity(row: AlumnoConcentrado): 'success' | 'danger' | 'secondary' {
    if (!this.tieneCalificaciones(row)) return 'secondary';
    return row.promedio_redondeado >= 6 ? 'success' : 'danger';
  }

  exportarCalificaciones() {
    if (!this.selectedMateriaId) return;
    
    const email = this.authService.currentUser()?.email || 'docente@buap.mx';
    
    this.messageService.add({
      severity: 'info',
      summary: 'Exportando',
      detail: 'Iniciando la exportación de calificaciones...',
      life: 2000
    });

    this.reportesService.descargarCalificaciones(this.selectedMateriaId, email, 'xlsx').subscribe({
      next: (res) => {
        if (res.isBlob) {
          const blob = res.blob;
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = res.filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          this.messageService.add({
            severity: 'success',
            summary: 'Descargado',
            detail: 'El archivo se ha descargado correctamente.',
            life: 3000
          });
        } else if (res.async) {
          this.messageService.add({
            severity: 'success',
            summary: '✉️ Reporte en Proceso',
            detail: res.message || 'El reporte se está procesando y lo recibirás en tu correo.',
            life: 6000
          });
        }
      },
      error: (err) => {
        console.error('[-] Error al exportar calificaciones:', err);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo exportar el reporte en este momento.',
          life: 4000
        });
      }
    });
  }

  exportarAsistencias() {
    if (!this.selectedMateriaId) return;
    
    const email = this.authService.currentUser()?.email || 'docente@buap.mx';
    
    this.messageService.add({
      severity: 'info',
      summary: 'Exportando',
      detail: 'Iniciando la exportación de asistencias...',
      life: 2000
    });

    this.reportesService.descargarAsistencias(this.selectedMateriaId, email, 'xlsx').subscribe({
      next: (res) => {
        if (res.isBlob) {
          const blob = res.blob;
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = res.filename;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);

          this.messageService.add({
            severity: 'success',
            summary: 'Descargado',
            detail: 'El archivo se ha descargado correctamente.',
            life: 3000
          });
        } else if (res.async) {
          this.messageService.add({
            severity: 'success',
            summary: '✉️ Reporte en Proceso',
            detail: res.message || 'El reporte se está procesando y lo recibirás en tu correo.',
            life: 6000
          });
        }
      },
      error: (err) => {
        console.error('[-] Error al exportar asistencias:', err);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo exportar el reporte en este momento.',
          life: 4000
        });
      }
    });
  }


}
