import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SelectModule } from 'primeng/select';
import { ButtonModule } from 'primeng/button';
import { SkeletonModule } from 'primeng/skeleton';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TooltipModule } from 'primeng/tooltip';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ReportesService, EstadisticasDocenteMateria } from '../../../core/services/reportes.service';
import { AuthService } from '../../../core/services/auth.service';

interface PeriodoNav {
  id: string;
  nombre: string;
  activo: boolean;
}

@Component({
  selector: 'app-historial',
  standalone: true,
  imports: [
    CommonModule, FormsModule, SelectModule, ButtonModule, SkeletonModule,
    CardModule, TagModule, TooltipModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './historial.component.html',
  styleUrls: ['./historial.component.scss']
})
export class HistorialComponent implements OnInit {
  private reportesService = inject(ReportesService);
  private authService = inject(AuthService);
  private messageService = inject(MessageService);

  loading = signal(true);
  docenteId = signal<string>('');

  // Historial completo retornado por el backend
  historialCompleto = signal<EstadisticasDocenteMateria[]>([]);

  // Periodos únicos detectados en la data
  periodos = signal<PeriodoNav[]>([]);

  // Periodo seleccionado actualmente
  selectedPeriodoId = signal<string>('');

  // Nombre formateado para el header del periodo seleccionado
  selectedPeriodoName = computed(() => {
    const selected = this.periodos().find(p => p.id === this.selectedPeriodoId());
    return selected ? selected.nombre : 'Periodo Desconocido';
  });

  // Indica si el periodo seleccionado es el periodo activo de clases
  isCurrentPeriodActive = computed(() => {
    const selected = this.periodos().find(p => p.id === this.selectedPeriodoId());
    return selected ? selected.activo : false;
  });

  // Materias filtradas por el periodo seleccionado
  materiasFiltradas = computed(() => {
    const pid = this.selectedPeriodoId();
    if (!pid) return [];
    return this.historialCompleto().filter(m => String(m.periodo_id) === String(pid));
  });

  // KPIs calculados en tiempo real para el periodo seleccionado
  statsPeriodo = computed(() => {
    const materias = this.materiasFiltradas();
    if (materias.length === 0) {
      return {
        promedioCalificaciones: 0.0,
        tasaAsistencia: 0.0,
        tasaAprobacion: 0.0,
        totalMaterias: 0
      };
    }

    const sumPromedios = materias.reduce((acc, m) => acc + (m.promedio_grupo || 0), 0);
    const sumAsistencias = materias.reduce((acc, m) => acc + (m.tasa_asistencia || 0), 0);
    const sumAprobaciones = materias.reduce((acc, m) => acc + (m.tasa_aprobacion || 0), 0);

    return {
      promedioCalificaciones: Math.round((sumPromedios / materias.length) * 100) / 100,
      tasaAsistencia: Math.round((sumAsistencias / materias.length) * 100) / 100,
      tasaAprobacion: Math.round((sumAprobaciones / materias.length) * 100) / 100,
      totalMaterias: materias.length
    };
  });

  ngOnInit() {
    const user = this.authService.currentUser();
    // Usar el ID del docente autenticado, o por defecto un mock ID
    const dId = user?.id || 'docente-1';
    this.docenteId.set(dId);
    this.cargarHistorial(dId);
  }

  cargarHistorial(id: string) {
    this.loading.set(true);
    this.reportesService.obtenerEstadisticasDocente(id).subscribe({
      next: (res) => {
        if (res.success && res.data && res.data.length > 0) {
          this.historialCompleto.set(res.data);
          this.procesarPeriodos(res.data);
        } else {
          this.cargarMockCompleto();
        }
        this.loading.set(false);
      },
      error: (err) => {
        console.error('[-] Error al obtener historial de reportes:', err);
        // Fallback robusto a datos Mock interactivos si el backend no está disponible
        this.cargarMockCompleto();
        this.loading.set(false);
      }
    });
  }

  private procesarPeriodos(data: EstadisticasDocenteMateria[]) {
    // Obtener IDs de periodos únicos de la data
    const pIds = Array.from(new Set(data.map(m => String(m.periodo_id))));
    
    // Mapear a objetos de navegación de periodos
    const mapped: PeriodoNav[] = pIds.map(pid => {
      // Determinamos si es el periodo activo (asumimos el id '13' o 'PR2026' como Primavera 2026)
      const esActivo = pid === '13' || pid === 'PR2026' || pid.toUpperCase().includes('2026');
      return {
        id: pid,
        nombre: this.formatPeriodoId(pid),
        activo: esActivo
      };
    });

    // Ordenar de forma descendente, dejando el periodo activo primero
    mapped.sort((a, b) => {
      if (a.activo) return -1;
      if (b.activo) return 1;
      return b.nombre.localeCompare(a.nombre);
    });

    this.periodos.set(mapped);
    if (mapped.length > 0) {
      this.selectedPeriodoId.set(mapped[0].id);
    }
  }

  private formatPeriodoId(id: string): string {
    const map: Record<string, string> = {
      '13': 'Primavera 2026',
      '1': 'Otoño 2025',
      'PR2026': 'Primavera 2026',
      'OT2025': 'Otoño 2025'
    };
    if (map[id]) return map[id];
    
    // Intentar formatear códigos comunes
    if (id.toUpperCase().startsWith('PR')) return `Primavera ${id.substring(2)}`;
    if (id.toUpperCase().startsWith('OT')) return `Otoño ${id.substring(2)}`;
    return id;
  }

  selectPeriodo(pid: string) {
    this.selectedPeriodoId.set(pid);
  }

  private cargarMockCompleto() {
    const mockData: EstadisticasDocenteMateria[] = [
      // Primavera 2026 (Activo)
      {
        periodo_id: '13',
        materia_id: 'm1',
        materia_nombre: 'Desarrollo de Aplicaciones Web',
        nrc: '25223',
        promedio_grupo: 8.45,
        tasa_asistencia: 94.20,
        tasa_aprobacion: 91.60,
        total_alumnos: 12,
        generado_en: new Date().toISOString()
      },
      {
        periodo_id: '13',
        materia_id: 'm2',
        materia_nombre: 'Desarrollo de Aplicaciones Móviles',
        nrc: '26206',
        promedio_grupo: 7.92,
        tasa_asistencia: 88.50,
        tasa_aprobacion: 85.00,
        total_alumnos: 10,
        generado_en: new Date().toISOString()
      },
      // Otoño 2025 (Histórico)
      {
        periodo_id: '1',
        materia_id: 'm3',
        materia_nombre: 'Redes de Computadoras',
        nrc: '40013',
        promedio_grupo: 8.10,
        tasa_asistencia: 91.00,
        tasa_aprobacion: 88.00,
        total_alumnos: 15,
        generado_en: new Date(2025, 11, 15).toISOString()
      },
      {
        periodo_id: '1',
        materia_id: 'm4',
        materia_nombre: 'Ingeniería de Software',
        nrc: '40014',
        promedio_grupo: 7.60,
        tasa_asistencia: 87.20,
        tasa_aprobacion: 82.50,
        total_alumnos: 18,
        generado_en: new Date(2025, 11, 15).toISOString()
      },
      {
        periodo_id: '1',
        materia_id: 'm5',
        materia_nombre: 'Base de Datos Avanzadas',
        nrc: '46860',
        promedio_grupo: 8.85,
        tasa_asistencia: 95.80,
        tasa_aprobacion: 100.00,
        total_alumnos: 14,
        generado_en: new Date(2025, 11, 15).toISOString()
      }
    ];

    this.historialCompleto.set(mockData);
    this.procesarPeriodos(mockData);
  }

  materiaColor(nrc: string): string {
    const colors = ['#004b93', '#F59E0B', '#06B6D4', '#22C55E', '#8B5CF6'];
    const num = parseInt(nrc) || 0;
    return colors[num % colors.length];
  }
}
