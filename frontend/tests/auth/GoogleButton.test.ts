/**
 * Tests para componente GoogleButton
 *
 * Contrato real (src/components/auth/GoogleButton.svelte): el botón dispara el
 * flujo OAuth como NAVEGACIÓN COMPLETA de la ventana principal hacia
 * `BACKEND_URL + /api/v1/auth/google` con el parámetro `redirect_to`, usando
 * `window.top.location.replace`. No hay popup, postMessage ni sesión en
 * localStorage. Mientras la navegación no se completa muestra "Conectando..."
 * con el botón deshabilitado.
 *
 * Intentos descartados de la versión anterior (comportamiento inexistente):
 * popup window.open + postMessage AUTH_SUCCESS/AUTH_ERROR/PENDING_APPROVAL,
 * alert de popup bloqueado, listeners de mensaje, aria-label e img alt.
 */
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/svelte';
import { describe, it, expect, beforeEach, afterEach, afterAll, vi } from 'vitest';
import GoogleButton from '../../src/components/auth/GoogleButton.svelte';
import { BACKEND_URL } from '../../src/config/api.config';

const AUTH_ENDPOINT = `${BACKEND_URL}/api/v1/auth/google`;
const FAKE_ORIGIN = 'http://localhost:4321';

// En jsdom `window === globalThis === window.top`, así que el componente lee
// `window.top.location` desde globalThis. Se sustituye el Location real (que
// jsdom no deja redefinir) para capturar la navegación — mismo patrón que
// tests/pages/login.test.ts.
const originalLocation = Object.getOwnPropertyDescriptor(globalThis, 'location');
let replaceSpy: ReturnType<typeof vi.fn>;

function stubLocation(): void {
  replaceSpy = vi.fn();
  Object.defineProperty(globalThis, 'location', {
    value: { origin: FAKE_ORIGIN, replace: replaceSpy },
    writable: true,
    configurable: true,
    enumerable: true,
  });
}

function redirectOf(call: unknown[]): string | null {
  return new URL(String(call[0])).searchParams.get('redirect_to');
}

describe('GoogleButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    stubLocation();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  afterAll(() => {
    if (originalLocation) {
      Object.defineProperty(globalThis, 'location', originalLocation);
    }
  });

  it('debería renderizar el botón con su texto, tipo e icono sin navegar todavía', () => {
    render(GoogleButton);

    const button = screen.getByRole('button', { name: 'Continuar con Google' });
    expect(button).toHaveAttribute('type', 'button');
    expect(button).toBeEnabled();
    expect(button.querySelector('svg')).toBeInTheDocument();
    expect(replaceSpy).not.toHaveBeenCalled();
  });

  it('debería navegar al endpoint OAuth del backend con redirect_to por defecto', async () => {
    render(GoogleButton);

    await fireEvent.click(screen.getByRole('button', { name: 'Continuar con Google' }));

    expect(replaceSpy).toHaveBeenCalledTimes(1);
    const url = new URL(String(replaceSpy.mock.calls[0][0]));
    expect(`${url.origin}${url.pathname}`).toBe(AUTH_ENDPOINT);
    expect(redirectOf(replaceSpy.mock.calls[0])).toBe(`${FAKE_ORIGIN}/dashboard`);
  });

  it('debería construir redirect_to a partir de redirectParam (relativa y absoluta)', async () => {
    const first = render(GoogleButton, { props: { redirectParam: '/panel' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Continuar con Google' }));
    expect(redirectOf(replaceSpy.mock.calls[0])).toBe(`${FAKE_ORIGIN}/panel`);
    first.unmount();

    render(GoogleButton, { props: { redirectParam: 'https://otro-sitio.com/home' } });
    await fireEvent.click(screen.getByRole('button', { name: 'Continuar con Google' }));
    expect(redirectOf(replaceSpy.mock.calls[1])).toBe('https://otro-sitio.com/home');
  });

  it('debería mostrar "Conectando..." y deshabilitar el botón tras el click', async () => {
    render(GoogleButton);
    const button = screen.getByRole('button', { name: 'Continuar con Google' });

    await fireEvent.click(button);

    expect(await screen.findByText('Conectando...')).toBeInTheDocument();
    expect(button).toBeDisabled();
    expect(screen.queryByText('Continuar con Google')).not.toBeInTheDocument();
  });

  it('debería ignorar clicks adicionales mientras está en estado de carga', async () => {
    render(GoogleButton);
    const button = screen.getByRole('button', { name: 'Continuar con Google' });

    await fireEvent.click(button);
    await waitFor(() => expect(button).toBeDisabled());
    await fireEvent.click(button);

    expect(replaceSpy).toHaveBeenCalledTimes(1);
  });

  it('no debería usar popup, postMessage ni guardar sesión en localStorage', async () => {
    const openSpy = vi.spyOn(window, 'open');
    render(GoogleButton);

    await fireEvent.click(screen.getByRole('button', { name: 'Continuar con Google' }));

    expect(replaceSpy).toHaveBeenCalledTimes(1);
    expect(openSpy).not.toHaveBeenCalled();
    expect(localStorage.length).toBe(0);
  });
});
