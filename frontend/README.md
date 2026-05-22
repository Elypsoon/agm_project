# Frontend — Angular 20 SPA (AGM)

**PrimeNG 20 + Tema Aura Personalizado + Chart.js**

## Descripción

Single Page Application (SPA) desarrollada con **Angular 20** que consume los microservicios del backend vía REST/HTTP. Implementa los tres roles del sistema (Administrador, Docente, Alumno) con interfaces completas y profesionales.

---

## Requisitos Técnicos

- **Lazy Loading**: cada módulo (admin, docente, alumno) carga de forma diferida
- **Route Guards**: `CanActivate` para proteger rutas según rol del usuario
- **HTTP Interceptors**:
  - Interceptor para agregar automáticamente el JWT al header de cada petición
  - Interceptor para manejar errores 401 (redirigir a login)
- **Reactive Forms**: validaciones síncronas y asíncronas en todos los formularios
- **Generación de QR**: `angularx-qrcode` en módulo del alumno
- **Escaneo de QR**: `jsQR` con acceso a cámara (MediaDevices API) en módulo del docente
- **Variables de entorno**: URLs de microservicios en `src/environments/environment.ts`
- **Standalone Components**: Angular 20 usa standalone por defecto (sin NgModules)

---

## Dependencias

| Paquete | Versión | Propósito |
|---|---|---|
| `primeng` | `^20.x` | Componentes UI (tabla, formularios, sidebar, toast, etc.) |
| `@primeuix/themes` | `^2.x` | Sistema de theming con design tokens (Aura preset) |
| `primeicons` | `^7.x` | Pack de +200 iconos SVG integrados |
| `chart.js` | `^4.x` | Motor de gráficas (usado internamente por `p-chart`) |
| `angularx-qrcode` | `^19.x` | Generación de código QR dinámico (módulo alumno) |
| `jsqr` | latest | Escaneo QR con cámara (módulo docente) |

---

## Configuración del Tema — Preset AGM

### `src/app/themes/agm-preset.ts`

```typescript
import { definePreset, palette } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

export const AgmPreset = definePreset(Aura, {
  primitive: {
    indigo: palette('#4338CA'),
    amber: {
      50:  '#FFFBEB',
      100: '#FEF3C7',
      200: '#FDE68A',
      300: '#FCD34D',
      400: '#FBBF24',
      500: '#F59E0B',
      600: '#D97706',
      700: '#B45309',
      800: '#92400E',
      900: '#78350F',
      950: '#451A03'
    }
  },

  semantic: {
    primary: palette('#4338CA'),

    colorScheme: {
      light: {
        surface: {
          0:   '#FFFFFF',
          50:  '#F8FAFC',
          100: '#F1F5F9',
          200: '#E2E8F0',
          300: '#CBD5E1',
          400: '#94A3B8',
          500: '#64748B',
          600: '#475569',
          700: '#334155',
          800: '#1E293B',
          900: '#0F172A',
          950: '#020617'
        },
        primary: {
          color:         '{indigo.600}',
          contrastColor: '#FFFFFF',
          hoverColor:    '{indigo.700}',
          activeColor:   '{indigo.800}'
        },
        highlight: {
          background:      'rgba(67, 56, 202, 0.08)',
          focusBackground: 'rgba(67, 56, 202, 0.16)',
          color:           '{indigo.600}',
          focusColor:      '{indigo.700}'
        }
      },
      dark: {
        surface: {
          0:   '#1A1A2E',
          50:  '#16213E',
          100: '#1E293B',
          200: '#273549',
          300: '#334155',
          400: '#4A5568',
          500: '#6B7280',
          600: '#9CA3AF',
          700: '#D1D5DB',
          800: '#E5E7EB',
          900: '#F3F4F6',
          950: '#F9FAFB'
        },
        primary: {
          color:         '{indigo.400}',
          contrastColor: '{indigo.950}',
          hoverColor:    '{indigo.300}',
          activeColor:   '{indigo.200}'
        }
      }
    }
  },

  components: {
    button: {
      borderRadius: '8px',
      paddingX:     '1.25rem',
      paddingY:     '0.625rem'
    },
    card: {
      borderRadius: '12px',
      shadow:       '0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05)'
    },
    inputtext: {
      borderRadius: '8px'
    },
    datatable: {
      headerCell: {
        background: '{surface.50}',
        color:      '{surface.600}'
      }
    }
  }
});
```

### `src/app/app.config.ts`

```typescript
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { providePrimeNG } from 'primeng/config';

import { routes } from './app.routes';
import { AgmPreset } from './themes/agm-preset';
import { jwtInterceptor } from './core/interceptors/jwt.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(withInterceptors([jwtInterceptor, errorInterceptor])),
    provideAnimationsAsync(),
    providePrimeNG({
      theme: {
        preset: AgmPreset,
        options: {
          darkModeSelector: '.app-dark'
        }
      },
      ripple: true
    })
  ]
};
```

