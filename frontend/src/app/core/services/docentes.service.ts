import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Docente {
  id: string;
  nombre_completo: string;
  correo_institucional: string;
  cubiculo: string | null;
  activo: boolean;
  fecha_registro: string;
}

export interface DocenteListResponse {
  success: boolean;
  data: {
    docentes: Docente[];
    total: number;
    page: number;
    limit: number;
  };
  message: string;
}

export interface DocenteDetalleResponse {
  success: boolean;
  data: Docente;
  message: string;
}

export interface ImportResponse {
  success: boolean;
  message: string;
  data?: {
    nuevos: number;
    actualizados: number;
    errores: number;
  };
}

@Injectable({ providedIn: 'root' })
export class DocentesService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrls.alumnos}/api/docentes`;

  /** GET /api/docentes/ — Lista con búsqueda y paginación */
  getDocentes(params?: { search?: string; page?: number; limit?: number }): Observable<DocenteListResponse> {
    let httpParams = new HttpParams();
    if (params?.search) httpParams = httpParams.set('search', params.search);
    if (params?.page)   httpParams = httpParams.set('page', String(params.page));
    if (params?.limit)  httpParams = httpParams.set('limit', String(params.limit));
    return this.http.get<DocenteListResponse>(this.baseUrl + '/', { params: httpParams });
  }

  /** GET /api/docentes/:id/ — Detalle de un docente */
  getDocente(id: string): Observable<DocenteDetalleResponse> {
    return this.http.get<DocenteDetalleResponse>(`${this.baseUrl}/${id}/`);
  }

  /** POST /api/docentes/importar/ — Importar desde PDF */
  importarDocentes(archivo: File): Observable<ImportResponse> {
    const formData = new FormData();
    formData.append('archivo', archivo);
    return this.http.post<ImportResponse>(`${this.baseUrl}/importar/`, formData);
  }

  createDocente(payload: { nombre_completo: string; correo_institucional: string; cubiculo: string }): Observable<any> {
    return this.http.post<any>(`${this.baseUrl}/`, payload);
  }

  updateDocente(id: string, payload: Partial<{ nombre_completo: string; correo_institucional: string; cubiculo: string }>): Observable<any> {
    return this.http.put<any>(`${this.baseUrl}/${id}/`, payload);
  }

  deleteDocente(id: string): Observable<any> {
    return this.http.delete<any>(`${this.baseUrl}/${id}/`);
  }
}
