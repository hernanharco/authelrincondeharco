import { describe, expect, it } from 'vitest';
import { displayMemberRole, memberRoleTooltip } from '@utils/auth.roles';

describe('displayMemberRole', () => {
  it('pinta SUPERADMIN cuando el rol GLOBAL es SUPERADMIN', () => {
    expect(displayMemberRole('ADMIN', 'SUPERADMIN')).toBe('SUPERADMIN');
  });

  it('ignora el rol global cuando no es SUPERADMIN', () => {
    expect(displayMemberRole('USER', 'ADMIN')).toBe('USER');
    expect(displayMemberRole('MANAGER', 'USER')).toBe('MANAGER');
  });

  it('normaliza el case del rol de membresía', () => {
    expect(displayMemberRole('admin', 'user')).toBe('ADMIN');
    expect(displayMemberRole(' admin ', null)).toBe('ADMIN');
  });

  it('si el rol global falta (backend sin desplegar) usa la membresía', () => {
    expect(displayMemberRole('MANAGER', undefined)).toBe('MANAGER');
    expect(displayMemberRole('VIEWER', '')).toBe('VIEWER');
    expect(displayMemberRole('ADMIN', null)).toBe('ADMIN');
  });

  it('un SUPERADMIN global con membresía USER sigue pintando SUPERADMIN', () => {
    expect(displayMemberRole('USER', 'SUPERADMIN')).toBe('SUPERADMIN');
  });
});

describe('memberRoleTooltip', () => {
  it('aclara ambos roles cuando el global difiere de la membresía', () => {
    // Label legible (no el código crudo): membresía ADMIN -> "Admin"
    expect(memberRoleTooltip('ADMIN', 'SUPERADMIN')).toBe(
      'Rol global: Superadmin · Rol en este tenant: Admin',
    );
  });

  it('no genera tooltip cuando coinciden (no aporta nada)', () => {
    expect(memberRoleTooltip('ADMIN', 'ADMIN')).toBeUndefined();
    expect(memberRoleTooltip('ADMIN', undefined)).toBeUndefined();
    expect(memberRoleTooltip('USER', 'USER')).toBeUndefined();
  });
});
