/**
 * Tests para componente GoogleButton
 * Flujo OAuth con popup y manejo de errores
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import GoogleButton from '../../src/components/auth/GoogleButton.svelte';

describe('GoogleButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Limpiar mocks del DOM
    document.body.innerHTML = '';
  });

  it('debería renderizar el botón de Google', () => {
    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('type', 'button');
    expect(button).toHaveClass('google-login-button');
  });

  it('debería abrir popup de Google al hacer click', async () => {
    const mockOpen = vi.fn();
    const mockWindow = {
      open: mockOpen,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    vi.stubGlobal('window', mockWindow);

    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOpen).toHaveBeenCalledWith(
        expect.stringContaining('accounts.google.com'),
        'google_oauth',
        'width=500,height=600'
      );
    });
  });

  it('debería manejar popup bloqueado', async () => {
    const mockOpen = vi.fn(() => null);
    const mockWindow = {
      open: mockOpen,
      alert: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    vi.stubGlobal('window', mockWindow);

    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockWindow.alert).toHaveBeenCalledWith(
        'Por favor permite las ventanas emergentes para iniciar sesión con Google'
      );
    });
  });

  it('debería mostrar loading durante el proceso', () => {
    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    
    // Estado inicial
    expect(button).not.toBeDisabled();
    expect(button).not.toHaveClass('loading');

    // Simular inicio de proceso OAuth
    fireEvent.click(button);
    
    // Durante el proceso debería mostrar loading
    expect(button).toBeDisabled();
    expect(button).toHaveClass('loading');
  });

  it('debería manejar mensaje de éxito del popup', async () => {
    const mockSetItem = vi.fn();
    const mockWindow = {
      open: vi.fn(() => ({
        closed: false,
        postMessage: vi.fn(),
      })),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      localStorage: {
        setItem: mockSetItem,
      },
      location: { href: '' },
    };
    vi.stubGlobal('window', mockWindow);

    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    fireEvent.click(button);

    // Simular mensaje de éxito del popup
    const messageEvent = new MessageEvent('message', {
      data: {
        type: 'AUTH_SUCCESS',
        payload: {
          token: 'mock_google_token',
          user: {
            id: '123',
            email: 'user@gmail.com',
            username: 'googleuser',
            full_name: 'Google User'
          }
        }
      }
    });

    // Disparar evento message
    window.dispatchEvent(messageEvent);

    await waitFor(() => {
      expect(mockSetItem).toHaveBeenCalledWith('session', 'mock_google_token');
      expect(mockWindow.location.href).toContain('/dashboard');
    });
  });

  it('debería manejar mensaje de error del popup', async () => {
    const mockAlert = vi.fn();
    const mockWindow = {
      open: vi.fn(() => ({
        closed: false,
        postMessage: vi.fn(),
      })),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      alert: mockAlert,
    };
    vi.stubGlobal('window', mockWindow);

    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    fireEvent.click(button);

    // Simular mensaje de error del popup
    const messageEvent = new MessageEvent('message', {
      data: {
        type: 'AUTH_ERROR',
        error: 'Usuario no encontrado'
      }
    });

    window.dispatchEvent(messageEvent);

    await waitFor(() => {
      expect(mockAlert).toHaveBeenCalledWith('Error en la autenticación: Usuario no encontrado');
    });
  });

  it('debería manejar estado PENDING_APPROVAL', async () => {
    const mockWindow = {
      open: vi.fn(() => ({
        closed: false,
        postMessage: vi.fn(),
      })),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      location: { href: '' },
    };
    vi.stubGlobal('window', mockWindow);

    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    fireEvent.click(button);

    // Simular mensaje de pending approval
    const messageEvent = new MessageEvent('message', {
      data: {
        type: 'PENDING_APPROVAL',
        payload: {
          message: 'Tu cuenta está pendiente de aprobación'
        }
      }
    });

    window.dispatchEvent(messageEvent);

    await waitFor(() => {
      expect(mockWindow.location.href).toContain('/login?status=pending');
    });
  });

  it('debería limpiar event listeners al desmontar', () => {
    const mockWindow = {
      open: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    vi.stubGlobal('window', mockWindow);

    const { unmount } = render(GoogleButton);

    // Desmontar componente
    unmount();

    // Verificar que se limpian los event listeners
    expect(mockWindow.removeEventListener).toHaveBeenCalledWith('message', expect.any(Function));
  });

  it('debería tener accesibilidad correcta', () => {
    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Iniciar con Google' });
    
    // Verificar atributos de accesibilidad
    expect(button).toHaveAttribute('type', 'button');
    expect(button).toHaveAttribute('aria-label', 'Iniciar sesión con Google');
    expect(button).toBeEnabled();
  });

  it('debería mostrar ícono de Google', () => {
    render(GoogleButton);

    // Verificar que contiene el ícono de Google
    const icon = screen.getByRole('img', { name: 'Google' });
    expect(icon).toBeInTheDocument();
    expect(icon).toHaveAttribute('alt', 'Google');
  });
});
