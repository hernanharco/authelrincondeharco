/**
 * Tests para componente TenantUsageTable
 *
 * Contrato real (src/components/dashboard/TenantUsageTable.svelte): prop
 * `usage` con filas { slug, name, personas, admins, activas_30d, activos,
 * ultimo_acceso }. Renderiza una tabla HTML plana con columnas Tenant
 * (name + slug), Personas, Admins, Activas 30d y Último acceso (fecha
 * formateada, "—" cuando ultimo_acceso es null). Con `usage` vacío muestra
 * el estado "No hay tenants con usuarios todavía".
 *
 * Intentos descartados de comportamiento inexistente (si se implementara,
 * los tests fallarían): prop `loading`, testids, ordenamiento/paginación
 * internos, enlaces por fila, columna "Activos" visible, formato de fecha
 * "N/A" en lugar de "—".
 */
import { render, screen, cleanup } from '@testing-library/svelte';
import { describe, it, expect, afterEach } from 'vitest';
import TenantUsageTable from '../../src/components/dashboard/TenantUsageTable.svelte';

type UsageRow = {
  slug: string;
  name: string;
  personas: number;
  admins: number;
  activas_30d: number;
  activos: number;
  ultimo_acceso: string | null;
};

const mockUsage: UsageRow[] = [
  {
    slug: 'acme',
    name: 'Acme Corp',
    personas: 42,
    admins: 3,
    activas_30d: 17,
    activos: 5,
    ultimo_acceso: '2024-05-10T14:30:00Z',
  },
  {
    slug: 'globex',
    name: 'Globex',
    personas: 8,
    admins: 1,
    activas_30d: 2,
    activos: 0,
    ultimo_acceso: null,
  },
];

function rowFor(slug: string): HTMLElement {
  const cell = screen.getByText(slug);
  const row = cell.closest('tr');
  if (!row) throw new Error(`No se encontró la fila del tenant ${slug}`);
  return row as HTMLElement;
}

describe('TenantUsageTable', () => {
  afterEach(() => {
    cleanup();
  });

  it('debería renderizar una fila por tenant con nombre, slug y métricas', () => {
    render(TenantUsageTable, { props: { usage: mockUsage } });

    expect(screen.getAllByRole('row')).toHaveLength(3); // cabecera + 2 filas

    const acmeRow = rowFor('acme');
    expect(acmeRow).toHaveTextContent('Acme Corp');
    expect(acmeRow).toHaveTextContent('42'); // personas
    expect(acmeRow).toHaveTextContent('3'); // admins
    expect(acmeRow).toHaveTextContent('17'); // activas_30d

    const globexRow = rowFor('globex');
    expect(globexRow).toHaveTextContent('Globex');
    expect(globexRow).toHaveTextContent('8');
    expect(globexRow).toHaveTextContent('1');
    expect(globexRow).toHaveTextContent('2');
  });

  it('debería mostrar las cabeceras de columnas en español', () => {
    render(TenantUsageTable, { props: { usage: mockUsage } });

    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent);
    expect(headers).toEqual(['Tenant', 'Personas', 'Admins', 'Activas 30d', 'Último acceso']);
  });

  it('debería formatear la fecha de último acceso cuando no es null', () => {
    render(TenantUsageTable, { props: { usage: mockUsage } });

    const cell = rowFor('acme').querySelector('td:last-child');
    // Fecha formateada en es-ES (dd/mm/yyyy ...), no el ISO crudo
    expect(cell!.textContent).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(cell!.textContent).not.toContain('2024-05-10T14:30:00Z');
  });

  it('debería mostrar "—" cuando ultimo_acceso es null', () => {
    render(TenantUsageTable, { props: { usage: mockUsage } });

    const cell = rowFor('globex').querySelector('td:last-child');
    expect(cell!.textContent).toContain('—');
    expect(cell!.textContent).not.toMatch(/\d{2}\/\d{2}\/\d{4}/);
  });

  it('debería mostrar el estado vacío cuando usage está vacío', () => {
    render(TenantUsageTable, { props: { usage: [] } });

    expect(screen.getByText('No hay tenants con usuarios todavía')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.queryAllByRole('row')).toHaveLength(0);
  });
});
