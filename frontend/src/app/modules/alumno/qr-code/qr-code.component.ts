import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { QRCodeComponent } from 'angularx-qrcode';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { SelectModule } from 'primeng/select';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../../core/services/auth.service';
import { AsistenciasService, MateriaResumen } from '../../../core/services/asistencias.service';

@Component({
  selector: 'app-qr-code',
  standalone: true,
  imports: [
    CommonModule, FormsModule, QRCodeComponent,
    ButtonModule, TagModule, ToastModule, SelectModule
  ],
  providers: [MessageService],
  templateUrl: './qr-code.component.html',
  styleUrls: ['./qr-code.component.scss']
})
export class QrCodeComponent implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  private asistenciasService = inject(AsistenciasService);
  private messageService = inject(MessageService);

  private intervalId: any = null;
  private readonly DURATION = 30;

  // Estado materias
  materias = signal<MateriaResumen[]>([]);
  materiaSeleccionada = signal<MateriaResumen | null>(null);
  cargandoMaterias = signal<boolean>(false);
  modoManual = signal<boolean>(false);
  sesionIdManual = signal<string>('');

  // Estado QR
  sesionId = signal<string>('');
  qrData = signal<string>('');
  secondsLeft = signal<number>(this.DURATION);
  cargando = signal<boolean>(false);
  sesionActiva = signal<boolean>(false);
  buscandoSesion = signal<boolean>(false);

  readonly userName = computed(() => this.authService.currentUser()?.nombre ?? 'Alumno');
  readonly avatarLabel = computed(() => {
    const n = this.userName();
    const parts = n.split(' ');
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : n.substring(0, 2).toUpperCase();
  });

  readonly dashOffset = computed(() => {
    const pct = 1 - (this.secondsLeft() / this.DURATION);
    return pct * 169.6;
  });

  ngOnInit() {
    this.cargarMaterias();
  }

  cargarMaterias() {
    this.cargandoMaterias.set(true);
    this.asistenciasService.getMisMaterias().subscribe({
      next: (res) => {
        this.cargandoMaterias.set(false);
        if (res.success && res.data.length > 0) {
          this.materias.set(res.data);
          this.modoManual.set(false);
        } else {
          this.modoManual.set(true);
        }
      },
      error: () => {
        this.cargandoMaterias.set(false);
        this.modoManual.set(true);
      }
    });
  }

  activarSesion() {
    if (this.modoManual()) {
      if (!this.sesionIdManual()) {
        this.messageService.add({
          severity: 'warn',
          summary: 'Campo requerido',
          detail: 'Ingresa el ID de la sesión',
          life: 3000
        });
        return;
      }
      this.sesionId.set(this.sesionIdManual());
      this.sesionActiva.set(true);
      this.generarQR();
      this.startCountdown();
      return;
    }

    if (!this.materiaSeleccionada()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Campo requerido',
        detail: 'Selecciona una materia',
        life: 3000
      });
      return;
    }

    // Buscar sesión activa para la materia seleccionada
    this.buscandoSesion.set(true);
    this.asistenciasService.getSesionActiva(this.materiaSeleccionada()!.id).subscribe({
      next: (res) => {
        this.buscandoSesion.set(false);
        if (res.success) {
          this.sesionId.set(res.data.id);
          this.sesionActiva.set(true);
          this.generarQR();
          this.startCountdown();
        }
      },
      error: (err) => {
        this.buscandoSesion.set(false);
        this.messageService.add({
          severity: 'warn',
          summary: 'Sin sesión activa',
          detail: err.message || 'No hay sesión activa para esta materia',
          life: 4000
        });
      }
    });
  }

  private generarQR() {
    this.cargando.set(true);
    this.asistenciasService.generarQRToken(this.sesionId()).subscribe({
      next: (res) => {
        if (res.success) {
          this.qrData.set(res.data.qr_token);
          this.cargando.set(false);
        }
      },
      error: (err) => {
        this.cargando.set(false);
        this.sesionActiva.set(false);
        this.stopCountdown();
        this.messageService.add({
          severity: 'error',
          summary: 'Sesión inválida',
          detail: err.message || 'La sesión no existe o ya cerró',
          life: 4000
        });
      }
    });
  }

  private startCountdown() {
    this.secondsLeft.set(this.DURATION);
    this.intervalId = setInterval(() => {
      this.secondsLeft.update(s => {
        if (s <= 1) {
          this.rotate();
          return this.DURATION;
        }
        return s - 1;
      });
    }, 1000);
  }

  private stopCountdown() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  private rotate() {
    this.generarQR();
  }

  refreshQr() {
    this.rotate();
    this.secondsLeft.set(this.DURATION);
  }

  desactivar() {
    this.sesionActiva.set(false);
    this.qrData.set('');
    this.sesionId.set('');
    this.materiaSeleccionada.set(null);
    this.sesionIdManual.set('');
    this.stopCountdown();
  }

  ngOnDestroy() {
    this.stopCountdown();
  }
}
