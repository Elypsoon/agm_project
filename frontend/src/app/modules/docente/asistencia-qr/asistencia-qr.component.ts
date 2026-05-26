import {
  Component, OnInit, OnDestroy, inject, signal, ElementRef, ViewChild, NgZone
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ButtonModule } from 'primeng/button';
import { ToastModule } from 'primeng/toast';
import { TagModule } from 'primeng/tag';
import { MessageService } from 'primeng/api';
import jsQR from 'jsqr';

type ScanStatus = 'idle' | 'scanning' | 'success' | 'error';

@Component({
  selector: 'app-asistencia-qr',
  standalone: true,
  imports: [CommonModule, ButtonModule, ToastModule, TagModule],
  providers: [MessageService],
  templateUrl: './asistencia-qr.component.html',
  styleUrls: ['./asistencia-qr.component.scss']
})
export class AsistenciaQrComponent implements OnInit, OnDestroy {
  @ViewChild('videoEl') videoEl!: ElementRef<HTMLVideoElement>;
  @ViewChild('canvasEl') canvasEl!: ElementRef<HTMLCanvasElement>;

  private messageService = inject(MessageService);
  private ngZone = inject(NgZone);

  status = signal<ScanStatus>('idle');
  scanHistory = signal<{ name: string; initials: string; timestamp: string; success: boolean }[]>([]);

  private stream: MediaStream | null = null;
  private animationId: number | null = null;

  ngOnInit() {}

  async startScanning() {
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
        detail: 'Permite el acceso a la cámara para escanear QR codes',
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

  private handleQRCode(data: string) {
    this.stopStream();

    // data esperado: alumno-uuid|timestamp
    const parts = data.split('|');
    const alumnoId = parts[0];

    // Validación básica
    if (!alumnoId || alumnoId.length < 10) {
      this.status.set('error');
      setTimeout(() => this.resetScanner(), 2000);
      return;
    }

    this.status.set('success');
    const name = 'Alumno QR'; // En producción: lookup por alumnoId
    const initials = 'AQ';
    const timestamp = new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });

    this.scanHistory.update(h => [{ name, initials, timestamp, success: true }, ...h]);

    this.messageService.add({
      severity: 'success',
      summary: 'Asistencia registrada',
      detail: `ID: ${alumnoId.substring(0, 8)}...`,
      life: 3000
    });

    setTimeout(() => this.resetScanner(), 2500);
  }

  stopScanning() {
    this.stopStream();
    this.status.set('idle');
  }

  resetScanner() {
    this.stopStream();
    this.status.set('idle');
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
  }
}
