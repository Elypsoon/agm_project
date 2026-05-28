import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { SkeletonModule } from 'primeng/skeleton';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { ReportesService, EstadisticasAlumnoMateria } from '../../../core/services/reportes.service';
import { AlumnosService } from '../../../core/services/alumnos.service';
import { AuthService } from '../../../core/services/auth.service';

interface MateriaOption {
  id: string;
  nombre: string;
}

@Component({
  selector: 'app-estadisticas',
  standalone: true,
  imports: [
    CommonModule, FormsModule, SelectModule, TagModule, SkeletonModule,
    ButtonModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './estadisticas.component.html',
  styleUrls: ['./estadisticas.component.scss']
})
export class EstadisticasComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private reportesService = inject(ReportesService);
  private alumnosService = inject(AlumnosService);
  private authService = inject(AuthService);
  private messageService = inject(MessageService);

  loading = signal(true);
  alumnoId = signal<string>('');
  selectedMateriaId = signal<string>('');
  
  // Lista de materias del alumno para el selector superior
  materias = signal<MateriaOption[]>([]);
  
  // Datos analíticos de la materia seleccionada
  stats = signal<EstadisticasAlumnoMateria | null>(null);

  // Semáforo de riesgo de asistencia (Regla BUAP 80%)
  asistenciaSeveridad = computed(() => {
    const risk = this.stats()?.asistencia_kpi?.estado_riesgo;
    if (risk === 'EXCELENTE') return 'success';
    if (risk === 'REGULAR') return 'warn';
    return 'danger'; // RIESGO_POR_FALTAS
  });

  // Clase CSS para el anillo circular de progreso de asistencia
  asistenciaClase = computed(() => {
    const risk = this.stats()?.asistencia_kpi?.estado_riesgo;
    if (risk === 'EXCELENTE') return 'risk-excellent';
    if (risk === 'REGULAR') return 'risk-regular';
    return 'risk-danger';
  });

  // Nombre de la materia seleccionada
  selectedMateriaNombre = computed(() => {
    const found = this.materias().find(m => m.id === this.selectedMateriaId());
    return found ? found.nombre : 'Selecciona una materia';
  });

  ngOnInit() {
    const user = this.authService.currentUser();
    const userId = user?.id || 'alumno-1';
    this.alumnoId.set(userId);

    // Cargar materias inscritas del alumno para el dropdown selector
    this.alumnosService.getAlumno(userId).subscribe({
      next: (res) => {
        const inscripciones = res.data.inscripciones?.filter(i => i.activo) ?? [];
        const options: MateriaOption[] = inscripciones.map(i => ({
          id: i.materia_id,
          nombre: i.materia_nombre
        }));

        this.materias.set(options);
        this.procesarRuta();
      },
      error: () => {
        this.materias.set([]);
        this.procesarRuta();
      }
    });
  }

  private procesarRuta() {
    // Escuchar parámetros de ruta
    this.route.queryParams.subscribe(params => {
      const materiaId = params['materia_id'];
      if (materiaId) {
        this.selectedMateriaId.set(materiaId);
        this.cargarEstadisticas(this.alumnoId(), materiaId);
      } else if (this.materias().length > 0) {
        // Si no hay parámetro, seleccionar la primera materia y actualizar URL
        const firstId = this.materias()[0].id;
        this.actualizarQueryParam(firstId);
      } else {
        this.loading.set(false);
      }
    });
  }

  cargarEstadisticas(alumnoId: string, materiaId: string) {
    this.loading.set(true);
    this.reportesService.obtenerEstadisticasAlumno(alumnoId, materiaId).subscribe({
      next: (res) => {
        if (res.success && res.data) {
          this.stats.set(res.data);
        } else {
          this.stats.set(null);
        }
        this.loading.set(false);
      },
      error: (err: any) => {
        console.error('[-] Error al obtener estadísticas del alumno:', err);
        this.stats.set(null);
        this.loading.set(false);
      }
    });
  }

  onMateriaChange(event: any) {
    const materiaId = event.value;
    if (materiaId) {
      this.actualizarQueryParam(materiaId);
    }
  }

  private actualizarQueryParam(materiaId: string) {
    this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { materia_id: materiaId },
      queryParamsHandling: 'merge'
    });
  }

  private mockMateriasOptions(): MateriaOption[] {
    return [
      { id: 'm1', nombre: 'Desarrollo de Aplicaciones Web' },
      { id: 'm2', nombre: 'Desarrollo de Aplicaciones Móviles' },
      { id: 'm3', nombre: 'Redes de Computadoras' },
      { id: 'm4', nombre: 'Ingeniería de Software' },
      { id: 'm5', nombre: 'Cálculo Diferencial e Integral' }
    ];
  }

  private generarMockStats(materiaId: string): EstadisticasAlumnoMateria {
    // Generar diferentes datos según el ID para pruebas
    let promedio = 8.5;
    let asistencia = 92.0;
    let presentes = 23;
    let tardanzas = 2;
    let faltas = 1;
    let progreso = 75.0;
    let entregadas = 9;
    let totales = 12;

    if (materiaId === 'm2' || materiaId === '2') {
      promedio = 5.8;
      asistencia = 76.5;
      presentes = 18;
      tardanzas = 1;
      faltas = 5;
      progreso = 58.3;
      entregadas = 7;
      totales = 12;
    } else if (materiaId === 'm5' || materiaId === '5') {
      promedio = 7.2;
      asistencia = 82.0;
      presentes = 20;
      tardanzas = 3;
      faltas = 3;
      progreso = 66.6;
      entregadas = 8;
      totales = 12;
    }

    const diffProm = Math.round((promedio - 8.1) * 100) / 100;
    const diffAsist = Math.round((asistencia - 88.0) * 100) / 100;

    let estado_riesgo: 'EXCELENTE' | 'REGULAR' | 'RIESGO_POR_FALTAS' = 'EXCELENTE';
    let mensaje_alerta = 'Cumples satisfactoriamente con el porcentaje de asistencia requerido (mínimo 80%).';

    if (asistencia < 80.0) {
      estado_riesgo = 'RIESGO_POR_FALTAS';
      mensaje_alerta = '¡Alerta! Tu asistencia es menor al 80%. Estás en riesgo de perder derecho a examen final.';
    } else if (asistencia < 90.0) {
      estado_riesgo = 'REGULAR';
      mensaje_alerta = 'Cumples con el porcentaje mínimo requerido de asistencia, pero procura no faltar más.';
    }

    return {
      alumno_id: this.alumnoId(),
      materia_id: materiaId,
      periodo_activo: 'PRIMAVERA 2026',
      calificaciones_kpi: {
        promedio_real: promedio,
        promedio_redondeado: Math.round(promedio),
        comparativa_grupo: {
          promedio_grupo: 8.1,
          diferencia: diffProm,
          mensaje: diffProm >= 0
            ? `Tu promedio se encuentra ${diffProm} puntos por encima de la media grupal.`
            : `Tu promedio se encuentra ${Math.abs(diffProm)} puntos por debajo de la media grupal.`
        }
      },
      asistencia_kpi: {
        porcentaje_asistencia: asistencia,
        total_presentes: presentes,
        total_retardos: tardanzas,
        total_faltas: faltas,
        comparativa_grupo: {
          tasa_asistencia_grupo: 88.0,
          diferencia: diffAsist,
          mensaje: diffAsist >= 0
            ? `Tu asistencia es un ${diffAsist}% superior a la media de tu grupo.`
            : `Tu asistencia es un ${Math.abs(diffAsist)}% inferior a la media de tu grupo.`
        },
        estado_riesgo,
        mensaje_alerta
      },
      progreso_academico: {
        actividades_entregadas: entregadas,
        actividades_totales: totales,
        porcentaje_completado: progreso
      }
    };
  }

  regresar() {
    this.router.navigate(['/alumno/materias']);
  }
}
