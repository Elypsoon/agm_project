import { Component, inject, signal, computed } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive, Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';
import { ButtonModule } from 'primeng/button';
import { TooltipModule } from 'primeng/tooltip';
import { AvatarModule } from 'primeng/avatar';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

interface NavItem {
  label: string;
  icon: string;
  route: string;
}

@Component({
  selector: 'app-alumno-layout',
  standalone: true,
  imports: [
    CommonModule, RouterOutlet, RouterLink, RouterLinkActive,
    ButtonModule, TooltipModule, AvatarModule, ToastModule
  ],
  providers: [MessageService],
  templateUrl: './alumno-layout.component.html',
  styleUrls: ['./alumno-layout.component.scss']
})
export class AlumnoLayoutComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  collapsed = signal(false);

  readonly navItems: NavItem[] = [
    { label: 'Dashboard',     icon: 'pi-chart-bar',     route: '/alumno/dashboard'     },
    { label: 'Mis Materias',  icon: 'pi-book',          route: '/alumno/materias'      },
    { label: 'Calificaciones',icon: 'pi-pencil',        route: '/alumno/calificaciones' },
    { label: 'Mi QR',         icon: 'pi-qrcode',        route: '/alumno/qr-code'       },
    { label: 'Estadísticas',  icon: 'pi-chart-line',    route: '/alumno/estadisticas'  },
  ];

  readonly userName = computed(() => this.authService.currentUser()?.nombre ?? 'Alumno');
  readonly avatarLabel = computed(() => {
    const n = this.userName();
    const parts = n.split(' ');
    return parts.length >= 2
      ? (parts[0][0] + parts[1][0]).toUpperCase()
      : n.substring(0, 2).toUpperCase();
  });

  readonly activePageLabel = computed(() => {
    const url = this.router.url;
    const found = this.navItems.find(i => url.includes(i.route.replace('/alumno/', '')));
    return found?.label ?? 'Dashboard';
  });

  toggleSidebar() { this.collapsed.update(v => !v); }

  logout() {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }
}
