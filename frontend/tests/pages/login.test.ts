/**
 * Tests para la página de login (src/pages/login.astro)
 *
 * Astro pages no se pueden renderizar con testing-library, así que aquí se
 * testean las unidades reales que la página cablea:
 *  - LoginForm.svelte  → comportamiento del formulario (envío, loading, éxito/error)
 *  - AuthAlert.svelte  → manejo de los query params `status`/`error` de la URL
 * El resto de la página es markup estático de Layout/PendingApproval/GoogleButton
 * (GoogleButton/LoginForm-tácticos viven en tests/auth/, batch siguiente).
 */
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, afterEach, afterAll, vi } from 'vitest';
import LoginForm from '../../src/components/auth/LoginForm.svelte';
import AuthAlert from '../../src/components/auth/AuthAlert.svelte';
import { authService } from '../../src/services/authService';

// La página usa este servicio vía LoginForm; lo mockeamos a nivel de módulo.
vi.mock('../../src/services/authService', () => ({
  authService: { login: vi.fn() },
}));

const mockLogin = vi.mocked(authService.login);

// jsdom bloquea redefinir window.location; se sustituye en globalThis
// para poder asertar la navegación que hace LoginForm tras el login.
const originalLocationDescriptor = Object.getOwnPropertyDescriptor(globalThis, 'location');
function stubLocation(origin: string): { origin: string; href: string } {
  const fake = { origin, href: '' };
  Object.defineProperty(globalThis, 'location', {
    value: fake,
    writable: true,
    configurable: true,
    enumerable: true,
  });
  return fake;
}

const USER = {
  id: '1',
  email: 'alice@example.com',
  username: 'alice',
  full_name: 'Alice',
  role: 'ADMIN',
  status: 'active',
};

function fillForm(username = 'alice', password = 'secret') {
  fireEvent.input(screen.getByLabelText('Nombre de usuario'), { target: { value: username } });
  fireEvent.input(screen.getByLabelText('Contraseña'), { target: { value: password } });
}

