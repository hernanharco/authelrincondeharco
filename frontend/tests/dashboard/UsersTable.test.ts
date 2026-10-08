/**
 * Tests para componente UsersTable
 *
 * Contrato real (src/components/dashboard/UsersTable.svelte): props `users`,
 * `onUserUpdate`, `onUserDelete`, `onUserLock`; el filtrado (búsqueda, rol,
 * estado, origen) y la paginación (20 por página) son INTERNOS. Las acciones
 * se renderizan en cada fila: enlace "Ver detalle", bloquear/desbloquear y
 * eliminar (con confirm), y los cambios de rol/estado vía los badges editables
 * de RoleBadge/StatusBadge que notifican a través de onUserUpdate.
 *
 * Intentos descartados de la versión anterior (comportamiento inexistente):
 * prop `loading` + "Cargando usuarios...", mensaje "No se encontraron
 * usuarios", callbacks `onFilter`/`onSort`/`onPageChange`/`onSelect`,
 * prop `pagination` controlada desde fuera, `selectable` + checkboxes de fila,
 * botones "Editar"/"Bloquear" con texto, ordenamiento por cabecera, aria-label
 * en la tabla, testid `user-avatar`, fechas de creación formateadas en la fila
 * y clases responsive fijas del contenedor.
 */
import { render, screen, fireEvent, within, cleanup } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import UsersTable from '../../src/components/dashboard/UsersTable.svelte';

const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();

type MockUser = {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string;
  status: string;
  origin?: string;
  created_at: string;
  last_login: string | null;
  is_locked: boolean;
};

const mockUsers: MockUser[] = [
  {
    id: 1,
    username: 'admin',
    email: 'admin@example.com',
    full_name: 'Administrator',
    role: 'ADMIN',
    status: 'ACTIVE',
    origin: 'https://github.com',
    created_at: '2024-01-01T00:00:00Z',
    last_login: twoHoursAgo,
    is_locked: false,
  },
  {
    id: 2,
    username: 'user1',
    email: 'user1@example.com',
    full_name: 'User One',
    role: 'USER',
    status: 'PENDING',
    created_at: '2024-01-02T00:00:00Z',
    last_login: null,
    is_locked: true,
  },
];

function makeUsers(count: number): MockUser[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    username: `user${String(i + 1).padStart(2, '0')}`,
    email: `user${i + 1}@example.com`,
    role: 'USER',
    status: 'ACTIVE',
    origin: 'https://example.com',
    created_at: '2024-01-01T00:00:00Z',
    last_login: null,
    is_locked: false,
  }));
}

function rowFor(username: string): HTMLElement {
  const cell = screen.getByText(`@${username}`);
  const row = cell.closest('tr');
  if (!row) throw new Error(`No se encontró la fila de @${username}`);
  return row as HTMLElement;
}