> [!NOTE]
> No se necesitan archivos CSS globales de PrimeNG. Solo agregar PrimeIcons en `angular.json`:
> ```json
> "styles": [
>   "node_modules/primeicons/primeicons.css",
>   "src/styles.scss"
> ]
> ```

---

## Paleta de Colores

### Índigo (Primario)

| Shade | Hex | Uso |
|---|---|---|
| 50 | `#EEF2FF` | Backgrounds de hover sutiles |
| 100 | `#E0E7FF` | Backgrounds de selección |
| 200 | `#C7D2FE` | Borders de focus |
| 300 | `#A5B4FC` | Iconos secundarios |
| **400** | `#818CF8` | Links hover, gráficas secundarias |
| **500** | `#6366F1` | Iconos activos, acentos |
| **600** | `#4F46E5` | **Botones primarios, headers** |
| **700** | `#4338CA` | Hover de botones, texto enfático |
| 800 | `#3730A3` | Active/pressed state |
| 900 | `#312E81` | **Sidebar background** |
| 950 | `#1E1B4B` | Fondos ultra oscuros |

### Ámbar (Acento)

| Shade | Hex | Uso |
|---|---|---|
| 50 | `#FFFBEB` | Background de alertas/info |
| 100 | `#FEF3C7` | Badges claros |
| 300 | `#FCD34D` | Iconos de métricas |
| **400** | `#FBBF24` | **Acento principal** — Badges, highlights |
| **500** | `#F59E0B` | Warnings, texto ámbar |
| 700 | `#B45309` | Texto ámbar sobre light |

### Cian (Acento Secundario)

| Nombre | Hex | Uso |
|---|---|---|
| Light | `#22D3EE` | Gráficas, iconos activos |
| **Base** | `#06B6D4` | Botones secundarios, links alternativos |
| Dark | `#0891B2` | Hover |

### Semánticos

| Estado | Hex | Background (12% opacity) | Uso |
|---|---|---|---|
| ✅ Success | `#22C55E` | `rgba(34, 197, 94, 0.12)` | Aprobado, asistencia confirmada, guardado exitoso |
| ⚠️ Warning | `#F59E0B` | `rgba(245, 158, 11, 0.12)` | Calificaciones bajas, periodo por cerrar |
| ❌ Danger | `#EF4444` | `rgba(239, 68, 68, 0.12)` | Reprobado, faltas, eliminar, error de validación |
| ℹ️ Info | `#3B82F6` | `rgba(59, 130, 246, 0.12)` | Notificaciones, tooltips informativos |

### Diferenciación Visual por Rol

| Rol | Color | Hex | Aplicación |
|---|---|---|---|
| **Administrador** | Índigo | `#4338CA` | `border-top: 3px solid #4338CA` en topbar |
| **Docente** | Cian | `#06B6D4` | `border-top: 3px solid #06B6D4` en topbar |
| **Alumno** | Ámbar | `#F59E0B` | `border-top: 3px solid #F59E0B` en topbar |

---

## Tipografía

### Fuentes (Google Fonts)

```html
<!-- En src/index.html -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">
```

| Uso | Fuente | Pesos | Ejemplo |
|---|---|---|---|
| **Títulos** (h1-h4) | **Outfit** | 500, 600, 700 | "Panel de Administración", "Calificaciones" |
| **Cuerpo / UI** | **Inter** | 400, 500, 600 | Tablas, formularios, labels, párrafos |
| **Monospace** | **JetBrains Mono** | 400, 500 | Matrículas (`202210482`), NRCs, códigos |

### Escala Tipográfica

```scss
$h1: 28px;    // weight: 700  → Títulos de página
$h2: 22px;    // weight: 600  → Subtítulos de sección
$h3: 18px;    // weight: 600  → Títulos de cards
$h4: 16px;    // weight: 500  → Labels de métricas

$body-lg: 16px;   // weight: 400  → Texto principal
$body:    14px;    // weight: 400  → Texto general, celdas de tabla
$body-sm: 13px;    // weight: 400  → Captions, metadata
$body-xs: 12px;    // weight: 500  → Badges, tags, hints
```

---

## Estructura SCSS

### `src/styles/_variables.scss`

