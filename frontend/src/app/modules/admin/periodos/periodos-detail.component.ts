import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { TableModule } from 'primeng/table';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { PeriodosService, Periodo } from './periodos.service';

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

  goBack() {
    this.router.navigate(['/admin/periodos']);
  }
}
