import { Component, OnInit, inject } from '@angular/core';
import { AbstractControl, FormBuilder, FormGroup, ValidationErrors, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { FloatLabelModule } from 'primeng/floatlabel';
import { CommonModule } from '@angular/common';

export function passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
  const newPassword = control.get('new_password')?.value;
  const confirmPassword = control.get('new_password_confirm')?.value;
  
  if (newPassword && confirmPassword && newPassword !== confirmPassword) {
    return { passwordMismatch: true };
  }
  return null;
}

@Component({
  selector: 'app-reset-password',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, PasswordModule, ButtonModule, FloatLabelModule, RouterModule],
  templateUrl: './reset-password.component.html',
  styleUrls: ['./reset-password.component.scss']
})
export class ResetPasswordComponent implements OnInit {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  resetForm: FormGroup = this.fb.group({
    new_password: ['', [Validators.required, Validators.minLength(8)]],
    new_password_confirm: ['', Validators.required]
  }, { validators: passwordMatchValidator });

  isLoading = false;
  successMessage = '';
  errorMessage = '';
  uid = '';
  token = '';

  ngOnInit(): void {
    this.uid = this.route.snapshot.paramMap.get('uid') || '';
    this.token = this.route.snapshot.paramMap.get('token') || '';

    if (!this.uid || !this.token) {
      this.errorMessage = 'Enlace de recuperación inválido o incompleto.';
    }
  }

  onSubmit() {
    if (this.resetForm.invalid || !this.uid || !this.token) {
      this.resetForm.markAllAsTouched();
      return;
    }

    this.isLoading = true;
    this.errorMessage = '';
    this.successMessage = '';

    const payload = {
      uid: this.uid,
      token: this.token,
      new_password: this.resetForm.value.new_password
    };

    this.authService.resetPassword(payload).subscribe({
      next: () => {
        this.isLoading = false;
        this.successMessage = 'Tu contraseña ha sido restablecida correctamente.';
      },
      error: (err) => {
        this.isLoading = false;
        this.errorMessage = err.message || 'Error al restablecer la contraseña. El enlace puede haber expirado.';
      }
    });
  }
}