```scss
// COLORES — Solo los que NO maneja PrimeNG
$sidebar-bg:          #312E81;
$sidebar-text:        #C7D2FE;
$sidebar-text-active: #FFFFFF;
$sidebar-active-bg:   rgba(99, 102, 241, 0.15);
$sidebar-hover-bg:    rgba(255, 255, 255, 0.05);
$sidebar-width:       260px;
$sidebar-collapsed:   64px;

// Acentos por rol
$role-admin:    #4338CA;
$role-docente:  #06B6D4;
$role-alumno:   #F59E0B;

// TIPOGRAFÍA
$font-heading: 'Outfit', system-ui, sans-serif;
$font-body:    'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
$font-mono:    'JetBrains Mono', 'Courier New', monospace;

// ESPACIADO
$spacing-xs:  4px;
$spacing-sm:  8px;
$spacing-md:  16px;
$spacing-lg:  24px;
$spacing-xl:  32px;
$spacing-2xl: 48px;

// RADII
$radius-sm:   6px;
$radius-md:   8px;
$radius-lg:   12px;
$radius-xl:   16px;
$radius-full: 9999px;

// SOMBRAS
$shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
$shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
$shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.05);

// BREAKPOINTS (Mobile First)
$bp-sm:  576px;
$bp-md:  768px;
$bp-lg:  992px;
$bp-xl:  1200px;
$bp-2xl: 1400px;

// TRANSICIONES
$transition-fast:   150ms ease;
$transition-normal: 250ms ease;
$transition-slow:   350ms cubic-bezier(0.4, 0, 0.2, 1);

// LAYOUT
$topbar-height: 64px;
```

### `src/styles/_mixins.scss`

```scss
@use 'variables' as v;

@mixin respond($bp) {
  @if $bp == sm  { @media (min-width: v.$bp-sm)  { @content; } }
  @if $bp == md  { @media (min-width: v.$bp-md)  { @content; } }
  @if $bp == lg  { @media (min-width: v.$bp-lg)  { @content; } }
  @if $bp == xl  { @media (min-width: v.$bp-xl)  { @content; } }
  @if $bp == 2xl { @media (min-width: v.$bp-2xl) { @content; } }
}

@mixin glass($opacity: 0.08) {
  background: rgba(255, 255, 255, $opacity);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

@mixin truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@mixin focus-ring($color: v.$role-admin) {
  &:focus-visible {
    outline: 2px solid $color;
    outline-offset: 2px;
  }
}

@mixin scrollbar {
  &::-webkit-scrollbar { width: 6px; height: 6px; }
  &::-webkit-scrollbar-track { background: transparent; }
  &::-webkit-scrollbar-thumb {
    background: rgba(148, 163, 184, 0.4);
    border-radius: v.$radius-full;
    &:hover { background: rgba(148, 163, 184, 0.6); }
  }
}
```

### `src/styles/styles.scss` (Global)

```scss
@use 'variables' as v;
@use 'mixins' as m;

*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  scroll-behavior: smooth;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: v.$font-body;
  line-height: 1.5;
  @include m.scrollbar;
}

h1, h2, h3, h4 {
  font-family: v.$font-heading;
  line-height: 1.3;
}

code, .mono {
  font-family: v.$font-mono;
}

.badge-role {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: v.$radius-full;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;

  &--admin   { background: rgba(v.$role-admin, 0.12);   color: v.$role-admin;   }
  &--docente { background: rgba(v.$role-docente, 0.12); color: v.$role-docente; }
  &--alumno  { background: rgba(v.$role-alumno, 0.12);  color: v.$role-alumno;  }
}

.mono-id {
  font-family: v.$font-mono;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.3px;
}
```

### `src/styles.scss` (Entrada principal)

```scss
@use './styles/styles.scss';
```

---

## Componentes PrimeNG por Vista

### 🔐 Auth (Login)

| Elemento | Componente | Configuración |
|---|---|---|
| Input de usuario | `InputText` | `pInputText` con `pFloatLabel` |
| Input de contraseña | `Password` | `<p-password>` con toggle de visibilidad |
| Botón de login | `Button` | `<p-button label="Iniciar Sesión" [loading]="isLoading" icon="pi pi-sign-in">` |
| Mensajes de error | `Message` | `<p-message severity="error">` |
| Loader | `ProgressSpinner` | Dentro del botón con `[loading]="true"` |

### 🛡️ Admin

| Vista | Componentes | Detalles |
|---|---|---|
| **Dashboard** | `Card` + `Chart` | 4 metric cards + donut + bar chart |
| **Periodos** | `Table` + `Tag` + `Calendar` | `<p-table [paginator]="true" [rows]="10">`, `<p-tag>` para Activo/Cerrado |
| **Materias** | `Table` + `IconField` + `FileUpload` | Tabla con búsqueda, `<p-fileUpload>` para PDF |
| **Docentes** | `Table` + `Select` + `Dialog` | Tabla + `<p-select>` para asignar materias |

### 👨‍🏫 Docente

