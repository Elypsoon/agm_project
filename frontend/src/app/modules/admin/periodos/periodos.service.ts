import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface Periodo {
  id: string;
  nombre: string;
  fecha_inicio: string;
  fecha_fin: string;
  plan_estudios: string;
  campus?: string;
  activo: boolean;
  materias?: unknown[];
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
  plan_estudios: string;
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
    return this.http.post<Periodo>(`${this.baseUrl}/periodos/`, payload);
  }

  deletePeriodo(periodoId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/periodos/${periodoId}/`);
  }

  activatePeriodo(periodoId: string): Observable<Periodo> {
    return this.http.put<Periodo>(`${this.baseUrl}/periodos/${periodoId}/activar/`, {});
  }

  importPdf(periodoId: string, file: File): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post(`${this.baseUrl}/materias/importar-pdf/${periodoId}/`, formData);
  }
}
