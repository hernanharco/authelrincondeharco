'use client';

import { InputHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/utils/cn';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: ReactNode;
  trailingIcon?: ReactNode;
  helperText?: string;
}

const Input = ({
  className,
  label,
  error,
  icon,
  trailingIcon,
  helperText,
  id,
  ...props
}: InputProps) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="space-y-2">
      {label && (
        <label
          htmlFor={inputId}
          className="block text-sm font-medium text-gray-700"
        >
          {label}
        </label>
      )}

      <div className="relative">
        {icon && (
          <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5">
            {icon}
          </div>
        )}

        <input
          id={inputId}
          className={cn(
            'w-full border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition',
            icon && 'pl-10',
            trailingIcon && 'pr-10',
            error && 'border-red-300 focus:ring-red-500 focus:border-red-500',
            className
          )}
          {...props}
        />

        {trailingIcon && (
          <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5">
            {trailingIcon}
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 flex items-center">
          {error}
        </p>
      )}

      {helperText && !error && (
        <p className="text-sm text-gray-500">
          {helperText}
        </p>
      )}
    </div>
  );
};

export default Input;
