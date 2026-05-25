import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface UserProfile {
  id: string;
  nombre: string;
  email: string;
  role: string;
  activo: boolean;
  requires_password_change: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  requires_password_change: boolean;
  user: UserProfile;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrls.auth;

  // ── Signals ──────────────────────────────────────────────
  private tokenSignal = signal<string | null>(localStorage.getItem('access_token'));
  private refreshTokenSignal = signal<string | null>(localStorage.getItem('refresh_token'));
  private roleSignal = signal<string | null>(localStorage.getItem('role'));
  private userSignal = signal<UserProfile | null>(
    JSON.parse(localStorage.getItem('user') || 'null')
  );

  // ── Computed (public, read-only) ─────────────────────────
  readonly isLoggedIn = computed(() => !!this.tokenSignal());
  readonly currentUser = computed(() => this.userSignal());
  readonly currentRole = computed(() => this.roleSignal());

  // ── Accessors ────────────────────────────────────────────
  getToken(): string | null {
    return this.tokenSignal();
  }

  getUserRole(): string {
    return this.roleSignal() || '';
  }

  isAuthenticated(): boolean {
    return this.isLoggedIn();
  }

  // ── Login ────────────────────────────────────────────────
  login(credentials: { email: string; password: string }): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.baseUrl}/auth/login/`, credentials).pipe(
      tap((res) => {
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('refresh_token', res.refresh_token);
        localStorage.setItem('role', res.user.role);
        localStorage.setItem('user', JSON.stringify(res.user));

        this.tokenSignal.set(res.access_token);
        this.refreshTokenSignal.set(res.refresh_token);
        this.roleSignal.set(res.user.role);
        this.userSignal.set(res.user);
      })
    );
  }

  // ── Logout ───────────────────────────────────────────────
  logout(): void {
    const refreshToken = this.refreshTokenSignal();

    // Intentar invalidar el refresh token en el backend (blacklist)
    if (refreshToken) {
      this.http
        .post(`${this.baseUrl}/auth/logout/`, { refresh: refreshToken })
        .subscribe({ error: () => {} }); // fire-and-forget
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('role');
    localStorage.removeItem('user');

    this.tokenSignal.set(null);
    this.refreshTokenSignal.set(null);
    this.roleSignal.set(null);
    this.userSignal.set(null);
  }

  // ── Change Password (first login) ───────────────────────
  changePassword(data: {
    old_password: string;
    new_password: string;
    new_password_confirm: string;
  }): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.baseUrl}/auth/change-password/`,
      data
    );
  }

  // ── Forgot Password ─────────────────────────────────────
  forgotPassword(email: string): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.baseUrl}/auth/forgot-password/`,
      { email }
    );
  }

  // ── Reset Password (from email link) ────────────────────
  resetPassword(data: {
    uid: string;
    token: string;
    new_password: string;
  }): Observable<{ message: string }> {
    return this.http.post<{ message: string }>(
      `${this.baseUrl}/auth/reset-password/`,
      data
    );
  }

  // ── Refresh Token ────────────────────────────────────────
  refreshToken(): Observable<{ access: string }> {
    const refresh = this.refreshTokenSignal();
    return this.http
      .post<{ access: string }>(`${this.baseUrl}/auth/token/refresh/`, { refresh })
      .pipe(
        tap((res) => {
          localStorage.setItem('access_token', res.access);
          this.tokenSignal.set(res.access);
        })
      );
  }

  // ── Get Profile ──────────────────────────────────────────
  getMe(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.baseUrl}/auth/me/`);
  }

  // ── Get Dashboard Route by Role ──────────────────────────
  getDashboardRoute(): string {
    const role = this.getUserRole().toLowerCase();
    switch (role) {
      case 'admin':   return '/admin/dashboard';
      case 'docente': return '/docente/dashboard';
      case 'alumno':  return '/alumno/dashboard';
      default:        return '/auth/login';
    }
  }
}
