'use client';

import { useState } from 'react';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import { useAuth } from '@/hooks/useAuth';
import type { LoginRequest } from '@/types/auth';

interface LoginFormProps {
  onSuccess?: () => void;
}

const LoginForm = ({ onSuccess }: LoginFormProps) => {
  const auth = useAuth();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState<LoginRequest>({
    username: '',
    password: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (auth.error || auth.success) auth.clearMessages();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await auth.login(formData);
    if (result && onSuccess) {
      onSuccess();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Input
        id="username"
        name="username"
        type="text"
        label="Usuario / Email"
        value={formData.username}
        onChange={handleInputChange}
        placeholder="Introduce tu usuario"
        autoComplete="username"
        required
        icon={<Mail className="h-5 w-5" />}
      />

      <Input
        id="password"
        name="password"
        type={showPassword ? 'text' : 'password'}
        label="Contraseña"
        value={formData.password}
        onChange={handleInputChange}
        placeholder="•••••••"
        autoComplete="current-password"
        required
        icon={<Lock className="h-5 w-5" />}
        trailingIcon={
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="text-gray-400 hover:text-gray-600"
          >
            {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
          </button>
        }
      />

      <Button
        type="submit"
        isLoading={auth.isLoading}
        className="w-full"
        disabled={auth.isLoading}
      >
        {auth.isLoading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
      </Button>
    </form>
  );
};

export default LoginForm;
