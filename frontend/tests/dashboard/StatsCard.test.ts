/**
 * Tests para componente StatsCard
 * Renderizado de estadísticas y accesibilidad
 */
import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import StatsCard from '../../src/components/dashboard/StatsCard.svelte';

describe('StatsCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debería renderizar tarjeta con título y valor', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Usuarios Activos',
        value: 150,
        icon: 'users',
        color: 'blue'
      }
    });

    expect(screen.getByText('Usuarios Activos')).toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('debería renderizar ícono correctamente', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Total Usuarios',
        value: 500,
        icon: 'users',
        color: 'green'
      }
    });

    const icon = getByTestId('stats-icon');
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveClass('icon-users');
  });

  it('debería aplicar clases de color correctas', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Usuarios Pendientes',
        value: 25,
        icon: 'pending',
        color: 'yellow'
      }
    });

    const card = getByTestId('stats-card');
    expect(card).toHaveClass('bg-yellow-100', 'border-yellow-200');
  });

  it('debería mostrar valor formateado para números grandes', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Total Sesiones',
        value: 1234567,
        icon: 'sessions',
        color: 'purple'
      }
    });

    // Debería formatear el número (ej: 1.23M)
    expect(screen.getByText(/1\.23M/)).toBeInTheDocument();
  });

  it('debería manejar valor cero correctamente', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Nuevos Usuarios',
        value: 0,
        icon: 'new',
        color: 'gray'
      }
    });

    expect(screen.getByText('0')).toBeInTheDocument();
    
    const card = getByTestId('stats-card');
    expect(card).toHaveClass('bg-gray-100');
  });

  it('debería ser accesible', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Tasa de Conversión',
        value: 85.5,
        icon: 'chart',
        color: 'blue'
      }
    });

    const card = getByTestId('stats-card');
    const title = screen.getByText('Tasa de Conversión');
    
    // Verificar atributos de accesibilidad
    expect(card).toHaveAttribute('role', 'article');
    expect(title).toHaveAttribute('aria-label', 'Tasa de Conversión: 85.5');
  });

  it('debería mostrar cambio en el valor', async () => {
    const { getByTestId, rerender } = render(StatsCard, {
      props: {
        title: 'Usuarios Online',
        value: 100,
        icon: 'online',
        color: 'green'
      }
    });

    expect(screen.getByText('100')).toBeInTheDocument();

    // Actualizar valor
    await rerender({
      title: 'Usuarios Online',
      value: 150,
      icon: 'online',
      color: 'green'
    });

    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('debería manejar propiedades opcionales', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Estadística Simple',
        value: 42
        // Sin icon, color, etc.
      }
    });

    expect(screen.getByText('Estadística Simple')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    
    const card = getByTestId('stats-card');
    expect(card).toHaveClass('bg-default'); // Clase por defecto
  });

  it('debería tener estructura semántica correcta', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Métrica Importante',
        value: 999,
        icon: 'important',
        color: 'red'
      }
    });

    const card = getByTestId('stats-card');
    const title = screen.getByText('Métrica Importante');
    const value = screen.getByText('999');

    // Verificar estructura semántica
    expect(card.tagName).toBe('ARTICLE');
    expect(title.tagName).toBe('H3');
    expect(value.tagName).toBe('P');
  });

  it('debería ser responsive', () => {
    const { getByTestId } = render(StatsCard, {
      props: {
        title: 'Métrica Responsive',
        value: 123,
        icon: 'responsive',
        color: 'indigo'
      }
    });

    const card = getByTestId('stats-card');
    
    // Verificar clases responsive
    expect(card).toHaveClass('w-full', 'sm:w-1/2', 'lg:w-1/4');
  });
});
