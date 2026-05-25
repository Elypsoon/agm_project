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
  }
});
