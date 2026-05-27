import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { InputTextModule } from 'primeng/inputtext';
import { PeriodosService, Periodo, Horario, Materia } from './periodos.service';

@Component({
  selector: 'agm-periodos-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    TableModule,
    ButtonModule,
    TagModule,
    InputTextModule
  ],
  templateUrl: './periodos-detail.component.html',
  styleUrls: ['./periodos-detail.component.scss']
})
export class PeriodosDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private periodosService = inject(PeriodosService);

  periodo: Periodo | null = null;
  loading = true;
  errorMessage = '';
  expandedMateriaId: string | null = null;
  
  searchText = '';
  selectedPlanEstudios: string | null = null;
  selectedCampus: string | null = null;

  planEstudiosMap = {
    'ITI': 'Ingeniería en Tecnologías de la Información',
    'LCC': 'Licenciatura en Ciencias de la Computación',
    'ICC': 'Ingeniería en Ciencias de la Computación',
    'ICD': 'Ingeniería en Ciencia de Datos',
    'ISC': 'Ingeniería en Ciberseguridad'
  };

  editingMateria: Materia | null = null;
  showEditModal = false;

  ngOnInit() {
    const periodoId = this.route.snapshot.paramMap.get('id');
    if (!periodoId) {
      this.errorMessage = 'Periodo no encontrado.';
      this.loading = false;
      return;
    }

    this.periodosService.getPeriodoById(periodoId).subscribe({
      next: (periodo) => {
        this.periodo = periodo;
        this.loading = false;
      },
      error: (err) => {
        this.errorMessage = err?.error?.detail || err?.message || 'No se pudo cargar el periodo.';
        this.loading = false;
      }
    });
  }

  toggleMateriaSchedule(materiaId: string) {
    this.expandedMateriaId = this.expandedMateriaId === materiaId ? null : materiaId;
  }

  isMateriaExpanded(materiaId: string) {
    return this.expandedMateriaId === materiaId;
  }

  getOrderedHorarios(horarios: Horario[]) {
    const order = ['L', 'A', 'M', 'J', 'V', 'S', 'D'];
    return [...horarios].sort((a, b) => {
      const idxA = order.indexOf(a.dia.toUpperCase());
      const idxB = order.indexOf(b.dia.toUpperCase());
      if (idxA === -1 && idxB === -1) {
        return a.dia.localeCompare(b.dia);
      }
      if (idxA === -1) {
        return 1;
      }
      if (idxB === -1) {
        return -1;
      }
      return idxA - idxB;
    });
  }

  getCampusBadgeStyle(campus: string) {
    if (campus === 'CU2') {
      return 'success';
    }
    if (campus === 'SAN_MANUEL') {
      return 'info';
    }
    return 'secondary';
  }

  getCampusLabel(campus: string) {
    if (campus === 'CU2') {
      return 'CU2';
    }
    if (campus === 'SAN_MANUEL') {
      return 'San Manuel';
    }
    return campus;
  }

  get filteredMaterias(): Materia[] {
    if (!this.periodo?.materias) {
      return [];
    }

    return this.periodo.materias.filter((materia) => {
      const matchesSearch =
        !this.searchText ||
        materia.nombre.toLowerCase().includes(this.searchText.toLowerCase()) ||
        materia.nrc.toLowerCase().includes(this.searchText.toLowerCase()) ||
        (materia.docente_nombre?.toLowerCase() || '').includes(this.searchText.toLowerCase());

      const matchesPlan = !this.selectedPlanEstudios || materia.plan_estudios === this.selectedPlanEstudios;
      const matchesCampus = !this.selectedCampus || materia.campus === this.selectedCampus;

      return matchesSearch && matchesPlan && matchesCampus;
    });
  }

  goBack() {
    this.router.navigate(['/admin/periodos']);
  }

  openEditModal(materia: Materia) {
    // Create a deep copy to avoid modifying the original
    this.editingMateria = JSON.parse(JSON.stringify(materia));
    this.showEditModal = true;
  }

  closeEditModal() {
    this.editingMateria = null;
    this.showEditModal = false;
  }

  addHorario() {
    if (!this.editingMateria) return;
    
    if (!this.editingMateria.horarios) {
      this.editingMateria.horarios = [];
    }
    
    this.editingMateria.horarios.push({
      id: '',
      dia: 'L',
      hora_inicio: '',
      hora_fin: '',
      salon: '',
      es_virtual: false
    });
  }

  deleteHorario(index: number) {
    if (!this.editingMateria?.horarios) return;
    this.editingMateria.horarios.splice(index, 1);
  }

  saveMateria() {
    if (!this.editingMateria) return;

    // Update the materia in the periodo's materias array
    if (this.periodo?.materias) {
      const index = this.periodo.materias.findIndex(m => m.id === this.editingMateria!.id);
      if (index !== -1) {
        this.periodo.materias[index] = this.editingMateria;
      }
    }

    // TODO: Call API to update materia on backend
    // this.periodosService.updateMateria(this.editingMateria).subscribe(...)

    this.closeEditModal();
  }
}
