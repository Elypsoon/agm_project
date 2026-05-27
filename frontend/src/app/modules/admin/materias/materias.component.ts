import { Component, OnInit, signal } from '@angular/core';
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
import { MessageService } from 'primeng/api';
import { SkeletonModule } from 'primeng/skeleton';
import { ProgressBarModule } from 'primeng/progressbar';

export interface Materia {
  id: string;
  nrc: string;
  nombre: string;
  docente: string;
  horario: string;
  aula: string;
  alumnos: number;
  periodo: string;
}

@Component({
  selector: 'app-admin-materias',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule,
    TableModule, ButtonModule, InputTextModule, IconFieldModule, InputIconModule,
    TagModule, DialogModule, ToastModule, SkeletonModule, ProgressBarModule
  ],
  providers: [MessageService],
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.scss']
})
export class MateriasComponent implements OnInit {

  loading = true;
  importLoading = false;
  searchValue = '';

  materias: Materia[] = [];

  showImportDialog = false;
  showCreateDialog = false;
  selectedFile: File | null = null;
  uploadError = '';
  uploadSuccess = '';
  importTargetPeriodo = 'Primavera 2026';

  createForm: FormGroup;

  constructor(private fb: FormBuilder, private messageService: MessageService) {
    this.createForm = this.fb.group({
      nrc:     ['', [Validators.required, Validators.pattern(/^\d{5}$/)]],
      nombre:  ['', Validators.required],
      docente: ['', Validators.required],
      horario: ['', Validators.required],
      aula:    ['', Validators.required],
    });
  }

  ngOnInit() {
    // Mock data — reemplazar con llamada al servicio
    setTimeout(() => {
      this.materias = [
        { id: '1', nrc: '12345', nombre: 'Servicios Web', docente: 'Dr. Martínez López', horario: 'Lun-Mié 08:00-10:00', aula: 'A-301', alumnos: 28, periodo: 'Primavera 2026' },
        { id: '2', nrc: '12346', nombre: 'Ingeniería de Software', docente: 'Mtra. García Ruiz', horario: 'Mar-Jue 10:00-12:00', aula: 'B-102', alumnos: 32, periodo: 'Primavera 2026' },
        { id: '3', nrc: '12347', nombre: 'Redes de Computadoras', docente: 'Dr. López Sánchez', horario: 'Lun-Mié 12:00-14:00', aula: 'C-204', alumnos: 25, periodo: 'Primavera 2026' },
        { id: '4', nrc: '12348', nombre: 'Base de Datos Avanzadas', docente: 'Dr. Hernández Cruz', horario: 'Mar-Jue 14:00-16:00', aula: 'A-201', alumnos: 30, periodo: 'Primavera 2026' },
        { id: '5', nrc: '12349', nombre: 'Cálculo Diferencial', docente: 'Mtra. Torres Vega', horario: 'Vie 08:00-12:00', aula: 'B-303', alumnos: 35, periodo: 'Primavera 2026' },
      ];
      this.loading = false;
    }, 700);
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
    // Simular importación
    setTimeout(() => {
      this.importLoading = false;
      this.uploadSuccess = 'PDF importado correctamente. Se registraron 12 materias.';
      this.selectedFile = null;
      this.messageService.add({ severity: 'success', summary: 'Importación exitosa', detail: 'Materias importadas correctamente.' });
    }, 1800);
  }

  submitCreate() {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }
    this.messageService.add({ severity: 'success', summary: 'Materia creada', detail: `NRC ${this.createForm.value.nrc} registrado.` });
    this.showCreateDialog = false;
    this.createForm.reset();
  }

  isInvalid(field: string): boolean {
    const c = this.createForm.get(field);
    return !!(c?.invalid && (c.dirty || c.touched));
  }
}
