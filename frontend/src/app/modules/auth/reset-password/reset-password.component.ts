import { Component, OnInit, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { passwordMatchValidator } from '../auth-validators';
import { extractErrorMessage } from '../../../core/utils/error-utils';

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule, RouterModule,
    PasswordModule, ButtonModule, FloatLabelModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.scss']
})
export class ResetPasswordComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private messageService = inject(MessageService);

  isLoading = signal(false);
  successMessage = signal('');
  errorMessage = signal('');
  uid = '';
  token = '';

  resetForm: FormGroup = this.fb.group({
    new_password: ['', [Validators.required, Validators.minLength(8)]],
    new_password_confirm: ['', Validators.required]
  }, { validators: passwordMatchValidator });

  ngOnInit(): void {
    this.uid = this.route.snapshot.paramMap.get('uid') || '';
    this.token = this.route.snapshot.paramMap.get('token') || '';

    if (!this.uid || !this.token) {
      this.errorMessage.set('Enlace de recuperación inválido o incompleto.');
    }
  }

  isInvalid(field: string): boolean {
    const control = this.resetForm.get(field);
    return !!(control?.invalid && (control?.dirty || control?.touched));
  }

  onSubmit() {
    if (this.resetForm.invalid || !this.uid || !this.token) {
      this.resetForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');

    const payload = {
      uid: this.uid,
      token: this.token,
      new_password: this.resetForm.value.new_password
    };

    this.authService.resetPassword(payload).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.successMessage.set('Tu contraseña ha sido restablecida correctamente.');
        this.messageService.add({
          severity: 'success',
          summary: 'Contraseña restablecida',
          detail: 'Ya puedes iniciar sesión con tu nueva contraseña',
          life: 4000
        });
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(extractErrorMessage(err, 'Error al restablecer la contraseña. El enlace puede haber expirado.'));
      }
    });
  }
}
