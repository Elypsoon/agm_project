import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Inscripcion {
  id: string;
  materia_id: string;
  materia_nombre: string;
  docente_nombre?: string;
  fecha_inscripcion: string;
  activo: boolean;
}

export interface Alumno {
  id: string;
  nombre_completo: string;
  correo: string;
  matricula: string;
  carrera: string;
  semestre: number | null;
  activo: boolean;
  fecha_registro: string;
}

export interface AlumnoDetalle extends Alumno {
  inscripciones: Inscripcion[];
}

export interface AlumnoListResponse {
  success: boolean;
  data: {
    alumnos: Alumno[];
    total: number;
    page: number;
    limit: number;
  };
  message: string;
}

export interface AlumnoDetalleResponse {
  success: boolean;
  data: AlumnoDetalle;
  message: string;
}

export interface ImportResponse {
  success: boolean;
  message: string;
  data?: {
    alumnos_nuevos: number;
    inscripciones_nuevas: number;
    ya_inscritos: number;
    total_extraidos: number;
    errores: number;
  };
}

@Injectable({ providedIn: 'root' })
export class AlumnosService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrls.alumnos}/api/alumnos`;

  /** GET /api/alumnos/ — Lista global con búsqueda y paginación */
  getAlumnos(params?: { search?: string; page?: number; limit?: number }): Observable<AlumnoListResponse> {
    let httpParams = new HttpParams();
    if (params?.search) httpParams = httpParams.set('search', params.search);
    if (params?.page)   httpParams = httpParams.set('page', String(params.page));
    if (params?.limit)  httpParams = httpParams.set('limit', String(params.limit));
    return this.http.get<AlumnoListResponse>(this.baseUrl + '/', { params: httpParams });
  }

  /** GET /api/alumnos/:id/ — Detalle con inscripciones */
  getAlumno(id: string): Observable<AlumnoDetalleResponse> {
    return this.http.get<AlumnoDetalleResponse>(`${this.baseUrl}/${id}/`);
  }

  /** GET /api/alumnos/materia/:materiaId/ — Alumnos inscritos activos en una materia */
  getAlumnosByMateria(
    materiaId: string,
    params?: { search?: string; page?: number; limit?: number }
  ): Observable<AlumnoListResponse> {
    let httpParams = new HttpParams();
    if (params?.search) httpParams = httpParams.set('search', params.search);
    if (params?.page)   httpParams = httpParams.set('page', String(params.page));
    if (params?.limit)  httpParams = httpParams.set('limit', String(params.limit));
    return this.http.get<AlumnoListResponse>(`${this.baseUrl}/materia/${materiaId}/`, { params: httpParams });
  }

  /** POST /api/alumnos/importar/:materiaId/ — Importar desde PDF */
  importarAlumnos(materiaId: string, archivo: File): Observable<ImportResponse> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<ImportResponse>(`${this.baseUrl}/importar/${materiaId}/`, formData);
  }

  /** DELETE /api/alumnos/:id/baja/?materia_id= — Dar de baja */
  darDeBaja(alumnoId: string, materiaId: string): Observable<any> {
    const params = new HttpParams().set('materia_id', materiaId);
    return this.http.delete(`${this.baseUrl}/${alumnoId}/baja/`, { params });
  }
}
