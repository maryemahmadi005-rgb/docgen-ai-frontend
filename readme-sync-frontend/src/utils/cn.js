import { clsx } from 'clsx'

/**
 * Petit helper pour composer des classes Tailwind conditionnelles.
 * Utilisation : cn('base', condition && 'variant', className)
 */
export function cn(...inputs) {
  return clsx(inputs)
}
