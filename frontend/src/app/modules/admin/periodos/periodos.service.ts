import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Horario {
  id: string;
  dia: string;
  hora_inicio: string;
  hora_fin: string | null;
  salon: string;
  es_virtual: boolean;
}

export interface Materia {
  id: string;
  nrc: string;
  clave: string;
  nombre: string;
  seccion: string;
  docente_nombre: string | null;
  estado: string;
  campus: string;
  plan_estudios: string;
  horarios?: Horario[];
}

export interface Periodo {
  id: string;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: 'pendiente' | 'activo' | 'finalizada';
  materias?: Materia[];
}

interface PaginatedPeriodosResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Periodo[];
}

export interface CreatePeriodoPayload {
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
}

@Injectable({ providedIn: 'root' })
export class PeriodosService {
  private http = inject(HttpClient);
  private baseUrl = `${environment.apiUrls.periodos}/api`;

  getPeriodos(): Observable<Periodo[]> {
    return this.http
      .get<PaginatedPeriodosResponse>(`${this.baseUrl}/periodos/`)
      .pipe(map((response) => response.results ?? []));
  }

  getPeriodoById(periodoId: string): Observable<Periodo> {
    return this.http.get<Periodo>(`${this.baseUrl}/periodos/${periodoId}/`);
  }

  getActivePeriodo(): Observable<Periodo> {
    return this.http.get<Periodo>(`${this.baseUrl}/periodos/activo/`);
  }

  createPeriodo(payload: CreatePeriodoPayload): Observable<Periodo> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    return this.http.post<Periodo>(
      `${this.baseUrl}/periodos/`,
      payload,
      { headers }
    );
  }

  deletePeriodo(periodoId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/periodos/${periodoId}/`);
  }

  activatePeriodo(periodoId: string): Observable<Periodo> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    return this.http.put<Periodo>(
      `${this.baseUrl}/periodos/${periodoId}/activar/`,
      {},
      { headers }
    );
  }

  deactivatePeriodo(periodoId: string): Observable<Periodo> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    return this.http.put<Periodo>(
      `${this.baseUrl}/periodos/${periodoId}/desactivar/`,
      {},
      { headers }
    );
  }

  updatePeriodo(periodoId: string, payload: Partial<CreatePeriodoPayload>): Observable<Periodo> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    return this.http.put<Periodo>(
      `${this.baseUrl}/periodos/${periodoId}/`,
      payload,
      { headers }
    );
  }

  updateMateria(materiaId: string, payload: any): Observable<Materia> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/json'
    });
    return this.http.put<Materia>(
      `${this.baseUrl}/materias/${materiaId}/`,
      payload,
      { headers }
    );
  }

  importPdf(periodoId: string, file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}/materias/importar-pdf/${periodoId}/`, formData);
  }
}
