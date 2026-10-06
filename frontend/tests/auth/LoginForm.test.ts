/**
 * Tests para componente LoginForm — rendering, validación e inputs.
 *
 * Contrato real (src/components/auth/LoginForm.svelte): labels "Nombre de
 * usuario"/"Contraseña", botón "Entrar al sistema", validación SOLO vía
 * atributo HTML `required` + botón deshabilitado hasta completar ambos campos,
 * sin mensajes de validación propios y sin toggle de visibilidad de
 * contraseña. El texto de carga es "Validando...".
 *
 * El cableado completo (payload de login, redirectParam, persistencia de
 * auth_user, limpieza de errores) vive en tests/pages/login.test.ts (T4a);
 * aquí se cubre el contrato del propio componente.
 *
 * Intentos descartados de la versión anterior (comportamiento inexistente):
 * mensajes "El username es requerido" / "al menos 3 caracteres" / "al menos 6
 * caracteres", toggle "Mostrar/Ocultar contraseña", loading "Iniciando
 * sesión...", labels "Username"/"Password" y botón "Iniciar Sesión".
 */
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, afterEach, afterAll, vi } from 'vitest';
import LoginForm from '../../src/components/auth/LoginForm.svelte';
import { authService } from '../../src/services/authService';

vi.mock('../../src/services/authService', () => ({
  authService: { login: vi.fn() },
}));

const mockLogin = vi.mocked(authService.login);

// jsdom no deja redefinir window.location (y `window === globalThis`); se
// sustituye en globalThis para que la navegación tras el login sea un no-op
// — mismo patrón que tests/pages/login.test.ts.
const originalLocation = Object.getOwnPropertyDescriptor(globalThis, 'location');

function stubLocation(): void {
  Object.defineProperty(globalThis, 'location', {
    value: { origin: 'http://localhost:4321', href: '' },
    writable: true,
    configurable: true,
    enumerable: true,
  });
}

function setUsername(value: string) {
  return fireEvent.input(screen.getByLabelText('Nombre de usuario'), {
    target: { value },
  });
}

function setPassword(value: string) {
  return fireEvent.input(screen.getByLabelText('Contraseña'), { target: { value } });
}

function submitButton() {
  return screen.getByRole('button', { name: 'Entrar al sistema' });
}

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    stubLocation();
  });

  afterEach(() => {
    cleanup();
  });

  afterAll(() => {
    if (originalLocation) {
      Object.defineProperty(globalThis, 'location', originalLocation);
    }
  });

  it('debería renderizar labels, placeholders y botón de envío', () => {
    render(LoginForm);

    expect(screen.getByLabelText('Nombre de usuario')).toBeInTheDocument();
    expect(screen.getByLabelText('Contraseña')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Tu usuario...')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('••••••••')).toBeInTheDocument();

    const button = submitButton();
    expect(button).toHaveAttribute('type', 'submit');
  });

  it('debería asociar cada input con su label, id, tipo y required', () => {
    render(LoginForm);

    const username = screen.getByLabelText('Nombre de usuario');
    const password = screen.getByLabelText('Contraseña');

    expect(username).toHaveAttribute('id', 'username');
    expect(username).toHaveAttribute('type', 'text');
    expect(username).toBeRequired();
    expect(password).toHaveAttribute('id', 'password');
    expect(password).toHaveAttribute('type', 'password');
    expect(password).toBeRequired();
  });

  it('debería mantener el botón deshabilitado con ambos campos vacíos', () => {
    render(LoginForm);

    expect(submitButton()).toBeDisabled();
  });

  it('debería mantener el botón deshabilitado solo con el usuario relleno', async () => {
    render(LoginForm);

    await setUsername('alice');

    expect(submitButton()).toBeDisabled();
  });

  it('debería mantener el botón deshabilitado solo con la contraseña rellena', async () => {
    render(LoginForm);

    await setPassword('secret');

    expect(submitButton()).toBeDisabled();
  });

  it('debería habilitar el botón al completar usuario y contraseña', async () => {
    render(LoginForm);

    await setUsername('alice');
    await setPassword('secret');

    expect(submitButton()).toBeEnabled();
  });

  it('debería enviar las credenciales a authService.login', async () => {
    mockLogin.mockResolvedValue({
      access_token: 'jwt',
      token_type: 'bearer',
      user: { id: '1', username: 'alice', email: 'alice@example.com' },
    });
    render(LoginForm);

    await setUsername('alice');
    await setPassword('hunter2');
    await fireEvent.click(submitButton());

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({ username: 'alice', password: 'hunter2' });
    });
  });

  it('debería confiar en required/required+disabled sin mensajes de validación propios', async () => {
    mockLogin.mockResolvedValue({
      access_token: 'jwt',
      token_type: 'bearer',
      user: { id: '1', username: 'ab', email: 'ab@example.com' },
    });
    render(LoginForm);

    // Valores "cortos": el componente no aplica reglas de longitud propias.
    await setUsername('ab');
    await setPassword('123');
    await fireEvent.click(submitButton());

    expect(await screen.findByText('¡Sesión iniciada con éxito!')).toBeInTheDocument();
    expect(screen.queryByText(/requerido|requerida|al menos/i)).not.toBeInTheDocument();
  });

  it('debería mostrar "Validando..." y deshabilitar los inputs durante el envío', async () => {
    mockLogin.mockReturnValue(new Promise(() => {})); // nunca resuelve
    render(LoginForm);

    await setUsername('alice');
    await setPassword('secret');
    await fireEvent.click(submitButton());

    expect(await screen.findByText('Validando...')).toBeInTheDocument();
    expect(screen.getByLabelText('Nombre de usuario')).toBeDisabled();
    expect(screen.getByLabelText('Contraseña')).toBeDisabled();
    expect(screen.getByRole('button', { name: /Validando/ })).toBeDisabled();
  });

  it('no debería incluir toggle de visibilidad de contraseña', async () => {
    render(LoginForm);

    const password = screen.getByLabelText('Contraseña');
    expect(password).toHaveAttribute('type', 'password');
    expect(
      screen.queryByRole('button', { name: /mostrar|ocultar|ver contraseña/i })
    ).not.toBeInTheDocument();

    await setPassword('secret');
    expect(password).toHaveAttribute('type', 'password');
  });
});