| Vista | Componentes | Detalles |
|---|---|---|
| **Dashboard** | `Card` + `Chart` | Cards de resumen + bar chart asistencia semanal |
| **Materias** | `Card` + `DataView` | `<p-dataView>` para listar grupos como cards |
| **Ponderaciones** | `InputNumber` + `ProgressBar` | `<p-inputNumber [suffix]="'%'">` + suma 100% |
| **Calificaciones** | `Table` (editable) | `<p-table [editMode]="'row'">` edición inline |
| **Asistencia QR** | HTML5 `<video>` + `Toast` | Cámara con jsQR, toast de confirmación |
| **Historial** | `Table` + `Calendar` | Filtro por rango con `<p-calendar [selectionMode]="'range'">` |

### 🎓 Alumno

| Vista | Componentes | Detalles |
|---|---|---|
| **Dashboard** | `Card` + `Chart` | Promedio general + radar chart rendimiento |
| **Materias** | `Card` | Cards con info, horario, profesor |
| **Calificaciones** | `Table` + `Tag` | Desglose parcial, `<p-tag>` Aprobado/Reprobado |
| **QR Code** | `angularx-qrcode` + `ProgressBar` | `<qrcode [data]="token">` + cuenta regresiva |
| **Estadísticas** | `Chart` (line + doughnut) | Evolución de calificaciones + % asistencia |

---

## Formularios — Patrón de Retroalimentación Visual

### Reactive Forms + PrimeNG

Todos los formularios usan **Reactive Forms** (`FormGroup` + `FormControl`).

```typescript
import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { InputTextModule } from 'primeng/inputtext';
import { FloatLabelModule } from 'primeng/floatlabel';
import { PasswordModule } from 'primeng/password';
import { ButtonModule } from 'primeng/button';
import { MessageModule } from 'primeng/message';
import { ToastModule } from 'primeng/toast';
import { MessageService } from 'primeng/api';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule, ReactiveFormsModule,
    InputTextModule, FloatLabelModule, PasswordModule,
    ButtonModule, MessageModule, ToastModule
  ],
  providers: [MessageService],
  template: `
    <p-toast position="top-right" />

    <form [formGroup]="form" (ngSubmit)="onSubmit()">

      <p-floatlabel>
        <input pInputText id="username" formControlName="username"
               [class.ng-invalid]="isInvalid('username')"
               [class.ng-dirty]="isInvalid('username')" />
        <label for="username">Usuario / Matrícula</label>
      </p-floatlabel>

      @if (isInvalid('username')) {
        <small class="p-error">
          @if (form.get('username')?.errors?.['required']) {
            El usuario es obligatorio.
          }
          @if (form.get('username')?.errors?.['minlength']) {
            Mínimo 5 caracteres.
          }
        </small>
      }

      <p-floatlabel>
        <p-password id="password" formControlName="password"
                    [feedback]="false" [toggleMask]="true" />
        <label for="password">Contraseña</label>
      </p-floatlabel>

      @if (isInvalid('password')) {
        <small class="p-error">La contraseña es obligatoria.</small>
      }

      <p-button
        type="submit"
        label="Iniciar Sesión"
        icon="pi pi-sign-in"
        [loading]="isLoading()"
        [disabled]="form.invalid || isLoading()" />

      @if (errorMessage()) {
        <p-message severity="error" [text]="errorMessage()" />
      }

    </form>
  `
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private messageService = inject(MessageService);

  isLoading = signal(false);
  errorMessage = signal('');

  form = this.fb.group({
    username: ['', [Validators.required, Validators.minLength(5)]],
    password: ['', [Validators.required]]
  });

  isInvalid(field: string): boolean {
    const control = this.form.get(field);
    return !!(control?.invalid && (control?.dirty || control?.touched));
  }

  async onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set('');

    try {
      // ... llamada al servicio de auth ...

      this.messageService.add({
        severity: 'success',
        summary: 'Bienvenido',
        detail: 'Inicio de sesión exitoso',
        life: 3000
      });
    } catch (err: any) {
      this.errorMessage.set(err.message || 'Credenciales incorrectas');
    } finally {
      this.isLoading.set(false);
    }
  }
}
```

### Tipos de Feedback

| Tipo | Componente PrimeNG | Cuándo Usarlo |
|---|---|---|
| **Error inline** | `<small class="p-error">` | Validación de campo (`required`, `minlength`, `email`, `pattern`) |
| **Error global** | `<p-message severity="error">` | Error del servidor (credenciales inválidas, duplicado) |
| **Spinner** | `<p-button [loading]="true">` | Mientras se espera respuesta del backend |
| **Éxito** | `<p-toast severity="success">` | Después de guardar/crear/actualizar |
| **Confirmación destructiva** | `<p-confirmDialog>` | Antes de eliminar un registro |
| **Progreso** | `<p-progressBar mode="indeterminate">` | Importación de PDF/Excel |
| **Skeleton** | `<p-skeleton>` | Carga inicial de tablas o cards |