describe('UsersTable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('debería renderizar una fila por usuario con nombre, @usuario y email', () => {
    render(UsersTable, { props: { users: mockUsers } });

    expect(screen.getByText('Administrator')).toBeInTheDocument();
    expect(screen.getByText('@admin')).toBeInTheDocument();
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('User One')).toBeInTheDocument();
    expect(screen.getByText('@user1')).toBeInTheDocument();
    expect(screen.getByText('user1@example.com')).toBeInTheDocument();
    expect(screen.getAllByRole('row')).toHaveLength(3); // cabecera + 2 filas
  });

  it('debería renderizar los badges de rol y estado con sus etiquetas', () => {
    render(UsersTable, { props: { users: mockUsers } });

    const adminRow = rowFor('admin');
    const userRow = rowFor('user1');

    expect(within(adminRow).getByText('Admin')).toBeInTheDocument();
    expect(within(adminRow).getByText('Activo')).toBeInTheDocument();
    expect(within(userRow).getByText('Usuario')).toBeInTheDocument();
    expect(within(userRow).getByText('Pendiente')).toBeInTheDocument();
  });

  it('debería mostrar el origen como dominio o "Desconocido"', () => {
    render(UsersTable, { props: { users: mockUsers } });

    expect(within(rowFor('admin')).getByText('github.com')).toBeInTheDocument();
    expect(within(rowFor('user1')).getByText('Desconocido')).toBeInTheDocument();
  });

  it('debería mostrar las iniciales del avatar de cada usuario', () => {
    render(UsersTable, { props: { users: mockUsers } });

    expect(within(rowFor('admin')).getByText('A')).toBeInTheDocument();
    expect(within(rowFor('user1')).getByText('UO')).toBeInTheDocument();
  });

  it('debería mostrar el último login en relativo o "Nunca"', () => {
    render(UsersTable, { props: { users: mockUsers } });

    expect(within(rowFor('admin')).getByText('hace 2 horas')).toBeInTheDocument();
    expect(within(rowFor('user1')).getByText('Nunca')).toBeInTheDocument();
  });

  it('debería enlazar el detalle de cada usuario', () => {
    render(UsersTable, { props: { users: mockUsers } });

    const link = within(rowFor('admin')).getByTitle('Ver detalle');
    expect(link).toHaveAttribute('href', '/dashboard/users/1');
    expect(within(rowFor('user1')).getByTitle('Ver detalle')).toHaveAttribute(
      'href',
      '/dashboard/users/2'
    );
  });

  it('debería invocar onUserLock con el estado invertido (bloquear/desbloquear)', async () => {
    const onUserLock = vi.fn();
    render(UsersTable, { props: { users: mockUsers, onUserLock } });

    // admin está desbloqueado → acción "Bloquear"
    await fireEvent.click(within(rowFor('admin')).getByTitle('Bloquear'));
    expect(onUserLock).toHaveBeenCalledWith(1, true);

    // user1 está bloqueado → acción "Desbloquear"
    await fireEvent.click(within(rowFor('user1')).getByTitle('Desbloquear'));
    expect(onUserLock).toHaveBeenCalledWith(2, false);
  });

  it('debería confirmar y notificar onUserDelete al eliminar', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);
    const onUserDelete = vi.fn();
    render(UsersTable, { props: { users: mockUsers, onUserDelete } });

    await fireEvent.click(within(rowFor('admin')).getByTitle('Eliminar'));

    expect(confirmSpy).toHaveBeenCalledWith('¿Estás seguro de eliminar este usuario?');
    expect(onUserDelete).toHaveBeenCalledWith(1);
  });

  it('no debería eliminar si se cancela la confirmación', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const onUserDelete = vi.fn();
    render(UsersTable, { props: { users: mockUsers, onUserDelete } });

    await fireEvent.click(within(rowFor('admin')).getByTitle('Eliminar'));

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(onUserDelete).not.toHaveBeenCalled();
  });

  it('debería notificar onUserUpdate al cambiar el rol desde el badge editable', async () => {
    const onUserUpdate = vi.fn();
    render(UsersTable, { props: { users: mockUsers, onUserUpdate } });

    const roleBadge = screen.getByRole('button', { name: 'Admin' });
    await fireEvent.click(roleBadge);

    // El desplegable vive en el mismo contenedor que el badge
    await fireEvent.click(within(roleBadge.parentElement!).getByRole('button', { name: 'Usuario' }));

    expect(onUserUpdate).toHaveBeenCalledWith(1, 'role', 'USER');
  });

  it('debería notificar onUserUpdate al cambiar el estado desde el badge editable', async () => {
    const onUserUpdate = vi.fn();
    render(UsersTable, { props: { users: mockUsers, onUserUpdate } });

    const statusBadge = screen.getByRole('button', { name: 'Activo' });
    await fireEvent.click(statusBadge);

    await fireEvent.click(
      within(statusBadge.parentElement!).getByRole('button', { name: 'Suspendido' })
    );

    expect(onUserUpdate).toHaveBeenCalledWith(1, 'status', 'SUSPENDED');
  });

  it('debería filtrar por búsqueda sobre username, nombre y email', async () => {
    render(UsersTable, { props: { users: mockUsers } });
    const search = screen.getByLabelText('Buscar');

    await fireEvent.input(search, { target: { value: 'admin' } });
    expect(screen.getByText('@admin')).toBeInTheDocument();
    expect(screen.queryByText('@user1')).not.toBeInTheDocument();

    await fireEvent.input(search, { target: { value: 'one' } }); // full_name "User One"
    expect(screen.getByText('@user1')).toBeInTheDocument();
    expect(screen.queryByText('@admin')).not.toBeInTheDocument();

    await fireEvent.input(search, { target: { value: 'admin@example.com' } }); // email
    expect(screen.getByText('@admin')).toBeInTheDocument();
    expect(screen.queryByText('@user1')).not.toBeInTheDocument();
  });

  it('debería dejar la tabla vacía cuando la búsqueda no tiene resultados', async () => {
    render(UsersTable, { props: { users: mockUsers } });

    await fireEvent.input(screen.getByLabelText('Buscar'), { target: { value: 'zzz' } });

    // No existe mensaje de "sin resultados": solo la tabla sin filas
    expect(screen.getAllByRole('row')).toHaveLength(1);
    expect(screen.queryByText('@admin')).not.toBeInTheDocument();
  });

  it('debería filtrar por rol con el select interno', async () => {
    render(UsersTable, { props: { users: mockUsers } });

    await fireEvent.change(screen.getByLabelText('Rol'), { target: { value: 'ADMIN' } });

    expect(screen.getByText('@admin')).toBeInTheDocument();
    expect(screen.queryByText('@user1')).not.toBeInTheDocument();
  });

  it('debería filtrar por estado con el select interno', async () => {
    render(UsersTable, { props: { users: mockUsers } });

    await fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'PENDING' } });

    expect(screen.getByText('@user1')).toBeInTheDocument();
    expect(screen.queryByText('@admin')).not.toBeInTheDocument();
  });

  it('debería filtrar por origen con el select interno', async () => {
    render(UsersTable, { props: { users: mockUsers } });

    await fireEvent.change(screen.getByLabelText('Origen'), {
      target: { value: 'https://github.com' },
    });

    expect(screen.getByText('@admin')).toBeInTheDocument();
    expect(screen.queryByText('@user1')).not.toBeInTheDocument();
  });

  it('debería paginar internamente con más de 20 usuarios', async () => {
    render(UsersTable, { props: { users: makeUsers(25) } });

    expect(screen.getByText(/Mostrando 20 de 25 usuarios/)).toBeInTheDocument();
    expect(screen.getByText(/Página 1 de 2/)).toBeInTheDocument();

    const prev = screen.getByRole('button', { name: 'Anterior' });
    const next = screen.getByRole('button', { name: 'Siguiente' });
    expect(prev).toBeDisabled();
    expect(next).toBeEnabled();

    await fireEvent.click(next);
    expect(screen.getByText(/Página 2 de 2/)).toBeInTheDocument();
    expect(screen.getByText(/Mostrando 5 de 25 usuarios/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeEnabled();

    await fireEvent.click(screen.getByRole('button', { name: 'Anterior' }));
    expect(screen.getByText(/Página 1 de 2/)).toBeInTheDocument();
    expect(screen.getByText(/Mostrando 20 de 25 usuarios/)).toBeInTheDocument();
  });

  it('no debería mostrar controles de paginación cuando todo cabe en una página', () => {
    render(UsersTable, { props: { users: mockUsers } });

    expect(screen.queryByText(/Mostrando/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Página/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Anterior' })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Siguiente' })).not.toBeInTheDocument();
  });

  it('debería exponer la exportación a CSV', () => {
    render(UsersTable, { props: { users: mockUsers } });

    // Solo se comprueba la presencia: la descarga usa URL.createObjectURL/anchor
    // click, APIs de navegador no disponibles en jsdom.
    expect(screen.getByRole('button', { name: 'Exportar CSV' })).toBeInTheDocument();
  });

  it('debería renderizar la tabla con sus cabeceras y contenedor con scroll horizontal', () => {
    render(UsersTable, { props: { users: mockUsers } });

    const headers = screen.getAllByRole('columnheader').map((th) => th.textContent);
    expect(headers).toEqual([
      'Usuario',
      'Email',
      'Origen',
      'Rol',
      'Estado',
      'Último login',
      'Acciones',
    ]);

    const table = screen.getByRole('table');
    expect(table).toHaveClass('w-full');
    expect(table.parentElement).toHaveClass('overflow-x-auto');
    expect(screen.getAllByRole('row')).toHaveLength(3);
  });
});
