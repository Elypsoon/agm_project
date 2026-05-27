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

export interface EstadisticasAlumnoMateria {
  alumno_id: string;
  materia_id: string;
  periodo_activo: string;
  calificaciones_kpi: {
    promedio_real: number;
    promedio_redondeado: number;
    comparativa_grupo: {
      promedio_grupo: number;
      diferencia: number;
      mensaje: string;
    };
  };
  asistencia_kpi: {
    porcentaje_asistencia: number;
    total_presentes: number;
    total_retardos: number;
    total_faltas: number;
    comparativa_grupo: {
      tasa_asistencia_grupo: number;
      diferencia: number;
      mensaje: string;
    };
    estado_riesgo: string;
    mensaje_alerta: string;
  };
  progreso_academico: {
    actividades_entregadas: number;
    actividades_totales: number;
    porcentaje_completado: number;
  };
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
  private baseUrl = `${environment.apiUrls.reportes}/api`;

  obtenerEstadisticasDocente(docenteId: string): Observable<{ success: boolean; data: EstadisticasDocenteMateria[]; message?: string }> {
    return this.http.get<{ success: boolean; data: EstadisticasDocenteMateria[]; message?: string }>(
      `${this.baseUrl}/estadisticas/docente/${docenteId}/`
    );
  }

  obtenerEstadisticasAlumno(alumnoId: string, materiaId: string): Observable<{ success: boolean; data: EstadisticasAlumnoMateria; message?: string }> {
    const params = new HttpParams().set('materia_id', materiaId);
    return this.http.get<{ success: boolean; data: EstadisticasAlumnoMateria; message?: string }>(
      `${this.baseUrl}/estadisticas/alumno/${alumnoId}/`,
      { params }
    );
  }

  descargarCalificaciones(materiaId: string, email: string, formato: string): Observable<ReporteResponse> {
    const params = new HttpParams().set('email', email).set('formato', formato);
    return this.http.get(`${this.baseUrl}/calificaciones/${materiaId}/`, {
      params,
      responseType: 'blob',
      observe: 'response'
    }).pipe(
      switchMap(response => this.parseResponse(response, `calificaciones_${materiaId}.${formato === 'xlsx' ? 'xlsx' : 'pdf'}`))
    );
  }

  descargarAsistencias(materiaId: string, email: string, formato: string): Observable<ReporteResponse> {
    const params = new HttpParams().set('email', email).set('formato', formato);
    return this.http.get(`${this.baseUrl}/asistencias/${materiaId}/`, {
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
