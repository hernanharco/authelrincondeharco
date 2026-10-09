/**
 * Tests para componente TenantUsageTable
 *
 * Contrato real (src/components/dashboard/TenantUsageTable.svelte): props
 * `usage` con filas { slug, name, personas, admins, activas_30d, activos,
 * ultimo_acceso } y `token` (string) con el JWT de sesión que la página
 * recibe por SSR. Renderiza una tabla con columnas Tenant (posición +
 * avatar de iniciales + name sobre slug), Personas, Admins, Activas 30d y
 * Último acceso (fecha formateada, "—" cuando ultimo_acceso es null).
 * Las métricas se muestran como números tabulares y las cabeceras en
 * versalitas. Con `usage` vacío muestra el estado "No hay tenants con
 * usuarios todavía".
 *
 * Presentación de los miembros expandidos: por cada persona, avatar de
 * iniciales (UserAvatar), username en negrita con el email debajo, badges
 * de rol y estado (RoleBadge/StatusBadge, que traducen ADMIN→"Admin" y
 * ACTIVE→"Activo") y el último acceso alineado a la derecha. El rol y el
 * estado se normalizan a mayúsculas antes de pasarlos a los badges.
 *
 * Cada fila es un enlace al detalle del tenant (/dashboard/tenants/{slug})
 * (stretched-link). Además, cada fila tiene un botón chevron
 * (aria-label "Ver miembros de {name}", aria-expanded) que alterna una fila
 * extra <tr><td colspan> con los miembros del tenant SIN navegar. Carga
 * perezosa en el primer expand: GET /api/v1/tenants/by-slug/{slug} → id y
 * después GET /api/v1/tenants/{id}/users, con Authorization: Bearer
 * construido con la prop `token` (el token llega por SSR desde la página;
 * la cookie access_token es httpOnly y el componente NO la lee). Cache por
 * slug (sin refetch al re-expandir). Estados: "Cargando miembros…", error
 * (con enlace al detalle como fallback) y "Sin miembros". DOM colapsado
 * idéntico al original (la fila extra solo aparece expandida).
 *
 * Intentos descartados de comportamiento inexistente (si se implementara,
 * los tests fallarían): prop `loading`, testids, ordenamiento/paginación
 * internos, columna "Activos" visible, formato de fecha "N/A" en lugar
 * de "—", exclusión mutua de filas abiertas (varias pueden estar abiertas),
 * lectura de document.cookie o de la prop `token` desde cualquier sitio que
 * no sean las cabeceras Authorization de los dos fetches.
 */
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, afterEach, vi } from 'vitest';
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

// Token de prueba: llega por prop (SSR), nunca se lee de document.cookie
const TEST_TOKEN = 'test-token-123';

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
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

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
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent);
    expect(headers).toEqual(['Tenant', 'Personas', 'Admins', 'Activas 30d', 'Último acceso']);
  });

  it('debería formatear la fecha de último acceso cuando no es null', () => {
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

    const cell = rowFor('acme').querySelector('td:last-child');
    // Fecha formateada en es-ES (dd/mm/yyyy ...), no el ISO crudo
    expect(cell!.textContent).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(cell!.textContent).not.toContain('2024-05-10T14:30:00Z');
  });

  it('debería mostrar "—" cuando ultimo_acceso es null', () => {
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

    const cell = rowFor('globex').querySelector('td:last-child');
    expect(cell!.textContent).toContain('—');
    expect(cell!.textContent).not.toMatch(/\d{2}\/\d{2}\/\d{4}/);
  });

  it('debería numerar las filas por posición (1 para la primera)', () => {
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

    // El número de posición abre el contenido de la fila del tenant
    expect(rowFor('acme')).toHaveTextContent(/^1/);
    expect(rowFor('globex')).toHaveTextContent(/^2/);
  });

  it('debería enlazar cada fila al detalle del tenant (/dashboard/tenants/{slug})', () => {
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

    const links = screen.getAllByRole('link');
    expect(links).toHaveLength(2);
    expect(links[0]).toHaveAttribute('href', '/dashboard/tenants/acme');
    expect(links[1]).toHaveAttribute('href', '/dashboard/tenants/globex');
  });

  it('debería mostrar el estado vacío cuando usage está vacío', () => {
    render(TenantUsageTable, { props: { usage: [], token: TEST_TOKEN } });

    expect(screen.getByText('No hay tenants con usuarios todavía')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.queryAllByRole('row')).toHaveLength(0);
  });
});

type TenantMember = {
  id: string;
  username: string;
  email: string;
  role_tenant: string;
  status: string;
  login_count: number;
  last_login: string | null;
};

const alice: TenantMember = {
  id: 'u-1',
  username: 'alice',
  email: 'alice@acme.test',
  role_tenant: 'admin',
  status: 'active',
  login_count: 12,
  last_login: '2024-05-10T14:30:00Z',
};

function okResponse(data: unknown) {
  return { ok: true, json: async () => data } as Response;
}