describe('Login Page → LoginForm', () => {
  let fakeLocation: { origin: string; href: string };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    fakeLocation = stubLocation('http://localhost:4321');
  });

  afterEach(() => {
    cleanup();
  });

  afterAll(() => {
    if (originalLocationDescriptor) {
      Object.defineProperty(globalThis, 'location', originalLocationDescriptor);
    }
  });

  it('debería renderizar el formulario con labels accesibles', () => {
    render(LoginForm);

    expect(screen.getByLabelText('Nombre de usuario')).toBeInTheDocument();
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Entrar al sistema' })).toBeInTheDocument();
  });

  it('debería tener campos obligatorios (required)', () => {
    render(LoginForm);

    expect(screen.getByLabelText('Nombre de usuario')).toBeRequired();
    expect(screen.getByLabelText('Contraseña')).toBeRequired();
  });

  it('debería mantener el botón deshabilitado con campos vacíos', () => {
    render(LoginForm);

    expect(screen.getByRole('button', { name: 'Entrar al sistema' })).toBeDisabled();
  });

  it('debería habilitar el botón al completar usuario y contraseña', () => {
    render(LoginForm);

    fillForm();

    expect(screen.getByRole('button', { name: 'Entrar al sistema' })).toBeEnabled();
  });

  it('debería enviar las credenciales a authService.login', async () => {
    mockLogin.mockResolvedValue({ access_token: 'jwt', token_type: 'bearer', user: USER });
    render(LoginForm);

    fillForm('bob', 'hunter2');
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({ username: 'bob', password: 'hunter2' });
    });
  });

  it('debería mostrar estado de carga (Validando…, campos deshabilitados)', async () => {
    mockLogin.mockReturnValue(new Promise(() => {})); // nunca resuelve
    render(LoginForm);

    fillForm();
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));

    expect(await screen.findByText('Validando...')).toBeInTheDocument();
    expect(screen.getByLabelText('Nombre de usuario')).toBeDisabled();
    expect(screen.getByLabelText('Contraseña')).toBeDisabled();
    expect(screen.getByRole('button', { name: /Validando/ })).toBeDisabled();
  });

  it('debería mostrar éxito y guardar el usuario en localStorage tras un login ok', async () => {
    mockLogin.mockResolvedValue({ access_token: 'jwt', token_type: 'bearer', user: USER });
    render(LoginForm);

    fillForm();
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));

    expect(await screen.findByText('¡Sesión iniciada con éxito!')).toBeInTheDocument();
    expect(JSON.parse(localStorage.getItem('auth_user')!)).toEqual(USER);
    expect(screen.getByRole('button', { name: 'Entrar al sistema' })).toBeEnabled();
  });

  it('debería navegar al destino relativo tras el login (redirectParam)', async () => {
    mockLogin.mockResolvedValue({ access_token: 'jwt', token_type: 'bearer', user: USER });
    render(LoginForm, { props: { redirectParam: '/dashboard' } });

    fillForm();
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));

    await waitFor(() => {
      expect(fakeLocation.href).toBe('http://localhost:4321/dashboard');
    });
  });

  it('debería usar una URL absoluta de redirectParam tal cual', async () => {
    mockLogin.mockResolvedValue({ access_token: 'jwt', token_type: 'bearer', user: USER });
    render(LoginForm, { props: { redirectParam: 'https://otro-sitio.com/home' } });

    fillForm();
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));

    await waitFor(() => {
      expect(fakeLocation.href).toBe('https://otro-sitio.com/home');
    });
  });

  it('debería mostrar el error del backend y no persistir nada si el login falla', async () => {
    mockLogin.mockRejectedValue(new Error('Credenciales inválidas'));
    render(LoginForm);

    fillForm('wronguser', 'wrongpass');
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));

    expect(await screen.findByText('Credenciales inválidas')).toBeInTheDocument();
    expect(localStorage.getItem('auth_user')).toBeNull();
    expect(screen.getByRole('button', { name: 'Entrar al sistema' })).toBeEnabled();
  });

  it('debería limpiar el mensaje de error al volver a escribir', async () => {
    mockLogin.mockRejectedValue(new Error('Credenciales inválidas'));
    render(LoginForm);

    fillForm();
    await fireEvent.click(screen.getByRole('button', { name: 'Entrar al sistema' }));
    expect(await screen.findByText('Credenciales inválidas')).toBeInTheDocument();

    await fireEvent.input(screen.getByLabelText('Nombre de usuario'), {
      target: { value: 'alice2' },
    });

    await waitFor(() => {
      expect(screen.queryByText('Credenciales inválidas')).not.toBeInTheDocument();
    });
  });
});

describe('Login Page → AuthAlert (query params status/error)', () => {
  afterEach(() => {
    cleanup();
  });

  it('debería mostrar aviso de cuenta pendiente con status=pending', () => {
    render(AuthAlert, { props: { status: 'pending', error: null } });

    expect(screen.getByText('Permisos Insuficientes')).toBeInTheDocument();
    expect(screen.getByText(/Tu cuenta no tiene los permisos adecuados/)).toBeInTheDocument();
  });

  it('debería mostrar el mismo aviso con error=insufficient_permissions', () => {
    render(AuthAlert, { props: { status: null, error: 'insufficient_permissions' } });

    expect(screen.getByText('Permisos Insuficientes')).toBeInTheDocument();
  });

  it('debería mostrar error de Google con error=auth_failed', () => {
    render(AuthAlert, { props: { status: null, error: 'auth_failed' } });

    expect(screen.getByText('Error de Acceso')).toBeInTheDocument();
    expect(screen.getByText(/Hubo un problema al autenticar con Google/)).toBeInTheDocument();
  });

  it('no debería renderizar alerta para códigos sin mensaje propio', () => {
    const { container } = render(AuthAlert, { props: { status: null, error: 'expired_token' } });

    expect(container.querySelector('[role], .mb-6')).toBeNull();
    expect(screen.queryByText('Permisos Insuficientes')).not.toBeInTheDocument();
  });

  it('debería poder descartar la alerta con el botón cerrar', async () => {
    render(AuthAlert, { props: { status: 'pending', error: null } });
    expect(screen.getByText('Permisos Insuficientes')).toBeInTheDocument();

    await fireEvent.click(screen.getByLabelText('Cerrar alerta'));

    await waitFor(() => {
      expect(screen.queryByText('Permisos Insuficientes')).not.toBeInTheDocument();
    });
  });
});
