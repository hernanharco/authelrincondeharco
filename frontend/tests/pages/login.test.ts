/**
 * Tests para página de login
 * Renderizado completo y flujo de autenticación
 */
import { render, screen, fireEvent, waitFor } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock de Astro para pages
const mockAstro = {
  redirect: vi.fn(),
};

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Limpiar localStorage
    localStorage.clear();
    // Mockear Astro
    vi.stubGlobal('Astro', mockAstro);
  });

  it('debería renderizar página de login completa', () => {
    // Simular renderizado de página Astro
    const { container } = render(() => '<div>Login Page Content</div>');
    
    expect(container.querySelector('h1')).toHaveTextContent('Iniciar Sesión');
    expect(container.querySelector('form')).toBeInTheDocument();
  });

  it('debería mostrar formulario de login tradicional', () => {
    const { container } = render(() => '<div>LoginForm Component</div>');
    
    // Verificar que existe el formulario
    expect(container.querySelector('[data-testid="login-form"]')).toBeInTheDocument();
    expect(container.querySelector('input[name="username"]')).toBeInTheDocument();
    expect(container.querySelector('input[name="password"]')).toBeInTheDocument();
  });

  it('debería mostrar botón de Google OAuth', () => {
    const { container } = render(() => '<div>GoogleButton Component</div>');
    
    // Verificar botón de Google
    expect(container.querySelector('[data-testid="google-login"]')).toBeInTheDocument();
  });

  it('debería redirigir si ya está autenticado', () => {
    // Simular usuario autenticado
    localStorage.setItem('session', 'mock_token');
    
    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar que se llama a redirección
    expect(mockAstro.redirect).toHaveBeenCalledWith('/dashboard');
  });

  it('debería manejar parámetro de estado pendiente', () => {
    // Mockear URL con parámetro
    vi.stubGlobal('URL', {
      searchParams: new URLSearchParams('status=pending')
    });

    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar que muestra mensaje de pendiente
    expect(container.querySelector('[data-testid="pending-message"]')).toBeInTheDocument();
    expect(container.querySelector('[data-testid="pending-message"]')).toHaveTextContent(
      'Tu cuenta está pendiente de aprobación'
    );
  });

  it('debería manejar parámetro de error', () => {
    // Mockear URL con parámetro de error
    vi.stubGlobal('URL', {
      searchParams: new URLSearchParams('error=session_expired')
    });

    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar que muestra mensaje de error
    expect(container.querySelector('[data-testid="error-message"]')).toBeInTheDocument();
    expect(container.querySelector('[data-testid="error-message"]')).toHaveTextContent(
      'Tu sesión ha expirado. Por favor inicia sesión nuevamente.'
    );
  });

  it('debería limpiar mensajes al cambiar de pestaña', async () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    // Simular mensaje de error
    expect(container.querySelector('[data-testid="error-message"]')).toBeInTheDocument();
    
    // Cambiar a otra pestaña y volver
    Object.defineProperty(document, 'hidden', {
      writable: true,
      value: true
    });
    Object.defineProperty(document, 'hidden', {
      writable: true,
      value: false
    });

    await waitFor(() => {
      // Verificar que se limpiaron los mensajes
      expect(container.querySelector('[data-testid="error-message"]')).not.toBeInTheDocument();
    });
  });

  it('debería tener metadatos SEO correctos', () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar título de página
    expect(document.title).toContain('Iniciar Sesión');
    
    // Verificar meta descripción
    const metaDescription = document.querySelector('meta[name="description"]');
    expect(metaDescription).toHaveAttribute('content', expect.stringContaining('AuthCore'));
  });

  it('debería ser accesible', () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar navegación principal
    const main = container.querySelector('main');
    expect(main).toHaveAttribute('role', 'main');
    
    // Verificar encabezado
    const heading = container.querySelector('h1');
    expect(heading).toHaveAttribute('tabindex', '-1');
  });

  it('debería tener enlaces de ayuda', () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar enlaces de ayuda
    const forgotPasswordLink = container.querySelector('a[href="/forgot-password"]');
    const supportLink = container.querySelector('a[href="/support"]');
    
    expect(forgotPasswordLink).toBeInTheDocument();
    expect(supportLink).toBeInTheDocument();
  });

  it('debería manejar envío de formulario exitoso', async () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    const form = container.querySelector('form');
    const usernameInput = container.querySelector('input[name="username"]');
    const passwordInput = container.querySelector('input[name="password"]');
    
    // Llenar formulario
    fireEvent.input(usernameInput, { target: { value: 'testuser' } });
    fireEvent.input(passwordInput, { target: { value: 'testpass123' } });
    
    // Enviar formulario
    fireEvent.submit(form);

    await waitFor(() => {
      // Verificar que se redirige al dashboard
      expect(mockAstro.redirect).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('debería manejar envío de formulario con error', async () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    const form = container.querySelector('form');
    const usernameInput = container.querySelector('input[name="username"]');
    const passwordInput = container.querySelector('input[name="password"]');
    
    // Llenar formulario con datos inválidos
    fireEvent.input(usernameInput, { target: { value: 'wronguser' } });
    fireEvent.input(passwordInput, { target: { value: 'wrongpass' } });
    
    // Enviar formulario
    fireEvent.submit(form);

    await waitFor(() => {
      // Verificar que muestra mensaje de error
      expect(container.querySelector('[data-testid="error-message"]')).toBeInTheDocument();
      expect(container.querySelector('[data-testid="error-message"]')).toHaveTextContent(
        'Credenciales inválidas'
      );
    });
  });

  it('debería ser responsive', () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    const main = container.querySelector('main');
    
    // Verificar clases responsive
    expect(main).toHaveClass('min-h-screen', 'flex', 'items-center', 'justify-center');
    
    // Verificar contenedor del formulario
    const formContainer = container.querySelector('[data-testid="form-container"]');
    expect(formContainer).toHaveClass('w-full', 'max-w-md', 'mx-auto');
  });

  it('debería tener tema de modo oscuro', () => {
    const { container } = render(() => '<div>Login Page</div>');
    
    // Verificar clases de tema oscuro
    const body = container.closest('body');
    expect(body).toHaveClass('bg-gray-900', 'text-gray-100');
  });
});
