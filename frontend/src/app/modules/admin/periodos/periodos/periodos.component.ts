import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { PeriodosService, Periodo } from '../periodos.service';

@Component({
  selector: 'agm-admin-periodos',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TableModule, TagModule, ButtonModule, TooltipModule],
  templateUrl: './periodos.component.html',
  styleUrls: ['./periodos.component.scss']
})
export class PeriodosComponent implements OnInit {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private periodosService = inject(PeriodosService);

  periodos: Periodo[] = [];
  activePeriodo: Periodo | null = null;
  loading = false;
  errorMessage = '';
  successMessage = '';
  lastUpdated = 0;
  createDialog = false;
  importDialogOpened = false;
  importTargetId: string | null = null;
  importTargetName = '';
  periodoForm: FormGroup;
  editPeriodoForm: FormGroup;
  actionLoading = '';
  uploadError = '';
  uploadSuccess = '';
  selectedFile: File | null = null;
  editingPeriodo: Periodo | null = null;
  showEditPeriodoDialog = false;

  constructor() {
    this.periodoForm = this.fb.group({
      nombre: ['', Validators.required],
      fecha_inicio: ['', Validators.required],
      fecha_fin: ['', Validators.required]
    });
    this.editPeriodoForm = this.fb.group({
      nombre: ['', Validators.required],
      fecha_inicio: ['', Validators.required],
      fecha_fin: ['', Validators.required]
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

  openImportDialog(periodo: Periodo) {
    this.importDialogOpened = true;
    this.importTargetId = periodo.id;
    this.importTargetName = periodo.nombre;
    this.selectedFile = null;
    this.uploadError = '';
    this.uploadSuccess = '';
  }

  closeImportDialog() {
    this.importDialogOpened = false;
    this.importTargetId = null;
    this.importTargetName = '';
    this.selectedFile = null;
    this.uploadError = '';
    this.uploadSuccess = '';
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
    if (periodo.estado === 'activo') {
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

  uploadPdf() {
    if (!this.selectedFile || !this.importTargetId) {
      this.uploadError = 'Selecciona un archivo PDF antes de subir.';
      return;
    }

    this.actionLoading = this.importTargetId;
    this.errorMessage = '';
    this.uploadError = '';
    this.uploadSuccess = '';

    this.periodosService.importPdf(this.importTargetId, this.selectedFile).subscribe({
      next: (res) => {
        this.actionLoading = '';
        this.uploadSuccess = res?.message || 'PDF importado con éxito.';
        this.selectedFile = null;
        this.importTargetId = null;
        this.loadPeriodos();
        this.closeImportDialog();
      },
      error: (err) => {
        this.actionLoading = '';
        this.uploadError = err?.error?.detail || err?.message || 'Error al importar el PDF.';
      }
    });
  }

  viewPeriodoDetails(periodo: Periodo) {
    this.router.navigate(['/admin/periodos', periodo.id]);
  }

  deactivatePeriodo(periodo: Periodo) {
    if (periodo.estado !== 'activo') {
      return;
    }

    this.actionLoading = periodo.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.periodosService.deactivatePeriodo(periodo.id).subscribe({
      next: () => {
        this.actionLoading = '';
        this.successMessage = `Periodo "${periodo.nombre}" desactivado.`;
        this.loadPeriodos();
      },
      error: (err) => {
        this.actionLoading = '';
        this.errorMessage = err?.message || 'No se pudo desactivar el periodo.';
      }
    });
  }

  openEditPeriodoDialog(periodo: Periodo) {
    this.editingPeriodo = { ...periodo };
    this.editPeriodoForm.patchValue({
      nombre: periodo.nombre,
      fecha_inicio: periodo.fecha_inicio,
      fecha_fin: periodo.fecha_fin
    });
    this.showEditPeriodoDialog = true;
  }

  closeEditPeriodoDialog() {
    this.showEditPeriodoDialog = false;
    this.editingPeriodo = null;
    this.editPeriodoForm.reset();
  }

  saveEditPeriodo() {
    if (!this.editingPeriodo || !this.editPeriodoForm.valid) {
      return;
    }

    this.actionLoading = this.editingPeriodo.id;
    this.errorMessage = '';
    this.successMessage = '';

    this.periodosService.updatePeriodo(this.editingPeriodo.id, this.editPeriodoForm.value).subscribe({
      next: () => {
        this.actionLoading = '';
        this.successMessage = `Periodo "${this.editPeriodoForm.value.nombre}" actualizado.`;
        this.closeEditPeriodoDialog();
        this.loadPeriodos();
      },
      error: (err) => {
        this.actionLoading = '';
        this.errorMessage = err?.message || 'No se pudo actualizar el periodo.';
      }
    });
  }

  getPeriodosCount() {
    return this.periodos.length;
  }

  getEstadoLabel(estado: string): string {
    const labels: { [key: string]: string } = {
      'pendiente': 'Pendiente',
      'activo': 'Activo',
      'finalizada': 'Finalizada'
    };
    return labels[estado.toLowerCase()] || estado;
  }

  getEstadoSeverity(estado: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    const severity: { [key: string]: 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' } = {
      'pendiente': 'warn',
      'activo': 'success',
      'finalizada': 'info'
    };
    return severity[estado.toLowerCase()] || 'secondary';
  }
}
