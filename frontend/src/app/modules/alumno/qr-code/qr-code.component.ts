import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { QRCodeComponent } from 'angularx-qrcode';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-qr-code',
  standalone: true,
  imports: [CommonModule, QRCodeComponent, ButtonModule, TagModule, ToastModule],
  providers: [MessageService],
  templateUrl: './qr-code.component.html',
  styleUrls: ['./qr-code.component.scss']
})
export class QrCodeComponent implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  private messageService = inject(MessageService);

  private intervalId: any = null;
  private readonly DURATION = 60;

  secondsLeft = signal(this.DURATION);

  readonly userName = computed(() => this.authService.currentUser()?.nombre ?? 'Alumno');
  readonly avatarLabel = computed(() => {
    const n = this.userName();
    const parts = n.split(' ');
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : n.substring(0, 2).toUpperCase();
  });

  readonly userId = computed(() => this.authService.currentUser()?.id ?? 'unknown');
  readonly shortId = computed(() => this.userId().substring(0, 12) + '...');

  // QR data = alumnoId|timestamp — se rota cada ciclo
  private qrTimestamp = signal(Date.now());
  readonly qrData = computed(() => `${this.userId()}|${this.qrTimestamp()}`);

  readonly countdownPct = computed(() => (this.secondsLeft() / this.DURATION) * 100);

  // SVG ring: circumference = 2π * 27 ≈ 169.6
  readonly dashOffset = computed(() => {
    const pct = 1 - (this.secondsLeft() / this.DURATION);
    return pct * 169.6;
  });

  readonly steps = [
    { num: 1, title: 'Abre esta pantalla', desc: 'Navega a "Mi QR" en el menú lateral' },
    { num: 2, title: 'Muestra el código', desc: 'Presenta la pantalla al docente' },
    { num: 3, title: 'El docente escanea', desc: 'Apunta la cámara del escáner al QR' },
    { num: 4, title: 'Asistencia registrada', desc: 'Recibirás confirmación inmediata' },
  ];

  readonly materiasHoy = [
    { nombre: 'Desarrollo de Sistemas Distribuidos', hora: '08:00', color: '#F59E0B' },
    { nombre: 'Redes de Computadoras',              hora: '10:00', color: '#06B6D4' },
  ];

  ngOnInit() {
    this.startCountdown();
  }

  private startCountdown() {
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

  private rotate() {
    this.qrTimestamp.set(Date.now());
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

  ngOnDestroy() {
    if (this.intervalId) clearInterval(this.intervalId);
  }
}
