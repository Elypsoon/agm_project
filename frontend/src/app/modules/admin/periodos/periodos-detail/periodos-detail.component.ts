import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { InputTextModule } from 'primeng/inputtext';
import { PeriodosService, Periodo, Horario, Materia } from '../periodos.service';

@Component({
  selector: 'agm-periodos-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    TableModule,
    ButtonModule,
    TagModule,
    TooltipModule,
    InputTextModule
  ],
  templateUrl: './periodos-detail.component.html',
  styleUrls: ['./periodos-detail.component.scss']
})
export class PeriodosDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private periodosService = inject(PeriodosService);

  periodoId: string | null = null;
  periodo: Periodo | null = null;
  loading = true;
  errorMessage = '';
  savingMateria = false;

  expandedMateriaId: string | null = null;
  searchText = '';
  selectedPlanEstudios: string | null = null;
  selectedCampus: string | null = null;

  planEstudiosMap: { [key: string]: string } = {
    'ITI': 'Ing. en Tecnologías de la Información',
    'LCC': 'Lic. en Ciencias de la Computación',
    'ICC': 'Ing. en Ciencias de la Computación',
    'ICD': 'Ing. en Ciencia de Datos',
    'ISC': 'Ing. en Ciberseguridad'
  };

  editingMateria: Materia | null = null;
  showEditModal = false;

  ngOnInit() {
    this.periodoId = this.route.snapshot.paramMap.get('id');
    if (!this.periodoId) {
      this.errorMessage = 'ID de periodo no encontrado en la URL.';
      this.loading = false;
      return;
    }
    this.loadPeriodo();
  }

  loadPeriodo() {
    this.loading = true;
    this.errorMessage = '';

    this.periodosService.getPeriodoById(this.periodoId!).subscribe({
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

  reloadPeriodo() {
    this.loadPeriodo();
  }

  // ─── Horario Toggle ───────────────────────────────────────────

  toggleMateriaSchedule(materiaId: string) {
    this.expandedMateriaId = this.expandedMateriaId === materiaId ? null : materiaId;
  }

  isMateriaExpanded(materiaId: string): boolean {
    return this.expandedMateriaId === materiaId;
  }

  // ─── Filters ──────────────────────────────────────────────────

  get filteredMaterias(): Materia[] {
    if (!this.periodo?.materias) return [];

    return this.periodo.materias.filter(materia => {
      const q = this.searchText.toLowerCase();
      const matchesSearch =
        !q ||
        materia.nombre.toLowerCase().includes(q) ||
        materia.nrc.toLowerCase().includes(q) ||
        (materia.docente_nombre?.toLowerCase() || '').includes(q);

      const matchesPlan = !this.selectedPlanEstudios || materia.plan_estudios === this.selectedPlanEstudios;
      const matchesCampus = !this.selectedCampus || materia.campus === this.selectedCampus;

      return matchesSearch && matchesPlan && matchesCampus;
    });
  }

  // ─── Helpers ──────────────────────────────────────────────────

  formatHora(hora: string | null): string {
    if (!hora) return '—';
    // Convert "0800" → "08:00"
    if (hora.length === 4) {
      return `${hora.slice(0, 2)}:${hora.slice(2)}`;
    }
    return hora;
  }

  getOrderedHorarios(horarios: Horario[]): Horario[] {
    const order = ['L', 'A', 'M', 'J', 'V', 'S', 'D'];
    return [...horarios].sort((a, b) => {
      const idxA = order.indexOf(a.dia.toUpperCase());
      const idxB = order.indexOf(b.dia.toUpperCase());
      if (idxA === -1 && idxB === -1) return a.dia.localeCompare(b.dia);
      if (idxA === -1) return 1;
      if (idxB === -1) return -1;
      return idxA - idxB;
    });
  }

  getDayName(dia: string): string {
    const dayMap: { [key: string]: string } = {
      'L': 'Lunes', 'A': 'Martes', 'M': 'Miérc.',
      'J': 'Jueves', 'V': 'Viernes', 'S': 'Sábado', 'D': 'Domingo'
    };
    return dayMap[dia.toUpperCase()] || dia;
  }

  getCampusBadgeStyle(campus: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    if (campus === 'CU2') return 'success';
    if (campus === 'SAN_MANUEL') return 'info';
    return 'secondary';
  }

  getCampusLabel(campus: string): string {
    if (campus === 'CU2') return 'CU2';
    if (campus === 'SAN_MANUEL') return 'San Manuel';
    return campus;
  }

  getEstadoLabel(estado: string): string {
    const labels: { [key: string]: string } = {
      'pendiente': 'Pendiente',
      'activo': 'Activo',
      'finalizada': 'Finalizada'
    };
    return labels[estado?.toLowerCase()] || estado;
  }

  getEstadoSeverity(estado: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    const map: { [key: string]: 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' } = {
      'pendiente': 'warn',
      'activo': 'success',
      'finalizada': 'info'
    };
    return map[estado?.toLowerCase()] || 'secondary';
  }

  getMateriaEstadoLabel(estado: string): string {
    const labels: { [key: string]: string } = {
      'abierta': 'Abierta',
      'cerrada': 'Cerrada',
      'finalizada': 'Finalizada'
    };
    return labels[estado?.toLowerCase()] || estado;
  }

  getMateriaEstadoSeverity(estado: string): 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' {
    const map: { [key: string]: 'success' | 'secondary' | 'info' | 'warn' | 'danger' | 'contrast' } = {
      'abierta': 'success',
      'cerrada': 'warn',
      'finalizada': 'info'
    };
    return map[estado?.toLowerCase()] || 'secondary';
  }

  goBack() {
    this.router.navigate(['/admin/periodos']);
  }

  // ─── Edit Modal ───────────────────────────────────────────────

  openEditModal(materia: Materia) {
    this.editingMateria = JSON.parse(JSON.stringify(materia));
    this.showEditModal = true;
  }

  closeEditModal() {
    this.editingMateria = null;
    this.showEditModal = false;
    this.savingMateria = false;
  }

  addHorario() {
    if (!this.editingMateria) return;
    if (!this.editingMateria.horarios) this.editingMateria.horarios = [];
    this.editingMateria.horarios.push({
      id: '', dia: 'L', hora_inicio: '', hora_fin: '', salon: '', es_virtual: false
    });
  }

  deleteHorario(index: number) {
    if (!this.editingMateria?.horarios) return;
    this.editingMateria.horarios.splice(index, 1);
  }

  saveMateria() {
    if (!this.editingMateria) return;

    this.savingMateria = true;

    const payload = {
      nombre: this.editingMateria.nombre,
      clave: this.editingMateria.clave,
      seccion: this.editingMateria.seccion,
      docente_nombre: this.editingMateria.docente_nombre,
      campus: this.editingMateria.campus,
      plan_estudios: this.editingMateria.plan_estudios,
      estado: this.editingMateria.estado,
      nrc: this.editingMateria.nrc,
      horarios: (this.editingMateria.horarios || []).map(horario => {
        const h: any = {
          dia: horario.dia,
          hora_inicio: horario.hora_inicio,
          hora_fin: horario.hora_fin,
          salon: horario.salon,
          es_virtual: horario.es_virtual
        };
        if (horario.id) h.id = horario.id;
        return h;
      })
    };

    this.periodosService.updateMateria(this.editingMateria.id, payload).subscribe({
      next: (updatedMateria) => {
        if (this.periodo?.materias) {
          const idx = this.periodo.materias.findIndex(m => m.id === this.editingMateria!.id);
          if (idx !== -1) this.periodo.materias[idx] = updatedMateria;
        }
        this.closeEditModal();
      },
      error: (err) => {
        this.savingMateria = false;
        alert('Error al actualizar la materia: ' + (err?.error?.detail || err?.message || 'Error desconocido'));
      }
    });
  }
}
