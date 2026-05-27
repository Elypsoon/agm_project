import { AbstractControl, ValidationErrors } from '@angular/forms';

/**
 * Validador de grupo que verifica que `new_password` y `new_password_confirm` coincidan.
 * Se aplica a nivel de FormGroup (no de control individual).
 */
export function passwordMatchValidator(control: AbstractControl): ValidationErrors | null {
  const newPassword = control.get('new_password')?.value;
  const confirmPassword = control.get('new_password_confirm')?.value;

  if (newPassword && confirmPassword && newPassword !== confirmPassword) {
    return { passwordMismatch: true };
  }
  return null;
}