describe('TenantUsageTable — expansión inline de miembros', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('debería renderizar el chevron con aria-expanded=false y no añadir filas extra en colapsado', () => {
    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });

    const buttons = screen.getAllByRole('button', { name: 'Ver miembros de Acme Corp' });
    expect(buttons).toHaveLength(1);
    expect(buttons[0]).toHaveAttribute('aria-expanded', 'false');

    // DOM colapsado idéntico: sin fila extra de miembros
    expect(screen.getAllByRole('row')).toHaveLength(3);
  });

  it('al expandir debería llamar a by-slug y después a users, y renderizar los miembros', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(okResponse({ id: 't-acme', slug: 'acme', name: 'Acme Corp' }))
      .mockResolvedValueOnce(okResponse([alice]));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });
    await fireEvent.click(screen.getByRole('button', { name: 'Ver miembros de Acme Corp' }));

    await screen.findByText('alice');
    expect(screen.getByText('alice@acme.test')).toBeInTheDocument();
    // Rol y estado como badges traducidos (RoleBadge/StatusBadge)
    expect(screen.getByText('Admin')).toBeInTheDocument();
    expect(screen.getByText('Activo')).toBeInTheDocument();
    // Avatar de iniciales del miembro (UserAvatar sobre el username)
    expect(screen.getByText('A')).toBeInTheDocument();
    // Último acceso del miembro formateado (dd/mm/yyyy), no el ISO crudo
    const memberRow = screen.getByText('alice').closest('li');
    expect(memberRow!.textContent).toMatch(/\d{2}\/\d{2}\/\d{4}/);
    expect(memberRow!.textContent).not.toContain('2024-05-10T14:30:00Z');

    const button = screen.getByRole('button', { name: 'Ver miembros de Acme Corp' });
    expect(button).toHaveAttribute('aria-expanded', 'true');

    const urls = fetchMock.mock.calls.map((c) => String(c[0]));
    expect(urls).toHaveLength(2);
    expect(urls[0]).toContain('/api/v1/tenants/by-slug/acme');
    expect(urls[1]).toContain('/api/v1/tenants/t-acme/users');
    // Los DOS fetches (by-slug y users) envían el token de la prop
    for (const call of fetchMock.mock.calls) {
      expect((call[1] as RequestInit).headers).toMatchObject({
        Authorization: `Bearer ${TEST_TOKEN}`,
      });
    }
  });

  it('al re-expandir no debería volver a fetchear (cache por slug)', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(okResponse({ id: 't-acme', slug: 'acme', name: 'Acme Corp' }))
      .mockResolvedValueOnce(okResponse([alice]));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });
    const button = () => screen.getByRole('button', { name: 'Ver miembros de Acme Corp' });

    await fireEvent.click(button());
    await screen.findByText('alice');
    expect(fetchMock).toHaveBeenCalledTimes(2);

    await fireEvent.click(button()); // colapsar
    expect(screen.queryByText('alice')).not.toBeInTheDocument();

    await fireEvent.click(button()); // re-expandir: sin refetch
    await screen.findByText('alice');
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it('si el fetch falla debería mostrar un error sin crashear y conservar el enlace al detalle', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 500, json: async () => ({ detail: 'boom' }) } as Response);
    vi.stubGlobal('fetch', fetchMock);

    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });
    await fireEvent.click(screen.getByRole('button', { name: 'Ver miembros de Acme Corp' }));

    const error = await screen.findByText(/No se pudieron cargar los miembros/);
    expect(error).toBeInTheDocument();

    // Fallback: enlace al detalle del tenant dentro del panel de error
    const fallback = screen.getByRole('link', { name: 'Ver ficha completa del tenant' });
    expect(fallback).toHaveAttribute('href', '/dashboard/tenants/acme');
    // El enlace de la fila sigue existiendo también
    expect(screen.getAllByRole('link').length).toBeGreaterThanOrEqual(2);
  });

  it('la lista vacía debería mostrar "Sin miembros"', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(okResponse({ id: 't-acme', slug: 'acme', name: 'Acme Corp' }))
      .mockResolvedValueOnce(okResponse([]));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });
    await fireEvent.click(screen.getByRole('button', { name: 'Ver miembros de Acme Corp' }));

    expect(await screen.findByText('Sin miembros')).toBeInTheDocument();
  });

  it('click en el chevron no debe navegar a la página de detalle', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(okResponse({ id: 't-acme', slug: 'acme', name: 'Acme Corp' }))
      .mockResolvedValueOnce(okResponse([alice]));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantUsageTable, { props: { usage: mockUsage, token: TEST_TOKEN } });
    await fireEvent.click(screen.getByRole('button', { name: 'Ver miembros de Acme Corp' }));

    // La ruta no cambia (sin navegación) y el toggle se ejecutó (miembros visibles)
    expect(window.location.pathname).toBe('/');
    await waitFor(() => expect(screen.getByText('alice')).toBeInTheDocument());
  });
});
