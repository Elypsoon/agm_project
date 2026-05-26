import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TableModule } from 'primeng/table';
import { DatePickerModule } from 'primeng/datepicker';
import { SelectModule } from 'primeng/select';
import { TagModule } from 'primeng/tag';
import { ButtonModule } from 'primeng/button';
import { IconFieldModule } from 'primeng/iconfield';
import { InputIconModule } from 'primeng/inputicon';
import { InputTextModule } from 'primeng/inputtext';
import { SkeletonModule } from 'primeng/skeleton';

interface RegistroAsistencia {
  fecha: string;
  materia: string;
  alumno: string;
  matricula: string;
  estado: 'presente' | 'ausente' | 'tardanza';
  hora: string;
}

@Component({
  selector: 'app-historial',
  standalone: true,
  imports: [
    CommonModule, FormsModule, TableModule, DatePickerModule, SelectModule,
    TagModule, ButtonModule, IconFieldModule, InputIconModule, InputTextModule, SkeletonModule
  ],
  templateUrl: './historial.component.html',
  styleUrls: ['./historial.component.scss']
})
export class HistorialComponent implements OnInit {
  loading = signal(true);
  rangoFechas: Date[] | null = null;
  selectedMateria: string | null = null;
  searchText = '';

  readonly materiaOptions = [
    'Desarrollo de Sistemas Distribuidos',
    'Redes de Computadoras',
    'Base de Datos Avanzadas'
  ];

  allData = signal<RegistroAsistencia[]>([]);
  filteredData = signal<RegistroAsistencia[]>([]);

  statsCards = [
    { label: 'Presentes',  value: '0', color: '#22C55E' },
    { label: 'Ausentes',   value: '0', color: '#EF4444' },
    { label: 'Tardanzas',  value: '0', color: '#F59E0B' },
    { label: '% Asistencia', value: '0%', color: '#06B6D4' }
  ];

  ngOnInit() {
    setTimeout(() => {
      const data = this.generateMock();
      this.allData.set(data);
      this.filteredData.set(data);
      this.updateStats(data);
      this.loading.set(false);
    }, 700);
  }

  private generateMock(): RegistroAsistencia[] {
    const materias = ['Desarrollo de Sistemas Distribuidos', 'Redes de Computadoras', 'Base de Datos Avanzadas'];
    const alumnos = [
      ['Ana García', '202200001'], ['Carlos Pérez', '202200002'],
      ['María Hernández', '202200003'], ['José Martínez', '202200004'],
      ['Laura Sánchez', '202200005']
    ];
    const estados: ('presente' | 'ausente' | 'tardanza')[] = ['presente', 'presente', 'presente', 'ausente', 'tardanza'];
    const records: RegistroAsistencia[] = [];

    for (let d = 0; d < 10; d++) {
      const date = new Date();
      date.setDate(date.getDate() - d);
      const fechaStr = date.toLocaleDateString('es-MX');

      alumnos.forEach(([alumno, matricula], i) => {
        materias.slice(0, 2).forEach(materia => {
          records.push({
            fecha: fechaStr,
            materia,
            alumno,
            matricula,
            estado: estados[Math.floor(Math.random() * estados.length)],
            hora: `${7 + Math.floor(Math.random() * 4)}:${Math.random() > 0.5 ? '00' : '30'}`
          });
        });
      });
    }
    return records;
  }

  onFilterChange() {
    let data = this.allData();

    if (this.selectedMateria) {
      data = data.filter(r => r.materia === this.selectedMateria);
    }

    if (this.searchText) {
      const q = this.searchText.toLowerCase();
      data = data.filter(r =>
        r.alumno.toLowerCase().includes(q) || r.matricula.includes(q)
      );
    }

    this.filteredData.set(data);
    this.updateStats(data);
  }

  private updateStats(data: RegistroAsistencia[]) {
    const presentes = data.filter(r => r.estado === 'presente').length;
    const ausentes = data.filter(r => r.estado === 'ausente').length;
    const tardanzas = data.filter(r => r.estado === 'tardanza').length;
    const pct = data.length > 0 ? Math.round(((presentes + tardanzas) / data.length) * 100) : 0;

    this.statsCards = [
      { label: 'Presentes',  value: String(presentes),  color: '#22C55E' },
      { label: 'Ausentes',   value: String(ausentes),   color: '#EF4444' },
      { label: 'Tardanzas',  value: String(tardanzas),  color: '#F59E0B' },
      { label: '% Asistencia', value: `${pct}%`,        color: '#06B6D4' }
    ];
  }

  clearFilters() {
    this.rangoFechas = null;
    this.selectedMateria = null;
    this.searchText = '';
    this.filteredData.set(this.allData());
    this.updateStats(this.allData());
  }

  exportar() {
    // Placeholder: En producción conectar con ms-reportes
    console.log('Exportar historial');
  }

  estadoLabel(estado: string): string {
    const map: Record<string, string> = {
      presente: 'Presente', ausente: 'Ausente', tardanza: 'Tardanza'
    };
    return map[estado] ?? estado;
  }

  estadoSeverity(estado: string): 'success' | 'danger' | 'warn' {
    const map: Record<string, any> = {
      presente: 'success', ausente: 'danger', tardanza: 'warn'
    };
    return map[estado] ?? 'secondary';
  }
}
