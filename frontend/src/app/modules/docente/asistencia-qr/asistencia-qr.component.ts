import {
  Component, OnInit, OnDestroy, inject, signal, ElementRef, ViewChild, NgZone
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { TagModule } from 'primeng/tag';
import { InputTextModule } from 'primeng/inputtext';
import { ProgressBarModule } from 'primeng/progressbar';
import { MessageService } from 'primeng/api';
import { AsistenciasService, Sesion } from '../../../core/services/asistencias.service';
import jsQR from 'jsqr';

type ScanStatus = 'idle' | 'scanning' | 'success' | 'error';

@Component({
  selector: 'app-asistencia-qr',
  standalone: true,
  imports: [
    CommonModule, FormsModule, ButtonModule, ToastModule,
    TagModule, InputTextModule, ProgressBarModule
  ],
  providers: [MessageService],
  templateUrl: './asistencia-qr.component.html',
  styleUrls: ['./asistencia-qr.component.scss']
})
export class AsistenciaQrComponent implements OnInit, OnDestroy {
  @ViewChild('videoEl') videoEl!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasEl') canvasEl!: ElementRef<HTMLCanvasElement>;

  private messageService = inject(MessageService);
  private ngZone = inject(NgZone);
  private asistenciasService = inject(AsistenciasService);

  // Estado de la sesión
  sesionActiva = signal<Sesion | null>(null);
  materiaId = signal<string>('');
  timerInterval: any = null;
  segundosRestantes = signal<number>(0);

  // Estado del escáner
  status = signal<ScanStatus>('idle');
  scanHistory = signal<{ matricula: string; estado: string; timestamp: string }[]>([]);

  private stream: MediaStream | null = null;
  private animationId: number | null = null;

  ngOnInit() {}

  // ── Sesión ───────────────────────────────────────────────

  iniciarSesion() {
    if (!this.materiaId()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Campo requerido',
        detail: 'Ingresa el ID de la materia',
        life: 3000
      });
      return;
    }

    this.asistenciasService.iniciarSesion(this.materiaId()).subscribe({
      next: (res) => {
        if (res.success) {
          this.sesionActiva.set(res.data);
          this.segundosRestantes.set(res.data.segundos_restantes);
          this.startTimer();
          this.messageService.add({
            severity: 'success',
            summary: 'Sesión iniciada',
            detail: 'Puedes comenzar a escanear QR',
            life: 3000
          });
        }
      },
      error: (err) => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: err.error?.message || 'No se pudo iniciar la sesión',
          life: 4000
        });
      }
    });
  }

  cerrarSesion() {
    const sesion = this.sesionActiva();
    if (!sesion) return;

    this.asistenciasService.cerrarSesion(sesion.id).subscribe({
      next: (res) => {
        if (res.success) {
          this.sesionActiva.set(null);
          this.stopTimer();
          this.stopScanning();
          this.messageService.add({
            severity: 'info',
            summary: 'Sesión cerrada',
            detail: 'La sesión de asistencia ha sido cerrada',
            life: 3000
          });
        }
      },
      error: () => {
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo cerrar la sesión',
          life: 3000
        });
      }
    });
  }

  private startTimer() {
    this.timerInterval = setInterval(() => {
      this.segundosRestantes.update(s => {
        if (s <= 1) {
          this.sesionActiva.set(null);
          this.stopTimer();
          this.stopScanning();
          this.messageService.add({
            severity: 'warn',
            summary: 'Sesión expirada',
            detail: 'La sesión de 10 minutos ha terminado',
            life: 4000
          });
          return 0;
        }
        return s - 1;
      });
    }, 1000);
  }

  private stopTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  // ── Escáner QR ───────────────────────────────────────────

  async startScanning() {
    if (!this.sesionActiva()) {
      this.messageService.add({
        severity: 'warn',
        summary: 'Sin sesión activa',
        detail: 'Primero inicia una sesión de asistencia',
        life: 3000
      });
      return;
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      this.videoEl.nativeElement.srcObject = this.stream;
      await this.videoEl.nativeElement.play();
      this.status.set('scanning');
      this.tick();
    } catch (err) {
      this.messageService.add({
        severity: 'error',
        summary: 'Sin acceso a cámara',
        detail: 'Permite el acceso a la cámara para escanear QR',
        life: 4000
      });
    }
  }

  private tick() {
    const video = this.videoEl?.nativeElement;
    const canvas = this.canvasEl?.nativeElement;
    if (!video || !canvas || this.status() !== 'scanning') return;

    const ctx = canvas.getContext('2d')!;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert'
    });

    if (code) {
      this.ngZone.run(() => this.handleQRCode(code.data));
      return;
    }

    this.animationId = requestAnimationFrame(() => this.tick());
  }

  private handleQRCode(qrToken: string) {
    this.stopStream();
    const sesion = this.sesionActiva();
    if (!sesion) return;

    this.asistenciasService.registrarAsistencia(qrToken, sesion.id).subscribe({
      next: (res) => {
        if (res.success) {
          this.status.set('success');
          const timestamp = new Date().toLocaleTimeString('es-MX', {
            hour: '2-digit', minute: '2-digit'
          });
          this.scanHistory.update(h => [{
            matricula: res.data.matricula,
            estado: res.data.estado,
            timestamp
          }, ...h]);

          this.messageService.add({
            severity: 'success',
            summary: 'Asistencia registrada',
            detail: `${res.data.matricula} — ${res.data.estado}`,
            life: 3000
          });

          // Actualizar contadores de la sesión
          this.asistenciasService.getAsistenciasHoy(sesion.materia_id).subscribe(r => {
            if (r.success && r.data.length > 0) {
              this.sesionActiva.set(r.data[0]);
            }
          });

          setTimeout(() => this.resetScanner(), 2500);
        }
      },
      error: (err) => {
        this.status.set('error');
        this.messageService.add({
          severity: 'error',
          summary: 'Error al registrar',
          detail: err.error?.message || 'QR inválido o expirado',
          life: 3000
        });
        setTimeout(() => this.resetScanner(), 2000);
      }
    });
  }

  stopScanning() {
    this.stopStream();
    this.status.set('idle');
  }

  resetScanner() {
    this.stopStream();
    this.status.set('idle');
    setTimeout(() => this.startScanning(), 500);
  }

  private stopStream() {
    if (this.animationId) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
    this.stream?.getTracks().forEach(t => t.stop());
    this.stream = null;
  }

  ngOnDestroy() {
    this.stopStream();
    this.stopTimer();
  }
}