### Patrón para Eliminación

```typescript
import { ConfirmDialogModule } from 'primeng/confirmdialog';
import { ConfirmationService, MessageService } from 'primeng/api';

confirmDelete(id: number) {
  this.confirmationService.confirm({
    message: '¿Estás seguro de eliminar este registro? Esta acción no se puede deshacer.',
    header: 'Confirmar eliminación',
    icon: 'pi pi-exclamation-triangle',
    acceptLabel: 'Sí, eliminar',
    rejectLabel: 'Cancelar',
    acceptButtonStyleClass: 'p-button-danger',
    accept: () => {
      this.service.delete(id).subscribe({
        next: () => {
          this.messageService.add({
            severity: 'success',
            summary: 'Eliminado',
            detail: 'El registro fue eliminado correctamente'
          });
          this.loadData();
        },
        error: (err) => {
          this.messageService.add({
            severity: 'error',
            summary: 'Error',
            detail: err.message
          });
        }
      });
    }
  });
}
```

### Validaciones Comunes

| Campo | Validación | Validators |
|---|---|---|
| Matrícula | Obligatoria, numérica, 9 dígitos | `required`, `pattern(/^\d{9}$/)` |
| Email | Obligatorio, formato válido | `required`, `email` |
| Contraseña | Obligatoria, mín 8 chars | `required`, `minLength(8)` |
| Nombre | Obligatorio, mín 2 chars | `required`, `minLength(2)` |
| Calificación | Obligatoria, 0-10 | `required`, `min(0)`, `max(10)` |
| Ponderación (%) | Obligatoria, 1-100 | `required`, `min(1)`, `max(100)` |
| Fecha de inicio | Obligatoria, no pasada | `required`, validador custom `fechaFutura` |
| NRC | Obligatorio, 5 dígitos | `required`, `pattern(/^\d{5}$/)` |

> [!TIP]
> PrimeNG aplica automáticamente un **borde rojo** a inputs con clases `ng-invalid ng-dirty`.

---

## Layout y Navegación

### Posible estructura del Layout Principal

```
┌──────────────────────────────────────────────────────────┐
│                    border-top: 3px solid $role-color      │
├──────────────┬───────────────────────────────────────────┤
│              │  Topbar (64px)                             │
│  Sidebar     │  ┌─ Hamburguesa (mobile) ─── Breadcrumb ──│── Badge Rol ─ Avatar ─┐
│  (260px)     │  └────────────────────────────────────────┘│
│  ──────────  │───────────────────────────────────────────│
│  Logo AGM    │                                           │
│              │   Contenido de la Página                  │
│  Dashboard ◀ │                                           │
│  Periodos    │   ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  Materias    │   │ Metric   │  │ Metric   │  │ Metric │ │
│  Docentes    │   │ Card     │  │ Card     │  │ Card   │ │
│              │   └──────────┘  └──────────┘  └────────┘ │
│  ──────────  │                                           │
│              │   ┌─────────────────────────────────────┐ │
│  Cerrar      │   │         p-table                     │ │
│  Sesión      │   │   Paginación  │  Filtro  │  Sort    │ │
│              │   └─────────────────────────────────────┘ │
└──────────────┴───────────────────────────────────────────┘
```

### Comportamiento Responsivo

| Breakpoint | Sidebar | Topbar | Contenido |
|---|---|---|---|
| **≥ 992px** (desktop) | Visible, 260px fijo | Completo: breadcrumb + avatar + badge | Grid de cards |
| **768–991px** (tablet) | Colapsado a 64px (solo iconos), hover para expandir | Simplificado | Cards en 2 columnas |
| **< 768px** (mobile) | Drawer overlay (hamburguesa) | Solo hamburguesa + avatar | 1 columna, tablas con scroll horizontal |

---

## Micro-Animaciones y Transiciones

| Elemento | Efecto | Implementación |
|---|---|---|
| **Botones** | Elevación al hover | `translateY(-1px)` + `box-shadow`, `transition: 250ms` |
| **Cards métricas** | Elevación al hover | `translateY(-3px)` + `$shadow-lg`, `transition: 300ms cubic-bezier(0.4, 0, 0.2, 1)` |
| **Sidebar items** | Borde izquierdo + highlight | `border-left: 3px solid transparent → $primary`, `background → $sidebar-active-bg` |
| **Transiciones de página** | Fade-in | `opacity: 0 → 1` + `translateY(8px) → 0` en 200ms |
| **Skeleton loading** | Pulse | `<p-skeleton>` (animado por defecto) |
| **Toast** | Slide desde arriba | `p-toast position="top-right"` (animado por defecto) |
| **Modales** | Fade + Scale | `<p-dialog>` (animación nativa PrimeNG) |
| **Valores numéricos** | Count-up | CSS `@property` con animación al entrar al viewport |
| **Ripple** | Material ripple | `ripple: true` en `providePrimeNG()` |

