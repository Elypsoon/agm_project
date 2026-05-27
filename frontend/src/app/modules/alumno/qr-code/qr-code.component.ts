import { Component, OnInit, OnDestroy, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { QRCodeComponent } from 'angularx-qrcode';
import { ButtonModule } from 'primeng/button';
import { TagModule } from 'primeng/tag';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { AuthService } from '../../../core/services/auth.service';
import { AsistenciasService } from '../../../core/services/asistencias.service';

@Component({
  selector: 'app-qr-code',
  standalone: true,
  imports: [
    CommonModule, QRCodeComponent,
    ButtonModule, TagModule, ToastModule
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

  qrData = signal<string>('');
  secondsLeft = signal<number>(this.DURATION);
  cargando = signal<boolean>(false);

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
    this.generarQR();
    this.startCountdown();
  }

  private generarQR() {
    this.cargando.set(true);
    this.asistenciasService.generarQRToken().subscribe({
      next: (res) => {
        if (res.success) {
          this.qrData.set(res.data.qr_token);
          this.cargando.set(false);
        }
      },
      error: () => {
        this.cargando.set(false);
        this.messageService.add({
          severity: 'error',
          summary: 'Error',
          detail: 'No se pudo generar el QR',
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
          this.generarQR();
          return this.DURATION;
        }
        return s - 1;
      });
    }, 1000);
  }

  refreshQr() {
    this.generarQR();
    this.secondsLeft.set(this.DURATION);
  }

  ngOnDestroy() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
  }
}
