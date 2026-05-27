import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { TagModule } from 'primeng/tag';
import { DialogModule } from 'primeng/dialog';
import { ToastModule } from 'primeng/toast';
import { SelectModule } from 'primeng/select';
import { MultiSelectModule } from 'primeng/multiselect';
import { AvatarModule } from 'primeng/avatar';
import { SkeletonModule } from 'primeng/skeleton';
import { TooltipModule } from 'primeng/tooltip';
import { ProgressBarModule } from 'primeng/progressbar';
import { MessageService } from 'primeng/api';
import { firstValueFrom, forkJoin } from 'rxjs';

import { DocentesService } from '../../../core/services/docentes.service';
import { PeriodosService } from '../periodos/periodos.service';

export interface Docente {
  id: string;
  nombre: string;
  email: string;
  departamento: string;
  materias: number;
}

@Component({
  selector: 'app-admin-docentes',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule,
    TableModule, ButtonModule, InputTextModule, IconFieldModule, InputIconModule,
    TagModule, DialogModule, ToastModule, SelectModule, MultiSelectModule, AvatarModule, SkeletonModule,
    TooltipModule, ProgressBarModule
  ],
  providers: [MessageService],
  templateUrl: './docentes.component.html',
  styleUrls: ['./docentes.component.scss']
})
export class DocentesComponent implements OnInit {

  loading = true;
  searchValue = '';
  docentes: Docente[] = [];

  showCreateDialog = false;
  showAssignDialog = false;
  showImportDialog = false;
  isEditMode = false;
  selectedDocente: Docente | null = null;

  materiaOptions: { label: string; value: string }[] = [];
  selectedMaterias: string[] = [];

  importLoading = false;
  selectedFile: File | null = null;
  uploadError = '';
  uploadSuccess = '';

  createForm: FormGroup;

  constructor(
    private fb: FormBuilder,
    private messageService: MessageService,
    private docentesService: DocentesService,
    private periodosService: PeriodosService
  ) {
    this.createForm = this.fb.group({
      nombre:       ['', [Validators.required, Validators.minLength(2)]],
      email:        ['', [Validators.required, Validators.email]],
      departamento: ['', Validators.required],
    });
  }

  ngOnInit() {
    this.loadData();
  }

  get filteredDocentes(): Docente[] {
    if (!this.searchValue) {
      return this.docentes;
    }
    const search = this.searchValue.toLowerCase();
    return this.docentes.filter(d =>
      d.nombre.toLowerCase().includes(search) ||
      d.email.toLowerCase().includes(search) ||
      d.departamento.toLowerCase().includes(search)
    );
  }

