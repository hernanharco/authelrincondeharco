/**
 * Tests para componente LoginForm
 * Validación de formulario, envío y manejo de errores
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import LoginForm from '../../src/components/auth/LoginForm.svelte';

// Mock del servicio de autenticación
const mockAuthService = {
  login: vi.fn(),
};

describe('LoginForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Mockear el servicio de autenticación
    vi.doMock('../../src/services/authService.ts', () => mockAuthService);
  });

  it('debería renderizar el formulario de login', () => {
    render(LoginForm);

    expect(screen.getByLabelText('Username')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Iniciar Sesión' })).toBeInTheDocument();
  });

  it('debería mostrar errores de validación con campos vacíos', async () => {
    render(LoginForm);
    
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('El username es requerido')).toBeInTheDocument();
      expect(screen.getByText('La contraseña es requerida')).toBeInTheDocument();
    });
  });

  it('debería mostrar error de validación con username corto', async () => {
    render(LoginForm);
    
    const usernameInput = screen.getByLabelText('Username');
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    
    fireEvent.input(usernameInput, { target: { value: 'ab' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('El username debe tener al menos 3 caracteres')).toBeInTheDocument();
    });
  });

  it('debería mostrar error de validación con contraseña corta', async () => {
    render(LoginForm);
    
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    
    fireEvent.input(passwordInput, { target: { value: '123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('La contraseña debe tener al menos 6 caracteres')).toBeInTheDocument();
    });
  });

  it('debería llamar al servicio de autenticación con datos válidos', async () => {
    mockAuthService.login.mockResolvedValue({
      access_token: 'mock_token',
      user: { id: 1, username: 'testuser' }
    });

    render(LoginForm);
    
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    
    fireEvent.input(usernameInput, { target: { value: 'testuser' } });
    fireEvent.input(passwordInput, { target: { value: 'testpass123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockAuthService.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'testpass123'
      });
    });
  });

  it('debería mostrar loading durante el envío', async () => {
    mockAuthService.login.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
    
    render(LoginForm);
    
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    fireEvent.click(submitButton);

    // Verificar estado de loading
    expect(submitButton).toBeDisabled();
    expect(screen.getByText('Iniciando sesión...')).toBeInTheDocument();
  });

  it('debería manejar error de autenticación', async () => {
    mockAuthService.login.mockRejectedValue(new Error('Credenciales inválidas'));

    render(LoginForm);
    
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    
    fireEvent.input(usernameInput, { target: { value: 'testuser' } });
    fireEvent.input(passwordInput, { target: { value: 'wrongpass' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText('Credenciales inválidas')).toBeInTheDocument();
      expect(submitButton).not.toBeDisabled();
    });
  });

  it('debería redirigir al dashboard en login exitoso', async () => {
    const mockRedirect = vi.fn();
    vi.stubGlobal('window', {
      location: { href: '' },
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    
    mockAuthService.login.mockResolvedValue({
      access_token: 'mock_token',
      user: { id: 1, username: 'testuser' }
    });

    render(LoginForm);
    
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    fireEvent.click(submitButton);

    await waitFor(() => {
      // Verificar que se llama a redirección
      expect(mockRedirect).toHaveBeenCalled();
    });
  });

  it('debería alternar visibilidad de contraseña', () => {
    render(LoginForm);
    
    const passwordInput = screen.getByLabelText('Password');
    const toggleButton = screen.getByRole('button', { name: 'Mostrar contraseña' });
    
    // Estado inicial: contraseña oculta
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Click para mostrar contraseña
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(toggleButton).toHaveAttribute('aria-label', 'Ocultar contraseña');
    
    // Click para ocultar contraseña
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(toggleButton).toHaveAttribute('aria-label', 'Mostrar contraseña');
  });

  it('debería tener accesibilidad correcta', () => {
    render(LoginForm);
    
    // Verificar labels y ARIA
    const usernameInput = screen.getByLabelText('Username');
    const passwordInput = screen.getByLabelText('Password');
    const submitButton = screen.getByRole('button', { name: 'Iniciar Sesión' });
    
    expect(usernameInput).toHaveAttribute('id');
    expect(passwordInput).toHaveAttribute('id');
    expect(submitButton).toHaveAttribute('type', 'submit');
    expect(submitButton).toBeEnabled();
  });
});
