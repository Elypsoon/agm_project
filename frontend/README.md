# Frontend — Aplicación Angular 20

---

## 🚀 Quick Start

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Manual:**
```bash
npm install
npm start
```

Then open: **http://localhost:4200**

---

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
- **Generación de QR**: `angularx-qrcode` o equivalente en módulo del alumno
- **Escaneo de QR**: `jsQR` o `zxing-js` con acceso a cámara (MediaDevices API) en módulo del docente
- **Variables de entorno**: URLs de microservicios en `src/environments/environment.ts`

---

## Requisitos de Diseño

- Identidad visual consistente (paleta de colores, tipografía, iconografía)
- Librería de componentes UI: **Angular Material**, PrimeNG, Taiga UI o ng-zorro-antd
- Diseño **completamente responsivo** (mobile-first)
- Dashboards con **gráficas** (Chart.js, ApexCharts o ng2-charts)
- Formularios con retroalimentación visual (errores inline, spinners, confirmaciones)
- Tablas con paginación, búsqueda en tiempo real y ordenamiento

---

## Posible estructura

```
frontend/
├── angular.json
├── package.json
├── tsconfig.json
├── Dockerfile
├── .env.example
├── src/
│   ├── environments/
│   │   ├── environment.ts          # URLs de microservicios (desarrollo)
│   │   └── environment.prod.ts     # URLs de microservicios (producción)
│   ├── app/
│   │   ├── app.module.ts
│   │   ├── app-routing.module.ts
│   │   ├── core/                   # Servicios singleton, guards, interceptors
│   │   │   ├── guards/
│   │   │   │   ├── auth.guard.ts
│   │   │   │   └── role.guard.ts
│   │   │   ├── interceptors/
│   │   │   │   ├── jwt.interceptor.ts
│   │   │   │   └── error.interceptor.ts
│   │   │   └── services/
│   │   │       ├── auth.service.ts
│   │   │       └── api.service.ts
│   │   ├── shared/                 # Componentes y pipes reutilizables
│   │   │   ├── components/
│   │   │   ├── pipes/
│   │   │   └── directives/
│   │   ├── modules/
│   │   │   ├── auth/               # Login, recuperación de contraseña
│   │   │   ├── admin/              # Módulo Administrador (lazy loaded)
│   │   │   │   ├── dashboard/
│   │   │   │   ├── periodos/
│   │   │   │   ├── materias/
│   │   │   │   └── docentes/
│   │   │   ├── docente/            # Módulo Docente (lazy loaded)
│   │   │   │   ├── dashboard/
│   │   │   │   ├── materias/
│   │   │   │   ├── ponderaciones/
│   │   │   │   ├── calificaciones/
│   │   │   │   ├── asistencia-qr/
│   │   │   │   └── historial/
│   │   │   └── alumno/             # Módulo Alumno (lazy loaded)
│   │   │       ├── dashboard/
│   │   │       ├── materias/
│   │   │       ├── calificaciones/
│   │   │       ├── qr-code/
│   │   │       └── estadisticas/
│   │   └── app.component.ts
│   ├── assets/
│   │   ├── images/
│   │   └── icons/
│   └── styles/
│       ├── _variables.scss
│       ├── _mixins.scss
│       └── styles.scss
└── README.md
```