---

## Gráficas — Configuración por Dashboard

Todas usan `<p-chart>` (wrapper de Chart.js incluido en PrimeNG).

### Admin Dashboard

```typescript
// Donut — Distribución de alumnos
chartData = {
  labels: ['Ing. Computación', 'Ing. Software', 'Matemáticas', 'Física'],
  datasets: [{
    data: [320, 280, 150, 90],
    backgroundColor: ['#4338CA', '#6366F1', '#06B6D4', '#F59E0B'],
    borderWidth: 0,
    cutout: '70%'
  }]
};

// Bar horizontal — Materias por periodo
barData = {
  labels: ['Otoño 2026', 'Primavera 2026', 'Verano 2025'],
  datasets: [{
    label: 'Materias activas',
    data: [48, 52, 12],
    backgroundColor: '#4338CA',
    borderRadius: 6
  }]
};
```

### Docente Dashboard

```typescript
// Bar vertical — Asistencia semanal
barData = {
  labels: ['Lun', 'Mar', 'Mié', 'Jue', 'Vie'],
  datasets: [{
    label: '% Asistencia',
    data: [95, 88, 92, 96, 90],
    backgroundColor: '#06B6D4',
    borderRadius: 6
  }]
};
```

### Alumno Dashboard

```typescript
// Radar — Rendimiento por materia
radarData = {
  labels: ['Servicios Web', 'Ing. Software', 'Redes', 'Base de Datos', 'Cálculo'],
  datasets: [{
    label: 'Mi rendimiento',
    data: [9.2, 8.5, 7.8, 9.0, 8.2],
    fill: true,
    backgroundColor: 'rgba(67, 56, 202, 0.15)',
    borderColor: '#4338CA',
    pointBackgroundColor: '#4338CA'
  }]
};
```

### Opciones globales para gráficas

```typescript
chartOptions = {
  plugins: {
    legend: {
      labels: {
        font: { family: 'Inter', size: 13 },
        color: '#64748B'
      }
    }
  },
  scales: {
    x: { ticks: { font: { family: 'Inter' }, color: '#94A3B8' }, grid: { color: '#E2E8F0' } },
    y: { ticks: { font: { family: 'Inter' }, color: '#94A3B8' }, grid: { color: '#E2E8F0' } }
  }
};
```

---

## Iconos (PrimeIcons)

| Contexto | Clase |
|---|---|
| Dashboard | `pi pi-chart-bar` |
| Usuarios | `pi pi-users` |
| Materias | `pi pi-book` |
| Periodos | `pi pi-calendar` |
| Calificaciones | `pi pi-pencil` |
| QR Code | `pi pi-qrcode` |
| Historial | `pi pi-history` |
| Estadísticas | `pi pi-chart-line` |
| Login | `pi pi-sign-in` |
| Logout | `pi pi-sign-out` |
| Buscar | `pi pi-search` |
| Filtrar | `pi pi-filter` |
| Éxito | `pi pi-check-circle` |
| Error | `pi pi-times-circle` |
| Warning | `pi pi-exclamation-triangle` |
| Descargar | `pi pi-download` |
| Subir archivo | `pi pi-upload` |

---

### Paso 3 — Nota sobre Standalone Components

> [!WARNING]
> Angular 20 usa **Standalone Components** por defecto:
>
> | README original (NgModule) | Equivalente Standalone |
> |---|---|
> | `app.module.ts` | `app.config.ts` |
> | `app-routing.module.ts` | `app.routes.ts` |
> | `app.component.ts` | Sin cambios, importa componentes en `imports: []` |

---

## Routing

### `src/app/app.routes.ts`

```typescript
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () => import('./modules/auth/auth.routes').then(m => m.AUTH_ROUTES)
  },
  {
    path: 'admin',
    loadChildren: () => import('./modules/admin/admin.routes').then(m => m.ADMIN_ROUTES),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] }
  },
  {
    path: 'docente',
    loadChildren: () => import('./modules/docente/docente.routes').then(m => m.DOCENTE_ROUTES),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['DOCENTE'] }
  },
  {
    path: 'alumno',
    loadChildren: () => import('./modules/alumno/alumno.routes').then(m => m.ALUMNO_ROUTES),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ALUMNO'] }
  },
  { path: '', redirectTo: '/auth/login', pathMatch: 'full' },
  { path: '**', redirectTo: '/auth/login' }
];
```

### `src/app/app.component.ts`

```typescript
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `<router-outlet />`
})
export class AppComponent {}
```

### Rutas de módulos

