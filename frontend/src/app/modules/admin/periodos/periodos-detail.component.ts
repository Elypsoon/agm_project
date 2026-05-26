import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { PeriodosService, Periodo, Horario } from './periodos.service';

@Component({
  selector: 'agm-periodos-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, TableModule, ButtonModule, TagModule],
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

  goBack() {
    this.router.navigate(['/admin/periodos']);
  }
}
