import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Observable, map, switchMap, from, of } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface EstadisticasDocenteMateria {
  periodo_id: string;
  materia_id: string;
  materia_nombre: string;
  nrc: string;
  promedio_grupo: number;
  tasa_asistencia: number;
  tasa_aprobacion: number;
  total_alumnos: number;
  generado_en: string;
}

export interface EstadisticasDocenteResponse {
  success: boolean;
  message: string;
  data: EstadisticasDocenteMateria[];
}

export interface ComparativaGrupo {
  promedio_grupo: number;
  diferencia: number;
  mensaje: string;
}

export interface CalificacionesKPI {
  promedio_real: number;
  promedio_redondeado: number;
  comparativa_grupo: ComparativaGrupo;
}

export interface ComparativaAsistenciaGrupo {
  tasa_asistencia_grupo: number;
  diferencia: number;
  mensaje: string;
}

export interface AsistenciaKPI {
  porcentaje_asistencia: number;
  total_presentes: number;
  total_retardos: number;
  total_faltas: number;
  comparativa_grupo: ComparativaAsistenciaGrupo;
  estado_riesgo: 'EXCELENTE' | 'REGULAR' | 'RIESGO_POR_FALTAS';
  mensaje_alerta: string;
}

export interface ProgresoAcademico {
  actividades_entregadas: number;
  actividades_totales: number;
  porcentaje_completado: number;
}

export interface EstadisticasAlumnoMateria {
  alumno_id: string;
  materia_id: string;
  periodo_activo: string;
  calificaciones_kpi: CalificacionesKPI;
  asistencia_kpi: AsistenciaKPI;
  progreso_academico: ProgresoAcademico;
}

export interface EstadisticasAlumnoResponse {
  success: boolean;
  message: string;
  data: EstadisticasAlumnoMateria;
}

export interface ReporteResponse {
  isBlob?: boolean;
  blob?: Blob;
  filename?: string;
  async?: boolean;
  success?: boolean;
  message?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ReportesService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrls.reportes;

  /**
   * Obtiene el historial analítico del docente por materias impartidas.
   */
  obtenerEstadisticasDocente(docenteId: string): Observable<EstadisticasDocenteResponse> {
    return this.http.get<EstadisticasDocenteResponse>(`${this.baseUrl}/estadisticas/docente/${docenteId}/`);
  }

  /**
   * Obtiene las estadísticas analíticas de un alumno específico para una materia dada.
   */
  obtenerEstadisticasAlumno(alumnoId: string, materiaId: string): Observable<EstadisticasAlumnoResponse> {
    const params = new HttpParams().set('materia_id', materiaId);
    return this.http.get<EstadisticasAlumnoResponse>(`${this.baseUrl}/estadisticas/alumno/${alumnoId}/`, { params });
  }

  /**
   * Obtiene las estadísticas de rendimiento consolidadas de un grupo.
   */
  obtenerEstadisticasGrupo(materiaId: string): Observable<any> {
    return this.http.get<any>(`${this.baseUrl}/estadisticas/${materiaId}/`);
  }

  /**
   * Descarga de calificaciones de una materia. Maneja descarga síncrona o flujo en background.
   */
  descargarCalificaciones(materiaId: string, email: string, formato: string = 'pdf'): Observable<ReporteResponse> {
    const url = `${this.baseUrl}/calificaciones/${materiaId}/`;
    let params = new HttpParams().set('formato', formato);
    if (email) {
      params = params.set('email', email);
    }

    return this.http.get(url, {
      params,
      responseType: 'blob',
      observe: 'response'
    }).pipe(
      switchMap(response => this.parseResponse(response, `calificaciones_${materiaId}.${formato === 'xlsx' ? 'xlsx' : 'pdf'}`))
    );
  }

  /**
   * Descarga de asistencias de una materia. Maneja descarga síncrona o flujo en background.
   */
  descargarAsistencias(materiaId: string, email: string, formato: string = 'pdf'): Observable<ReporteResponse> {
    const url = `${this.baseUrl}/asistencias/${materiaId}/`;
    let params = new HttpParams().set('formato', formato);
    if (email) {
      params = params.set('email', email);
    }

    return this.http.get(url, {
      params,
      responseType: 'blob',
      observe: 'response'
    }).pipe(
      switchMap(response => this.parseResponse(response, `asistencias_${materiaId}.${formato === 'xlsx' ? 'xlsx' : 'pdf'}`))
    );
  }

  private parseResponse(response: HttpResponse<Blob>, defaultFilename: string): Observable<ReporteResponse> {
    const contentType = response.headers.get('content-type') || '';
    const body = response.body;

    if (!body) {
      return of({ success: false, message: 'Cuerpo de respuesta vacío' });
    }

    if (contentType.includes('application/json')) {
      return from(body.text()).pipe(
        map(text => {
          try {
            const json = JSON.parse(text);
            return {
              success: json.success,
              async: json.async,
              message: json.message
            };
          } catch (e) {
            return { success: false, message: 'Error al parsear la respuesta JSON' };
          }
        })
      );
    } else {
      let filename = defaultFilename;
      const disposition = response.headers.get('Content-Disposition');
      if (disposition) {
        const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
        if (matches && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      return of({
        isBlob: true,
        blob: body,
        filename: filename
      });
    }
  }
}
