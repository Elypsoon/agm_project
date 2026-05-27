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
import { SkeletonModule } from 'primeng/skeleton';
import { ProgressBarModule } from 'primeng/progressbar';
import { TooltipModule } from 'primeng/tooltip';
import { MessageService } from 'primeng/api';
import { firstValueFrom } from 'rxjs';

import { PeriodosService, Materia } from '../periodos/periodos.service';

export interface MateriaInstancia {
  id: string;
  nrc: string;
  periodoNombre: string;
  docente: string;
  horario: string;
  aula: string;
  estado: string;
}

export interface UniqueMateria {
  clave: string;
  nombre: string;
  plan_estudios: string;
  campus: string;
  instancias: MateriaInstancia[];
  periodosNames: string[];
  docentesNames: string[];
  totalGrupos: number;
}

@Component({
  selector: 'app-admin-materias',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, FormsModule,
    TableModule, ButtonModule, InputTextModule, IconFieldModule, InputIconModule,
    TagModule, DialogModule, ToastModule, SkeletonModule, ProgressBarModule,
    SelectModule, TooltipModule
  ],
  providers: [MessageService],
  templateUrl: './materias.component.html',
  styleUrls: ['./materias.component.scss']
})
export class MateriasComponent implements OnInit {

  loading = true;
  searchValue = '';
  uniqueMaterias: UniqueMateria[] = [];

  showCreateDialog = false;
  createForm: FormGroup;

  periodOptions: { label: string; value: string }[] = [];
  campusOptions = [
    { label: 'Campus CU San Manuel', value: 'SAN_MANUEL' },
    { label: 'Campus CU2', value: 'CU2' }
  ];
  planOptions = [
    { label: 'Ingeniería en Tecnologías de la Información (ITI)', value: 'ITI' },
    { label: 'Licenciatura en Ciencias de la Computación (LCC)', value: 'LCC' },
    { label: 'Ingeniería en Ciencias de la Computación (ICC)', value: 'ICC' }
  ];

  constructor(
    private fb: FormBuilder,
    private messageService: MessageService,
    private periodosService: PeriodosService
  ) {
    this.createForm = this.fb.group({
      nrc:     ['', [Validators.required, Validators.pattern(/^\d{5}$/)]],
      clave:   ['', [Validators.required, Validators.pattern(/^[A-Z]{3,5}\s?\d{3}$/i)]],
      nombre:  ['', Validators.required],
      docente: ['POR ASIGNAR', Validators.required],
      periodo: ['', Validators.required],
      plan:    ['ITI', Validators.required],
      campus:  ['SAN_MANUEL', Validators.required],
      seccion: ['001', Validators.required],
    });
  }

  ngOnInit() {
    this.loadData();
  }

  get filteredMaterias(): UniqueMateria[] {
    if (!this.searchValue) {
      return this.uniqueMaterias;
    }
    const search = this.searchValue.toLowerCase();
    return this.uniqueMaterias.filter(m =>
      m.nombre.toLowerCase().includes(search) ||
      m.clave.toLowerCase().includes(search) ||
      m.plan_estudios.toLowerCase().includes(search) ||
      m.campus.toLowerCase().includes(search)
    );
  }

  async loadData() {
    this.loading = true;
    try {
      // 1. Fetch all materias and periodos
      const [materias, periodos] = await Promise.all([
        this.periodosService.getAllMaterias(),
        firstValueFrom(this.periodosService.getPeriodos())
      ]);

      const periodosMap = new Map<string, string>();
      periodos.forEach(p => periodosMap.set(p.id, p.nombre));

      // Populate period options for manual creation
      this.periodOptions = periodos.map(p => ({
        label: p.nombre,
        value: p.id
      }));

      // 2. Group materias by clave (or name if empty)
      const groups = new Map<string, Materia[]>();
      
      materias.forEach(m => {
        const key = (m.clave || m.nombre).trim().toUpperCase();
        if (!groups.has(key)) {
          groups.set(key, []);
        }
        groups.get(key)!.push(m);
      });

      // 3. Map groups to UniqueMateria
      this.uniqueMaterias = Array.from(groups.values()).map(items => {
        const first = items[0];
        
        // Collect unique period names
        const periodIds = Array.from(new Set(items.map(i => i.periodo)));
        const periodosNames = periodIds.map(id => periodosMap.get(id) || 'Desconocido');

        // Collect unique teacher names
        const docentesNames = Array.from(new Set(
          items
            .map(i => i.docente_nombre || 'POR ASIGNAR')
            .filter(name => name.trim() !== '-' && name.trim() !== '')
        ));

        // Map instances
        const instancias = items.map(i => {
          return {
            id: i.id,
            nrc: i.nrc,
            periodoNombre: periodosMap.get(i.periodo) || 'Desconocido',
            docente: i.docente_nombre || 'POR ASIGNAR',
            horario: this.formatHorarios(i.horarios),
            aula: i.horarios && i.horarios.length > 0 ? i.horarios[0].salon : 'POR ASIGNAR',
            estado: i.estado
          };
        });

        return {
          clave: first.clave || 'S/C',
          nombre: first.nombre,
          plan_estudios: first.plan_estudios || 'ITI',
          campus: first.campus,
          instancias: instancias,
          periodosNames: periodosNames,
          docentesNames: docentesNames,
          totalGrupos: items.length
        };
      });

      this.loading = false;
    } catch (error) {
      console.error(error);
      this.messageService.add({ severity: 'error', summary: 'Error', detail: 'Error al cargar las materias.' });
      this.loading = false;
    }
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

  openCreateDialog() {
    this.createForm.reset({
      docente: 'POR ASIGNAR',
      plan: 'ITI',
      campus: 'SAN_MANUEL',
      seccion: '001'
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
      nrc: val.nrc,
      clave: val.clave.toUpperCase(),
      nombre: val.nombre,
      seccion: val.seccion,
      docente_nombre: val.docente,
      plan_estudios: val.plan,
      campus: val.campus,
      periodo: val.periodo,
      estado: 'abierta'
    };

    this.periodosService.createMateria(payload).subscribe({
      next: () => {
        this.messageService.add({ severity: 'success', summary: 'Materia creada', detail: `NRC ${val.nrc} registrado con éxito.` });
        this.showCreateDialog = false;
        this.loadData();
      },
      error: (err) => {
        console.error(err);
        this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudo crear la materia.' });
      }
    });
  }

  deleteMateriaInstance(instance: MateriaInstancia, name: string) {
    if (confirm(`¿Estás seguro de que deseas eliminar el grupo NRC ${instance.nrc} de ${name}?`)) {
      this.periodosService.deleteMateria(instance.id).subscribe({
        next: () => {
          this.messageService.add({ severity: 'success', summary: 'Grupo eliminado', detail: `NRC ${instance.nrc} eliminado.` });
          this.loadData();
        },
        error: (err) => {
          console.error(err);
          this.messageService.add({ severity: 'error', summary: 'Error', detail: 'No se pudo eliminar el grupo.' });
        }
      });
    }
  }

  isInvalid(field: string): boolean {
    const c = this.createForm.get(field);
    return !!(c?.invalid && (c.dirty || c.touched));
  }
}
