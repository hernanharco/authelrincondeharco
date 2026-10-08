/**
 * Tests para componente StatsCard
 *
 * Contrato real (src/components/dashboard/StatsCard.svelte): props `title`,
 * `value` (string | number, renderizado TAL CUAL sin formateo), `iconName`
 * opcional, `trend` { value, isPositive } y `color`
 * (primary|success|warning|danger|muted) que decide las clases del contenedor
 * del icono. No hay testids, ni role/aria-label, ni formateo numérico.
 *
 * Intentos descartados de la versión anterior (comportamiento inexistente):
 * props `icon`/`color` con valores arbitrarios ("blue", "green"), testids
 * `stats-card`/`stats-icon`, formateo "1.23M", role="article"/aria-label,
 * etiquetas H3, clases Tailwind fijas de la tarjeta y clases responsive.
 */
import { render, screen, cleanup } from '@testing-library/svelte';
import { describe, it, expect, afterEach, vi } from 'vitest';
import StatsCard from '../../src/components/dashboard/StatsCard.svelte';

function iconBox(container: HTMLElement): HTMLElement | null {
  return container.querySelector<HTMLElement>('[style*="48px"]');
}

describe('StatsCard', () => {
  afterEach(() => {
    cleanup();
  });

  it('debería renderizar título y valor numérico', () => {
    render(StatsCard, { props: { title: 'Usuarios Activos', value: 150 } });

    const title = screen.getByText('Usuarios Activos');
    const value = screen.getByText('150');
    expect(title.tagName).toBe('P');
    expect(value.tagName).toBe('P');
  });

  it('debería renderizar el valor tal cual, sin formateo numérico', () => {
    render(StatsCard, { props: { title: 'Total Sesiones', value: 1234567 } });

    expect(screen.getByText('1234567')).toBeInTheDocument();
    expect(screen.queryByText(/1\.23M/)).not.toBeInTheDocument();
  });

  it('debería manejar el valor cero correctamente', () => {
    render(StatsCard, { props: { title: 'Nuevos Usuarios', value: 0 } });

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('debería renderizar el contenedor del icono con el color por defecto (primary)', () => {
    const { container } = render(StatsCard, {
      props: { title: 'Total Usuarios', value: 500, iconName: 'user' },
    });

    const box = iconBox(container);
    expect(box).not.toBeNull();
    expect(box).toHaveClass('bg-[#6366F1]/10', 'text-[#6366F1]');
    expect(box!.querySelector('svg')).toBeInTheDocument();
  });

  it('debería aplicar las clases del color elegido al contenedor del icono', () => {
    const { container } = render(StatsCard, {
      props: { title: 'Usuarios Pendientes', value: 25, iconName: 'pending', color: 'danger' },
    });

    const box = iconBox(container);
    expect(box).not.toBeNull();
    expect(box).toHaveClass('bg-[#EF4444]/10', 'text-[#EF4444]');
  });

  it('no debería renderizar contenedor de icono sin iconName', () => {
    const { container } = render(StatsCard, {
      props: { title: 'Estadística Simple', value: 42 },
    });

    expect(screen.getByText('Estadística Simple')).toBeInTheDocument();
    expect(screen.getByText('42')).toBeInTheDocument();
    expect(iconBox(container)).toBeNull();
  });

  it('debería mostrar el trend positivo con su clase de color', () => {
    render(StatsCard, {
      props: { title: 'Usuarios Online', value: 100, trend: { value: 12, isPositive: true } },
    });

    const pct = screen.getByText('12%');
    expect(pct.closest('div')).toHaveClass('text-[#10B981]');
  });

  it('debería mostrar el valor absoluto del trend negativo en rojo', () => {
    render(StatsCard, {
      props: { title: 'Conversión', value: 85, trend: { value: -5, isPositive: false } },
    });

    const pct = screen.getByText('5%');
    expect(pct.closest('div')).toHaveClass('text-[#EF4444]');
  });

  it('no debería renderizar indicador de trend sin la prop trend', () => {
    render(StatsCard, { props: { title: 'Métrica', value: 999 } });

    expect(screen.getByText('999')).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it('debería actualizar el valor al cambiar las props', async () => {
    const { rerender } = render(StatsCard, {
      props: { title: 'Usuarios Online', value: 100 },
    });

    expect(screen.getByText('100')).toBeInTheDocument();

    await rerender({ title: 'Usuarios Online', value: 150 });

    expect(screen.queryByText('100')).not.toBeInTheDocument();
    expect(screen.getByText('150')).toBeInTheDocument();
  });

  it('debería renderizar solo con title y value (props opcionales omitidas)', () => {
    const { container } = render(StatsCard, {
      props: { title: 'Mínimo', value: '1,2 k' },
    });

    expect(screen.getByText('Mínimo')).toBeInTheDocument();
    expect(screen.getByText('1,2 k')).toBeInTheDocument();
    expect(iconBox(container)).toBeNull();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });
});
