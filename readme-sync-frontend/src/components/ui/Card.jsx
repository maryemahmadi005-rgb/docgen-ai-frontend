import { cn } from '../../utils/cn'

export default function Card({ className, children, ...props }) {
  return (
    <div
      className={cn(
        'bg-surface border border-slate-200 rounded-[var(--radius-card)] shadow-[var(--shadow-soft)]',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}

export function CardHeader({ className, children, ...props }) {
  return (
    <div className={cn('px-5 py-4 border-b border-slate-200', className)} {...props}>
      {children}
    </div>
  )
}

export function CardBody({ className, children, ...props }) {
  return (
    <div className={cn('p-5', className)} {...props}>
      {children}
    </div>
  )
}
