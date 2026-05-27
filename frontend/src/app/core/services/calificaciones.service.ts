import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// Interfaces para Ponderaciones
export interface PonderacionInput {
  nombre: string; // Mapea a nombre_categoria en el backend
  porcentaje: number;
  orden?: number;
  activa?: boolean;
}

export interface CategoriaPonderacion {
  id: string;
  nombre: string;
  porcentaje: number;
}

export interface PonderacionResponse {
  materia_id: string;
  bloqueada: boolean;
  categorias: CategoriaPonderacion[];
}

// Interfaces para Actividades
export interface Actividad {
  id: string;
  ponderacion_id: string;
  nombre: string;
  descripcion?: string;
  orden: number;
  estado: string;
  fecha_vencimiento?: string;
  created_at: string;
  updated_at: string;
}

export interface ActividadInput {
  materia_id: string;
  ponderacion_id: string;
  nombre: string;
  descripcion?: string;
  estado?: string;
}

// Interfaces para Calificaciones
export interface CalificacionInput {
  actividad_id: string;
  alumno_id: string;
  valor: number;
  observacion?: string;
}

export interface CalificacionNota {
  actividad_id: string;
  valor: number;
}

// Interfaces para el Concentrado de Calificaciones (Acta)
export interface ActividadHeader {
  actividad_id: string;
  actividad_nombre: string;
}

export interface CategoriaHeader {
  nombre_categoria: string;
  porcentaje: number;
  actividades: ActividadHeader[];
}

export interface AlumnoConcentrado {
  alumno_id: string;
  alumno_matricula: string;
  alumno_nombre: string;
  promedio_real: number;
  promedio_redondeado: number;
  calificaciones: CalificacionNota[];
}

export interface ConcentradoResponse {
  materia_id: string;
  materia_nombre: string;
  categorias: CategoriaHeader[];
  alumnos: AlumnoConcentrado[];
}

// Interfaces para Periodos y Materias
export interface PeriodoActivo {
  id: string;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  plan_estudios: string;
  activo: boolean;
}

export interface HorarioMateria {
  id: string;
  dia: string;
  hora_inicio: string;
  hora_fin: string;
  salon: string;
  es_virtual: boolean;
}

export interface MateriaReal {
  id: string;
  nrc: string;
  clave: string;
  nombre: string;
  seccion: string;
  docente_nombre: string;
  docente_id: string;
  periodo: string;
  estado: string;
  horarios: HorarioMateria[];
}

@Injectable({
  providedIn: 'root',
})
export class CalificacionesService {
  private http = inject(HttpClient);
  
  private baseUrlCalificaciones = environment.apiUrls.calificaciones;
  private baseUrlPeriodos = environment.apiUrls.periodos;

  // ── Endpoints del MS-2 Periodos (Consumo sin modificaciones) ────────────────

  /** Obtiene el periodo académico activo */
  getPeriodoActivo(): Observable<PeriodoActivo> {
    return this.http.get<PeriodoActivo>(`${this.baseUrlPeriodos}/api/periodos/activo/`);
  }

  /** Obtiene las materias asociadas a un periodo y opcionalmente a un docente */
  getMaterias(params: { periodo_id?: string; docente_id?: string }): Observable<any> {
    return this.http.get<any>(`${this.baseUrlPeriodos}/api/materias/`, { params: params as any });
  }

  // ── Endpoints de Ponderaciones (MS-4) ────────────────────────────────────────

  /** Obtiene el esquema de ponderaciones configurado para una materia */
  getPonderaciones(materiaId: string): Observable<PonderacionResponse> {
    return this.http.get<PonderacionResponse>(`${this.baseUrlCalificaciones}/api/ponderaciones/${materiaId}/`);
  }

  /** Configura de forma masiva las ponderaciones para una materia */
  crearPonderaciones(materiaId: string, categorias: PonderacionInput[]): Observable<any> {
    return this.http.post<any>(`${this.baseUrlCalificaciones}/api/ponderaciones/${materiaId}/`, {
      categorias,
    });
  }

  // ── Endpoints de Actividades (MS-4) ──────────────────────────────────────────

  /** Crea una nueva actividad evaluable asignada a una ponderación */
  crearActividad(input: ActividadInput): Observable<any> {
    return this.http.post<any>(`${this.baseUrlCalificaciones}/api/actividades/`, input);
  }

  /** Elimina una actividad evaluable por su ID */
  eliminarActividad(actividadId: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrlCalificaciones}/api/actividades/${actividadId}/`);
  }

  // ── Endpoints de Calificaciones (MS-4) ────────────────────────────────────────

  /** Registra o actualiza de forma manual la calificación individual de un alumno */
  actualizarCalificacion(input: CalificacionInput): Observable<any> {
    return this.http.post<any>(`${this.baseUrlCalificaciones}/api/calificaciones/`, input);
  }

  /** Importa calificaciones de alumnos masivamente desde una hoja de Excel exportada de Teams */
  importarCalificaciones(materiaId: string, criterioEval: string, archivo: File): Observable<any> {
    const formData = new FormData();
    formData.append('materia_id', materiaId);
    formData.append('criterio_evaluacion', criterioEval);
    formData.append('archivo', archivo);
    return this.http.post<any>(`${this.baseUrlCalificaciones}/api/calificaciones/importar/`, formData);
  }

  // ── Endpoints de Concentrado (MS-4) ───────────────────────────────────────────

  /** Obtiene el acta concentrada (promedios ponderados e individuales) de una materia */
  getConcentrado(materiaId: string): Observable<ConcentradoResponse> {
    return this.http.get<ConcentradoResponse>(`${this.baseUrlCalificaciones}/api/concentrado/${materiaId}/`);
  }

  /** Obtiene las estadísticas y desglose detallado de calificaciones de un alumno en una materia (MS-4) */
  getEstadisticasAlumno(alumnoId: string, materiaId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrlCalificaciones}/api/estadisticas/alumno/${alumnoId}/materia/${materiaId}/`);
  }
}
