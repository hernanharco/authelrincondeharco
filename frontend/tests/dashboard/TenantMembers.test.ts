/**
 * Tests para componente TenantMembers.svelte (S3 — approval-tenant-membership)
 *
 * Contrato real: la card "Miembros" de la ficha de tenant
 * (src/pages/dashboard/tenants/[slug].astro) extraída a isla Svelte para
 * gestionar la asignación manual usuario↔tenant:
 *  - Props: tenantId, token (JWT por SSR), members iniciales (SSR) y
 *    allUsers (todos los usuarios del panel, para el selector).
 *  - Renderiza la misma tabla que la página (usuario con avatar, rol de
 *    membresía, estado, logins, último acceso) con una columna extra
 *    "Acciones" con botón "Quitar" por miembro.
 *  - Formulario "Asignar miembro": selector de usuarios que NO son miembros
 *    todavía + selector de rol de membresía (USER por defecto; ADMIN, MANAGER,
 *    USER, VIEWER) + botón "Asignar".
 *  - Asignar → POST /api/v1/tenants/{tenantId}/users con body
 *    { user_id, role } y Authorization: Bearer {token}; tras éxito recarga
 *    la lista (GET .../users) y el usuario sale del selector.
 *  - Quitar → DELETE /api/v1/tenants/{tenantId}/users/{user_id} con el mismo
 *    Bearer; recarga la lista y el usuario vuelve al selector.
 *  - Estados de error (POST/DELETE no ok → mensaje, sin romper la lista) y
 *    envío en curso (botones deshabilitados mientras hay request).
 *  - Estado vacío "Este tenant aún no tiene miembros" (conservado de la página).
 *
 * Intentos descartados (si se implementaran, estos tests fallarían): leer el
 * token de document.cookie, alta sin selector de rol, quitar sin recargar,
 * mostrar usuarios ya asignados en el selector.
 */
import { render, screen, cleanup, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, afterEach, vi } from 'vitest';
import TenantMembers from '../../src/components/dashboard/TenantMembers.svelte';

type TenantMember = {
  id: number;
  username: string;
  email: string;
  role_tenant: string;
  status: string;
  login_count: number;
  last_login: string | null;
};

type PanelUser = { id: number; username: string; email: string };

const TEST_TOKEN = 'test-token-456';
const TENANT_ID = 'tenant-uuid-1';

const alice: TenantMember = {
  id: 1,
  username: 'alice',
  email: 'alice@acme.test',
  role_tenant: 'ADMIN',
  status: 'ACTIVE',
  login_count: 12,
  last_login: '2024-05-10T14:30:00Z',
};

const bob: PanelUser = { id: 2, username: 'bob', email: 'bob@acme.test' };
const carol: PanelUser = { id: 3, username: 'carol', email: 'carol@acme.test' };

function baseProps(members: TenantMember[] = [alice]) {
  return {
    tenantId: TENANT_ID,
    token: TEST_TOKEN,
    members,
    allUsers: [alice as unknown as PanelUser, bob, carol],
  };
}

function okResponse(data: unknown) {
  return { ok: true, json: async () => data } as Response;
}

function failResponse(status = 400) {
  return {
    ok: false,
    status,
    json: async () => ({ detail: 'boom' }),
  } as Response;
}

describe('TenantMembers — tabla de miembros', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('debería renderizar los miembros con email, rol, estado y logins', () => {
    render(TenantMembers, { props: baseProps() });

    expect(screen.getByText('alice')).toBeInTheDocument();
    expect(screen.getByText('alice@acme.test')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument(); // login_count
  });

  it('debería mostrar el estado vacío cuando no hay miembros', () => {
    render(TenantMembers, { props: baseProps([]) });

    expect(screen.getByText('Este tenant aún no tiene miembros')).toBeInTheDocument();
  });

  it('debería tener columna de acciones con botón Quitar por miembro', () => {
    render(TenantMembers, { props: baseProps() });

    expect(screen.getByText('Acciones')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Quitar a alice' })).toBeInTheDocument();
  });
});

describe('TenantMembers — selector de alta', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('debería excluir a los miembros actuales del selector de usuarios', () => {
    render(TenantMembers, { props: baseProps() });

    const select = screen.getByLabelText('Usuario') as HTMLSelectElement;
    const values = Array.from(select.options).map((o) => o.value);

    expect(values).not.toContain('1'); // alice ya es miembro
    expect(values).toContain('2'); // bob
    expect(values).toContain('3'); // carol
    expect(screen.getByRole('option', { name: /bob \(bob@acme\.test\)/ })).toBeInTheDocument();
  });

  it('debería ofrecer los 4 roles de membresía con USER por defecto', () => {
    render(TenantMembers, { props: baseProps() });

    const select = screen.getByLabelText('Rol en el tenant') as HTMLSelectElement;
    const values = Array.from(select.options).map((o) => o.value);

    expect(values).toEqual(['USER', 'ADMIN', 'MANAGER', 'VIEWER']);
    expect(select.value).toBe('USER');
  });
});

