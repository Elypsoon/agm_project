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
import { AvatarModule } from 'primeng/avatar';
import { SkeletonModule } from 'primeng/skeleton';
import { MessageService } from 'primeng/api';

export interface Docente {
  id: string;
  nombre: string;
  email: string;
  departamento: string;
  materias: number;
  estado: 'activo' | 'inactivo';
  claveAcceso?: string;
}

@Component({
  selector: 'app-admin-docentes',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule,
    TableModule, ButtonModule, InputTextModule, IconFieldModule, InputIconModule,
    TagModule, DialogModule, ToastModule, SelectModule, AvatarModule, SkeletonModule
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
  selectedDocente: Docente | null = null;

  materiaOptions = [
    { label: 'Servicios Web (12345)', value: '1' },
    { label: 'Ingeniería de Software (12346)', value: '2' },
    { label: 'Redes de Computadoras (12347)', value: '3' },
    { label: 'Base de Datos Avanzadas (12348)', value: '4' },
  ];
  selectedMateria: string | null = null;

  createForm: FormGroup;

  constructor(private fb: FormBuilder, private messageService: MessageService) {
    this.createForm = this.fb.group({
      nombre:       ['', [Validators.required, Validators.minLength(2)]],
      email:        ['', [Validators.required, Validators.email]],
      departamento: ['', Validators.required],
    });
  }

  ngOnInit() {
    setTimeout(() => {
      this.docentes = [
        { id: '1', nombre: 'Dr. Martínez López',  email: 'martinez@itson.edu.mx',  departamento: 'Ciencias Exactas', materias: 2, estado: 'activo' },
        { id: '2', nombre: 'Mtra. García Ruiz',   email: 'garcia@itson.edu.mx',    departamento: 'Ingeniería',       materias: 3, estado: 'activo' },
        { id: '3', nombre: 'Dr. López Sánchez',   email: 'lopez@itson.edu.mx',     departamento: 'Ciencias Exactas', materias: 1, estado: 'activo' },
        { id: '4', nombre: 'Dr. Hernández Cruz',  email: 'hernandez@itson.edu.mx', departamento: 'Ingeniería',       materias: 2, estado: 'inactivo' },
        { id: '5', nombre: 'Mtra. Torres Vega',   email: 'torres@itson.edu.mx',    departamento: 'Matemáticas',      materias: 1, estado: 'activo' },
      ];
      this.loading = false;
    }, 700);
  }

  getInitials(nombre: string): string {
    const parts = nombre.split(' ');
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : nombre.substring(0, 2).toUpperCase();
  }

  openAssignDialog(docente: Docente) {
    this.selectedDocente = docente;
    this.selectedMateria = null;
    this.showAssignDialog = true;
  }

  saveAssignment() {
    if (!this.selectedMateria) {
      this.messageService.add({ severity: 'warn', summary: 'Selecciona una materia', detail: '' });
      return;
    }
    const mat = this.materiaOptions.find(m => m.value === this.selectedMateria);
    this.messageService.add({
      severity: 'success',
      summary: 'Asignación guardada',
      detail: `${mat?.label} asignada a ${this.selectedDocente?.nombre}.`
    });
    this.showAssignDialog = false;
  }

  submitCreate() {
    if (this.createForm.invalid) {
      this.createForm.markAllAsTouched();
      return;
    }
    this.messageService.add({ severity: 'success', summary: 'Docente registrado', detail: this.createForm.value.nombre });
    this.showCreateDialog = false;
    this.createForm.reset();
  }

  isInvalid(field: string): boolean {
    const c = this.createForm.get(field);
    return !!(c?.invalid && (c.dirty || c.touched));
  }
}
