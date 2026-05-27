import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { QRCodeComponent } from 'angularx-qrcode';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { InputTextModule } from 'primeng/inputtext';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../../core/services/auth.service';
import { AsistenciasService } from '../../../core/services/asistencias.service';

@Component({
  selector: 'app-qr-code',
  standalone: true,
  imports: [
    CommonModule, FormsModule, QRCodeComponent,
    ButtonModule, TagModule, ToastModule, InputTextModule
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

  // Estado
  sesionId = signal<string>('');
  qrData = signal<string>('');
  secondsLeft = signal<number>(this.DURATION);
  cargando = signal<boolean>(false);
  sesionActiva = signal<boolean>(false);

  readonly userName = computed(() => this.authService.currentUser()?.nombre ?? 'Alumno');
  readonly avatarLabel = computed(() => {
    const n = this.userName();
    const parts = n.split(' ');
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : n.substring(0, 2).toUpperCase();
  });

  readonly countdownPct = computed(() => (this.secondsLeft() / this.DURATION) * 100);
  readonly dashOffset = computed(() => {
    const pct = 1 - (this.secondsLeft() / this.DURATION);
    return pct * 169.6;
  });

  ngOnInit() {}

  activarSesion() {
    if (!this.sesionId()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Campo requerido',
        detail: 'Ingresa el ID de la sesión activa',
        life: 3000
      });
      return;
    }
    this.sesionActiva.set(true);
    this.generarQR();
    this.startCountdown();
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
          detail: err.error?.message || 'La sesión no existe o ya cerró',
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
    this.messageService.add({
      severity: 'info',
      summary: 'QR renovado',
      detail: 'Tu código de asistencia ha sido actualizado',
      life: 2000
    });
  }

  refreshQr() {
    this.rotate();
    this.secondsLeft.set(this.DURATION);
  }

  desactivar() {
    this.sesionActiva.set(false);
    this.qrData.set('');
    this.sesionId.set('');
    this.stopCountdown();
  }

  ngOnDestroy() {
    this.stopCountdown();
  }
}
