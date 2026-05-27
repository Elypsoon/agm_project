import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Sesion {
  id: string;
  materia_id: string;
  docente_id: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string | null;
  estado: 'activa' | 'cerrada';
  duracion_segundos: number;
  segundos_restantes: number;
  total_presentes: number;
  total_retardos: number;
  asistencias?: Asistencia[];
}

export interface Asistencia {
  id: string;
  sesion: string;
  alumno_id: string;
  materia_id: string;
  matricula: string;
  estado: 'presente' | 'retardo' | 'ausente';
  hora_registro: string;
}

export interface QRToken {
  qr_token: string;
  expira_en_segundos: number;
}

export interface MateriaResumen {
  id: string;
  nombre: string;
  nrc: string;
  seccion: string;
  estado: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message: string;
}

@Injectable({ providedIn: 'root' })
export class AsistenciasService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrls.asistencias;

  // ── Sesiones ────────────────────────────────────────────

  iniciarSesion(materia_id: string): Observable<ApiResponse<Sesion>> {
    return this.http.post<ApiResponse<Sesion>>(
      `${this.baseUrl}/sesiones/iniciar`,
      { materia_id }
    );
  }

  cerrarSesion(sesion_id: string): Observable<ApiResponse<Sesion>> {
    return this.http.delete<ApiResponse<Sesion>>(
      `${this.baseUrl}/sesiones/${sesion_id}/cerrar`
    );
  }

  // ── Asistencias ─────────────────────────────────────────

  registrarAsistencia(qr_token: string, sesion_id: string): Observable<ApiResponse<Asistencia>> {
    return this.http.post<ApiResponse<Asistencia>>(
      `${this.baseUrl}/asistencias/registrar`,
      { qr_token, sesion_id }
    );
  }

  getAsistenciasHoy(materia_id: string): Observable<ApiResponse<Sesion[]>> {
    return this.http.get<ApiResponse<Sesion[]>>(
      `${this.baseUrl}/asistencias/${materia_id}/hoy`
    );
  }

  getHistorial(materia_id: string, page = 1, limit = 10): Observable<ApiResponse<any>> {
    const params = new HttpParams()
      .set('page', page.toString())
      .set('limit', limit.toString());
    return this.http.get<ApiResponse<any>>(
      `${this.baseUrl}/asistencias/${materia_id}/historial`,
      { params }
    );
  }

  // ── QR ──────────────────────────────────────────────────

  generarQRToken(): Observable<ApiResponse<QRToken>> {
    return this.http.get<ApiResponse<QRToken>>(
      `${this.baseUrl}/asistencias/qr/generar`
    );
  }

  getMisMaterias(): Observable<ApiResponse<MateriaResumen[]>> {
    return this.http.get<ApiResponse<MateriaResumen[]>>(
      `${this.baseUrl}/materias/mis-materias`
    );
  }

  getSesionActiva(materia_id: string): Observable<ApiResponse<Sesion>> {
    const params = new HttpParams().set('materia_id', materia_id);
    return this.http.get<ApiResponse<Sesion>>(
      `${this.baseUrl}/sesiones/activa`,
      { params }
    );
  }

}