describe('TenantMembers — asignación (POST)', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('debería enviar POST con user_id, role y Bearer del token SSR', async () => {
    const fetchMock = vi.fn().mockResolvedValue(okResponse([]));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantMembers, { props: baseProps() });

    await fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: '3' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));

    await waitFor(() => {
      const postCall = fetchMock.mock.calls.find(
        (c) => String(c[0]).includes(`/tenants/${TENANT_ID}/users`) && c[1]?.method === 'POST',
      );
      expect(postCall).toBeTruthy();
      expect(JSON.parse(postCall![1].body)).toEqual({ user_id: 3, role: 'USER' });
      expect(postCall![1].headers).toEqual({
        'Content-Type': 'application/json',
        Authorization: `Bearer ${TEST_TOKEN}`,
      });
    });
  });

  it('tras un POST correcto debería recargar la lista de miembros', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okResponse({ id: 'm-1', user_id: '3', tenant_id: TENANT_ID, role: 'USER' }))
      .mockResolvedValueOnce(
        okResponse([
          alice,
          { ...bob, id: 2, role_tenant: 'USER', status: 'ACTIVE', login_count: 0, last_login: null },
        ]),
      );
    vi.stubGlobal('fetch', fetchMock);

    render(TenantMembers, { props: baseProps() });

    await fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: '2' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));

    await waitFor(() => {
      expect(screen.getByText('bob')).toBeInTheDocument();
    });
    // Y bob sale del selector (ya es miembro)
    await waitFor(() => {
      const select = screen.getByLabelText('Usuario') as HTMLSelectElement;
      expect(Array.from(select.options).map((o) => o.value)).not.toContain('2');
    });
  });

  it('con un POST fallido debería mostrar el error y no romper la lista', async () => {
    const fetchMock = vi.fn().mockResolvedValue(failResponse(404));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantMembers, { props: baseProps() });

    await fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: '2' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Asignar' }));

    await waitFor(() => {
      expect(screen.getAllByText(/boom/).length).toBeGreaterThan(0);
    });
    expect(screen.getByText('alice')).toBeInTheDocument();
  });
});

describe('TenantMembers — baja (DELETE)', () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it('debería enviar DELETE al endpoint del miembro con el Bearer y recargar', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okResponse({ id: 'm-1', user_id: '1', tenant_id: TENANT_ID, role: 'ADMIN' }))
      .mockResolvedValueOnce(okResponse([]));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantMembers, { props: baseProps() });

    await fireEvent.click(screen.getByRole('button', { name: 'Quitar a alice' }));

    await waitFor(() => {
      const del = fetchMock.mock.calls.find((c) => c[1]?.method === 'DELETE');
      expect(del).toBeTruthy();
      expect(String(del![0])).toContain(`/tenants/${TENANT_ID}/users/1`);
      expect(del![1].headers).toEqual({ Authorization: `Bearer ${TEST_TOKEN}` });
    });
    await waitFor(() => {
      expect(screen.queryByText('alice')).not.toBeInTheDocument();
    });
  });

  it('con un DELETE fallido debería mostrar el error y conservar al miembro', async () => {
    const fetchMock = vi.fn().mockResolvedValue(failResponse(404));
    vi.stubGlobal('fetch', fetchMock);

    render(TenantMembers, { props: baseProps() });

    await fireEvent.click(screen.getByRole('button', { name: 'Quitar a alice' }));

    await waitFor(() => {
      expect(screen.getAllByText(/boom/).length).toBeGreaterThan(0);
    });
    expect(screen.getByText('alice')).toBeInTheDocument();
  });
});