```typescript
// src/app/modules/auth/auth.routes.ts
export const AUTH_ROUTES: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./login/login.component').then(c => c.LoginComponent)
  },
  {
    path: 'forgot-password',
    loadComponent: () => import('./forgot-password/forgot-password.component')
      .then(c => c.ForgotPasswordComponent)
  },
  { path: '', redirectTo: 'login', pathMatch: 'full' }
];
```

```typescript
// src/app/modules/admin/admin.routes.ts
export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./admin-layout.component').then(c => c.AdminLayoutComponent),
    children: [
      { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard.component').then(c => c.DashboardComponent) },
      { path: 'periodos', loadComponent: () => import('./periodos/periodos.component').then(c => c.PeriodosComponent) },
      { path: 'materias', loadComponent: () => import('./materias/materias.component').then(c => c.MateriasComponent) },
      { path: 'docentes', loadComponent: () => import('./docentes/docentes.component').then(c => c.DocentesComponent) },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  }
];
```

```typescript
// src/app/modules/docente/docente.routes.ts
export const DOCENTE_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./docente-layout.component').then(c => c.DocenteLayoutComponent),
    children: [
      { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard.component').then(c => c.DashboardComponent) },
      { path: 'materias', loadComponent: () => import('./materias/materias.component').then(c => c.MateriasComponent) },
      { path: 'ponderaciones', loadComponent: () => import('./ponderaciones/ponderaciones.component').then(c => c.PonderacionesComponent) },
      { path: 'calificaciones', loadComponent: () => import('./calificaciones/calificaciones.component').then(c => c.CalificacionesComponent) },
      { path: 'asistencia-qr', loadComponent: () => import('./asistencia-qr/asistencia-qr.component').then(c => c.AsistenciaQrComponent) },
      { path: 'historial', loadComponent: () => import('./historial/historial.component').then(c => c.HistorialComponent) },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  }
];
```

```typescript
// src/app/modules/alumno/alumno.routes.ts
export const ALUMNO_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./alumno-layout.component').then(c => c.AlumnoLayoutComponent),
    children: [
      { path: 'dashboard', loadComponent: () => import('./dashboard/dashboard.component').then(c => c.DashboardComponent) },
      { path: 'materias', loadComponent: () => import('./materias/materias.component').then(c => c.MateriasComponent) },
      { path: 'calificaciones', loadComponent: () => import('./calificaciones/calificaciones.component').then(c => c.CalificacionesComponent) },
      { path: 'qr-code', loadComponent: () => import('./qr-code/qr-code.component').then(c => c.QrCodeComponent) },
      { path: 'estadisticas', loadComponent: () => import('./estadisticas/estadisticas.component').then(c => c.EstadisticasComponent) },
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' }
    ]
  }
];
```

---

## Core — Guards

```typescript
// src/app/core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  router.navigate(['/auth/login'], { queryParams: { returnUrl: state.url } });
  return false;
};
```

```typescript
// src/app/core/guards/role.guard.ts
import { inject } from '@angular/core';
import { Router, type CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const expectedRoles = route.data?.['roles'] as string[] ?? [];
  const userRole = authService.getUserRole();

  if (authService.isAuthenticated() && expectedRoles.includes(userRole)) {
    return true;
  }

  router.navigate(['/auth/login']);
  return false;
};
```

---

## Core — Interceptors