  async loadData() {
    this.loading = true;
    try {
      // 1. Fetch all materias and periodos to calculate counts
      const [materias, periodos] = await Promise.all([
        this.periodosService.getAllMaterias(),
        firstValueFrom(this.periodosService.getPeriodos())
      ]);

      const periodosMap = new Map<string, string>();
      periodos.forEach(p => periodosMap.set(p.id, p.nombre));

      // Populate assignment options
      this.materiaOptions = materias.map(m => {
        const periodName = periodosMap.get(m.periodo) || 'Periodo Desconocido';
        return {
          label: `${m.nombre} (${m.nrc}) — ${m.plan_estudios} (${periodName})`,
          value: m.id
        };
      });

      // 2. Fetch docentes from MS-Alumnos
      this.docentesService.getDocentes({ limit: 1000 }).subscribe({
        next: (res) => {
          if (res.success && res.data && res.data.docentes) {
            this.docentes = res.data.docentes.map(d => {
              // Count materias assigned to this docente
              const docenteMaterias = materias.filter(m =>
                (m.docente_id && m.docente_id === d.id) ||
                (!m.docente_id && m.docente_nombre && m.docente_nombre.trim().toLowerCase() === d.nombre_completo.trim().toLowerCase())
              );
              return {
                id: d.id,
                nombre: d.nombre_completo,
                email: d.correo_institucional,
                departamento: d.cubiculo || 'Sin cubículo',
                materias: docenteMaterias.length
              };
            });
          }
          this.loading = false;
        },
        error: (err) => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron cargar los docentes.' });
          this.loading = false;
        }
      });
    } catch (error) {
      console.error(error);
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Error de comunicación con los servicios.' });
      this.loading = false;
    }
  }

  getInitials(nombre: string): string {
    const parts = nombre.split(' ');
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : nombre.substring(0, 2).toUpperCase();
  }

  openAssignDialog(docente: Docente) {
    this.selectedDocente = docente;
    this.selectedMaterias = [];
    this.showAssignDialog = true;
  }

  saveAssignment() {
    if (!this.selectedMaterias || this.selectedMaterias.length === 0 || !this.selectedDocente) {
      this.messageService.add({ severity: 'warn', summary: 'Selecciona al menos una materia', detail: '' });
      return;
    }
    const docente = this.selectedDocente;
    const requests = this.selectedMaterias.map(materiaId => 
      this.periodosService.updateMateria(materiaId, {
        docente_id: docente.id,
        docente_nombre: docente.nombre
      })
    );

    this.loading = true;
    forkJoin(requests).subscribe({
      next: () => {
        this.messageService.add({
          severity: 'success',
          summary: 'Asignaciones guardadas',
          detail: `Materias asignadas con éxito a ${docente.nombre}.`
        });
        this.showAssignDialog = false;
        this.loadData();
      },
      error: (err) => {
        console.error(err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudieron realizar algunas asignaciones.' });
        this.loading = false;
      }
    });
  }

  openCreateDialog() {
    this.isEditMode = false;
    this.selectedDocente = null;
    this.createForm.reset();
    this.showCreateDialog = true;
  }

  openEditDialog(docente: Docente) {
    this.selectedDocente = docente;
    this.isEditMode = true;
    this.createForm.patchValue({
      nombre: docente.nombre,
      email: docente.email,
      departamento: docente.departamento === 'Sin cubículo' ? '' : docente.departamento
    });
    this.showCreateDialog = true;
  }

  submitCreate() {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }
    const val = this.createForm.value;
    const payload = {
      nombre_completo: val.nombre,
      correo_institucional: val.email,
      cubiculo: val.departamento
    };

    if (this.isEditMode && this.selectedDocente) {
      this.docentesService.updateDocente(this.selectedDocente.id, payload).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Docente actualizado', detail: val.nombre });
          this.showCreateDialog = false;
          this.createForm.reset();
          this.loadData();
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudo actualizar el docente.' });
        }
      });
    } else {
      this.docentesService.createDocente(payload).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Docente registrado', detail: val.nombre });
          this.showCreateDialog = false;
          this.createForm.reset();
          this.loadData();
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudo registrar el docente.' });
        }
      });
    }
  }

  deleteDocente(docente: Docente) {
    if (confirm(`¿Estás seguro de que deseas eliminar al docente ${docente.nombre}?`)) {
      this.docentesService.deleteDocente(docente.id).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Docente eliminado', detail: docente.nombre });
          this.loadData();
        },
        error: () => {
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el docente.' });
        }
      });
    }
  }

  openImportDialog() {
    this.selectedFile = null;
    this.uploadError = '';
    this.uploadSuccess = '';
    this.showImportDialog = true;
  }

  onFileChange(event: Event) {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
    this.uploadError = '';
    this.uploadSuccess = '';
  }

  uploadPdf() {
    if (!this.selectedFile) {
      this.uploadError = 'Selecciona un archivo PDF antes de continuar.';
      return;
    }
    this.importLoading = true;
    this.uploadError = '';
    this.uploadSuccess = '';

    this.docentesService.importarDocentes(this.selectedFile).subscribe({
      next: (res) => {
        this.importLoading = false;
        if (res.success) {
          this.uploadSuccess = res.message || 'PDF importado correctamente.';
          this.selectedFile = null;
          this.messageService.add({
            severity: 'success',
            summary: 'Importación exitosa',
            detail: res.message
          });
          this.loadData();
          setTimeout(() => {
            this.showImportDialog = false;
            this.uploadSuccess = '';
          }, 1500);
        } else {
          this.uploadError = res.message || 'Error al procesar el PDF.';
        }
      },
      error: (err) => {
        this.importLoading = false;
        const msg = err.error?.detail || err.error?.message || 'Error al subir el archivo.';
        this.uploadError = `Error: ${msg}`;
        this.messageService.add({
          severity: 'error',
          summary: 'Error de importación',
          detail: msg
        });
      }
    });
  }

  isInvalid(field: string): boolean {
    const c = this.createForm.get(field);
    return !!(c?.invalid && (c.dirty || c.touched));
  }
}
