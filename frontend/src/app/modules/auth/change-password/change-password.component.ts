import { Component, inject, signal } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';
import { CommonModule } from '@angular/common';
import { passwordMatchValidator } from '../auth-validators';

@Component({
  selector: 'app-change-password',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule,
    PasswordModule, ButtonModule, FloatLabelModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './change-password.component.html',
  styleUrls: ['./change-password.component.scss']
})
export class ChangePasswordComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private messageService = inject(MessageService);

  isLoading = signal(false);
  errorMessage = signal('');

  passwordForm: FormGroup = this.fb.group({
    old_password: ['', Validators.required],
    new_password: ['', [Validators.required, Validators.minLength(8)]],
    new_password_confirm: ['', Validators.required]
  }, { validators: passwordMatchValidator });

  isInvalid(field: string): boolean {
    const control = this.passwordForm.get(field);
    return !!(control?.invalid && (control?.dirty || control?.touched));
  }

  onSubmit() {
    if (this.passwordForm.invalid) {
      this.passwordForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    this.authService.changePassword(this.passwordForm.value).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.messageService.add({
          severity: 'success',
          summary: 'Contraseña actualizada',
          detail: 'Tu contraseña ha sido cambiada correctamente',
          life: 3000
        });
        setTimeout(() => {
          this.router.navigate([this.authService.getDashboardRoute()]);
        }, 1500);
      },
      error: (err) => {
        this.isLoading.set(false);
        this.errorMessage.set(err.message || 'Error al cambiar la contraseña. Verifica tu contraseña actual.');
      }
    });
  }
}