```typescript
// src/app/core/interceptors/jwt.interceptor.ts
import { type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const token = inject(AuthService).getToken();

  if (token) {
    req = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` }
    });
  }

  return next(req);
};
```

```typescript
// src/app/core/interceptors/error.interceptor.ts
import { type HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return next(req).pipe(
    catchError((err) => {
      if ([401, 403].includes(err.status)) {
        authService.logout();
        router.navigate(['/auth/login']);
      }
      const message = err.error?.message || err.statusText || 'Error desconocido';
      return throwError(() => new Error(message));
    })
  );
};
```

---

## Core — Services

```typescript
// src/app/core/services/auth.service.ts
import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);

  private tokenSignal = signal<string | null>(localStorage.getItem('token'));
  private roleSignal = signal<string | null>(localStorage.getItem('role'));
  private userSignal = signal<any | null>(
    JSON.parse(localStorage.getItem('user') || 'null')
  );

  readonly isLoggedIn = computed(() => !!this.tokenSignal());
  readonly currentUser = computed(() => this.userSignal());
  readonly currentRole = computed(() => this.roleSignal());

  getToken(): string | null { return this.tokenSignal(); }
  getUserRole(): string { return this.roleSignal() || ''; }
  isAuthenticated(): boolean { return this.isLoggedIn(); }

  login(credentials: { username: string; password: string }): Observable<any> {
    return this.http.post(`${environment.apiUrls.auth}/login`, credentials).pipe(
      tap((res: any) => {
        localStorage.setItem('token', res.token);
        localStorage.setItem('role', res.user.rol);
        localStorage.setItem('user', JSON.stringify(res.user));

        this.tokenSignal.set(res.token);
        this.roleSignal.set(res.user.rol);
        this.userSignal.set(res.user);
      })
    );
  }

  logout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('user');

    this.tokenSignal.set(null);
    this.roleSignal.set(null);
    this.userSignal.set(null);
  }
}
```

```typescript
// src/app/core/services/api.service.ts
import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);

  get<T>(url: string, params?: Record<string, string>): Observable<T> {
    const httpParams = new HttpParams({ fromObject: params || {} });
    return this.http.get<T>(url, { params: httpParams });
  }

  post<T>(url: string, body: any): Observable<T> {
    return this.http.post<T>(url, body);
  }

  put<T>(url: string, body: any): Observable<T> {
    return this.http.put<T>(url, body);
  }

  patch<T>(url: string, body: any): Observable<T> {
    return this.http.patch<T>(url, body);
  }

  delete<T>(url: string): Observable<T> {
    return this.http.delete<T>(url);
  }
}
```

---

## Environments

```typescript
// src/environments/environment.ts (desarrollo)
export const environment = {
  production: false,
  apiUrls: {
    auth:            'http://localhost:3001/api',
    periodos:        'http://localhost:3002/api',
    alumnos:         'http://localhost:3003/api',
    calificaciones:  'http://localhost:3004/api',
    asistencias:     'http://localhost:3005/api',
    notificaciones:  'http://localhost:3006/api',
    reportes:        'http://localhost:3007/api'
  }
};
```

```typescript
// src/environments/environment.prod.ts (producción)
export const environment = {
  production: true,
  apiUrls: {
    auth:            '/api/auth',
    periodos:        '/api/periodos',
    alumnos:         '/api/alumnos',
    calificaciones:  '/api/calificaciones',
    asistencias:     '/api/asistencias',
    notificaciones:  '/api/notificaciones',
    reportes:        '/api/reportes'
  }
};
```

---

### nginx.conf

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

## Estructura Final del Proyecto

```
frontend/
├── angular.json
├── package.json
├── tsconfig.json
├── Dockerfile
├── nginx.conf
├── .env.example
├── README.md
├── src/
│   ├── main.ts
│   ├── index.html                         # Con Google Fonts
│   ├── styles.scss                        # Entrada SCSS
│   ├── environments/
│   │   ├── environment.ts
│   │   └── environment.prod.ts
│   ├── styles/
│   │   ├── _variables.scss
│   │   ├── _mixins.scss
│   │   └── styles.scss
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   └── app/
│       ├── app.component.ts
│       ├── app.config.ts
│       ├── app.routes.ts
│       ├── themes/
│       │   └── agm-preset.ts
│       ├── core/
│       │   ├── guards/
│       │   │   ├── auth.guard.ts
│       │   │   └── role.guard.ts
│       │   ├── interceptors/
│       │   │   ├── jwt.interceptor.ts
│       │   │   └── error.interceptor.ts
│       │   └── services/
│       │       ├── auth.service.ts
│       │       └── api.service.ts
│       ├── shared/
│       │   ├── components/
│       │   ├── pipes/
│       │   └── directives/
│       └── modules/
│           ├── auth/
│           │   └── auth.routes.ts
│           ├── admin/
│           │   ├── admin.routes.ts
│           │   ├── admin-layout.component.ts
│           │   ├── dashboard/
│           │   ├── periodos/
│           │   ├── materias/
│           │   └── docentes/
│           ├── docente/
│           │   ├── docente.routes.ts
│           │   ├── docente-layout.component.ts
│           │   ├── dashboard/
│           │   ├── materias/
│           │   ├── ponderaciones/
│           │   ├── calificaciones/
│           │   ├── asistencia-qr/
│           │   └── historial/
│           └── alumno/
│               ├── alumno.routes.ts
│               ├── alumno-layout.component.ts
│               ├── dashboard/
│               ├── materias/
│               ├── calificaciones/
│               ├── qr-code/
│               └── estadisticas/
```

---

## Decisiones de Diseño

| Decisión | Elección |
|---|---|
| **Librería UI** | PrimeNG 20 + Aura |
| **Theming** | `definePreset()` con design tokens |
| **Color primario** | Índigo `#4338CA` |
| **Modo visual** | Sidebar oscuro + contenido claro |
| **Fuente headings** | Outfit |
| **Fuente body** | Inter |
| **Iconos** | PrimeIcons |
| **Gráficas** | `p-chart` (Chart.js integrado) |
| **SCSS** | `@use` en lugar de `@import` |
| **Arquitectura** | Standalone Components (Angular 20) |