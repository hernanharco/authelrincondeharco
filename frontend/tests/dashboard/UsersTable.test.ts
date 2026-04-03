/**
 * Tests para componente UsersTable
 * Tabla de usuarios con filtros, paginación y acciones
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import UsersTable from '../../src/components/dashboard/UsersTable.svelte';

describe('UsersTable', () => {
  const mockUsers = [
    {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      full_name: 'Administrator',
      role: 'ADMIN',
      status: 'ACTIVE',
      is_active: true,
      is_locked: false,
      created_at: '2024-01-01T00:00:00Z',
      last_login: '2024-01-15T10:30:00Z'
    },
    {
      id: 2,
      username: 'user1',
      email: 'user1@example.com',
      full_name: 'User One',
      role: 'USER',
      status: 'ACTIVE',
      is_active: true,
      is_locked: false,
      created_at: '2024-01-02T00:00:00Z',
      last_login: null
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('debería renderizar tabla con usuarios', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('user1')).toBeInTheDocument();
    expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    expect(screen.getByText('user1@example.com')).toBeInTheDocument();
  });

  it('debería mostrar estado de carga', () => {
    render(UsersTable, {
      props: {
        users: [],
        loading: true
      }
    });

    expect(screen.getByText('Cargando usuarios...')).toBeInTheDocument();
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('debería mostrar mensaje cuando no hay usuarios', () => {
    render(UsersTable, {
      props: {
        users: [],
        loading: false
      }
    });

    expect(screen.getByText('No se encontraron usuarios')).toBeInTheDocument();
  });

  it('debería renderizar badges de rol y estado', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    // Verificar badges de rol
    expect(screen.getByText('ADMIN')).toBeInTheDocument();
    expect(screen.getByText('USER')).toBeInTheDocument();

    // Verificar badges de estado
    expect(screen.getAllByText('ACTIVE')).toHaveLength(2);
  });

  it('debería mostrar avatares de usuarios', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    const avatars = screen.getAllByTestId('user-avatar');
    expect(avatars).toHaveLength(2);
    
    // Verificar iniciales
    expect(avatars[0]).toHaveTextContent('A'); // Admin
    expect(avatars[1]).toHaveTextContent('U'); // User One
  });

  it('debería formatear fechas correctamente', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    // Verificar formato de fecha
    expect(screen.getByText('01/01/2024')).toBeInTheDocument();
    expect(screen.getByText('02/01/2024')).toBeInTheDocument();
    
    // Verificar formato de último login
    expect(screen.getByText('15/01/2024 10:30')).toBeInTheDocument();
  });

  it('debería mostrar acciones para cada usuario', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    // Verificar botones de acción
    const editButtons = screen.getAllByRole('button', { name: 'Editar' });
    const lockButtons = screen.getAllByRole('button', { name: 'Bloquear' });
    
    expect(editButtons).toHaveLength(2);
    expect(lockButtons).toHaveLength(2);
  });

  it('debería manejar filtros de búsqueda', async () => {
    const mockOnFilter = vi.fn();
    
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false,
        onFilter: mockOnFilter
      }
    });

    const searchInput = screen.getByPlaceholderText('Buscar usuarios...');
    fireEvent.input(searchInput, { target: { value: 'admin' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenCalledWith({
        search: 'admin',
        role: null,
        status: null
      });
    });
  });

  it('debería manejar filtros de rol', async () => {
    const mockOnFilter = vi.fn();
    
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false,
        onFilter: mockOnFilter
      }
    });

    const roleSelect = screen.getByLabelText('Filtrar por rol');
    fireEvent.change(roleSelect, { target: { value: 'ADMIN' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenCalledWith({
        search: '',
        role: 'ADMIN',
        status: null
      });
    });
  });

  it('debería manejar filtros de estado', async () => {
    const mockOnFilter = vi.fn();
    
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false,
        onFilter: mockOnFilter
      }
    });

    const statusSelect = screen.getByLabelText('Filtrar por estado');
    fireEvent.change(statusSelect, { target: { value: 'ACTIVE' } });

    await waitFor(() => {
      expect(mockOnFilter).toHaveBeenCalledWith({
        search: '',
        role: null,
        status: 'ACTIVE'
      });
    });
  });

  it('debería manejar paginación', async () => {
    const mockOnPageChange = vi.fn();
    
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false,
        pagination: {
          page: 1,
          limit: 10,
          total: 25
        },
        onPageChange: mockOnPageChange
      }
    });

    // Verificar controles de paginación
    expect(screen.getByText('Página 1 de 3')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeInTheDocument();

    // Click en siguiente
    const nextButton = screen.getByRole('button', { name: 'Siguiente' });
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(mockOnPageChange).toHaveBeenCalledWith(2);
    });
  });

  it('debería manejar ordenamiento', async () => {
    const mockOnSort = vi.fn();
    
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false,
        onSort: mockOnSort
      }
    });

    // Click en encabezado de tabla para ordenar
    const usernameHeader = screen.getByText('Username');
    fireEvent.click(usernameHeader);

    await waitFor(() => {
      expect(mockOnSort).toHaveBeenCalledWith('username');
    });
  });

  it('debería ser accesible', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    const table = screen.getByRole('table');
    
    // Verificar atributos de accesibilidad
    expect(table).toHaveAttribute('role', 'table');
    expect(table).toHaveAttribute('aria-label', 'Lista de usuarios');
    
    // Verificar encabezados
    const headers = screen.getAllByRole('columnheader');
    expect(headers.length).toBeGreaterThan(0);
    
    // Verificar celdas de datos
    const cells = screen.getAllByRole('cell');
    expect(cells.length).toBeGreaterThan(0);
  });

  it('debería ser responsive', () => {
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false
      }
    });

    const table = screen.getByRole('table');
    const container = table.parentElement;
    
    // Verificar clases responsive
    expect(container).toHaveClass('w-full', 'overflow-x-auto');
  });

  it('debería manejar selección de usuarios', async () => {
    const mockOnSelect = vi.fn();
    
    render(UsersTable, {
      props: {
        users: mockUsers,
        loading: false,
        selectable: true,
        onSelect: mockOnSelect
      }
    });

    // Seleccionar primer usuario
    const firstUserCheckbox = screen.getByLabelText('Seleccionar usuario admin');
    fireEvent.click(firstUserCheckbox);

    await waitFor(() => {
      expect(mockOnSelect).toHaveBeenCalledWith([mockUsers[0]]);
    });
  });

  it('debería mostrar usuarios filtrados', () => {
    const filteredUsers = [mockUsers[0]]; // Solo admin
    
    render(UsersTable, {
      props: {
        users: filteredUsers,
        loading: false
      }
    });

    // Verificar que solo muestra el usuario filtrado
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.queryByText('user1')).not.toBeInTheDocument();
  });
});
