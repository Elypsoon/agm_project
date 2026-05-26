import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { PeriodosService, Periodo } from './periodos.service';

@Component({
  selector: 'agm-admin-periodos',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TableModule, TagModule, ButtonModule],
  templateUrl: './periodos.component.html',
  styleUrls: ['./periodos.component.scss']
})
export class PeriodosComponent implements OnInit {
  private fb = inject(FormBuilder);
  private periodosService = inject(PeriodosService);

  periodos: Periodo[] = [];
  activePeriodo: Periodo | null = null;
  loading = false;
  errorMessage = '';
  successMessage = '';
  lastUpdated = 0;
  createDialog = false;
  periodoForm: FormGroup;
  actionLoading = '';
  uploadError = '';
  uploadSuccess = '';
  selectedFile: File | null = null;
  importTargetId: string | null = null;

  constructor() {
    this.periodoForm = this.fb.group({
      nombre: ['', Validators.required],
      fecha_inicio: ['', Validators.required],
      fecha_fin: ['', Validators.required],
      plan_estudios: ['', Validators.required]
    });
  }

  ngOnInit() {
    this.loadPeriodos();
  }

  loadPeriodos() {
    this.loading = true;
    this.errorMessage = '';
    this.successMessage = '';
    this.uploadError = '';
    this.uploadSuccess = '';

    this.periodosService.getPeriodos().subscribe({
      next: (data) => {
        this.periodos = data ?? [];
        this.lastUpdated = Date.now();
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err?.message || 'No se pudo cargar los periodos.';
      }
    });

    this.periodosService.getActivePeriodo().subscribe({
      next: (periodo) => {
        this.activePeriodo = periodo;
      },
      error: () => {
        this.activePeriodo = null;
      }
    });
  }

  openCreateDialog() {
    this.createDialog = true;
    this.periodoForm.reset();
  }

  closeCreateDialog() {
    this.createDialog = false;
  }

  submitNewPeriodo() {
    if (this.periodoForm.invalid) {
      this.periodoForm.markAllAsTouched();
      return;
    }

    this.actionLoading = 'create';
    this.errorMessage = '';
    this.successMessage = '';

    const payload = this.periodoForm.value;
    this.periodosService.createPeriodo(payload).subscribe({
      next: () => {
        this.actionLoading = '';
        this.successMessage = 'Periodo creado correctamente.';
        this.closeCreateDialog();
        this.loadPeriodos();
      },
      error: (err) => {
        this.actionLoading = '';
        this.errorMessage = err?.message || 'No se pudo crear el periodo.';
      }
    });
  }

  activatePeriodo(periodo: Periodo) {
    if (periodo.activo) {
      return;
    }

    this.actionLoading = periodo.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.periodosService.activatePeriodo(periodo.id).subscribe({
      next: () => {
        this.actionLoading = '';
        this.successMessage = `Periodo "${periodo.nombre}" activado.`;
        this.loadPeriodos();
      },
      error: (err) => {
        this.actionLoading = '';
        this.errorMessage = err?.message || 'No se pudo activar el periodo.';
      }
    });
  }

  deletePeriodo(periodo: Periodo) {
    if (!confirm(`¿Eliminar el periodo "${periodo.nombre}"? Esta acción no se puede deshacer.`)) {
      return;
    }

    this.actionLoading = periodo.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.periodosService.deletePeriodo(periodo.id).subscribe({
      next: () => {
        this.actionLoading = '';
        this.successMessage = `Periodo "${periodo.nombre}" eliminado.`;
        this.loadPeriodos();
      },
      error: (err) => {
        this.actionLoading = '';
        this.errorMessage = err?.message || 'No se pudo eliminar el periodo.';
      }
    });
  }

  onFileChange(event: Event, periodoId: string) {
    const input = event.target as HTMLInputElement;
    this.selectedFile = input.files?.[0] ?? null;
    this.importTargetId = periodoId;
    this.uploadError = '';
    this.uploadSuccess = '';
  }

  uploadPdf(periodo: Periodo) {
    if (!this.selectedFile || this.importTargetId !== periodo.id) {
      this.uploadError = 'Selecciona un archivo PDF antes de subir.';
      return;
    }

    this.actionLoading = periodo.id;
    this.errorMessage = '';
    this.uploadError = '';
    this.uploadSuccess = '';

    this.periodosService.importPdf(periodo.id, this.selectedFile).subscribe({
      next: (res) => {
        this.actionLoading = '';
        this.uploadSuccess = res?.message || 'PDF importado con éxito.';
        this.selectedFile = null;
        this.importTargetId = null;
        this.loadPeriodos();
      },
      error: (err) => {
        this.actionLoading = '';
        this.uploadError = err?.error?.detail || err?.message || 'Error al importar el PDF.';
      }
    });
  }

  getPeriodosCount() {
    return this.periodos.length;
  }
}
