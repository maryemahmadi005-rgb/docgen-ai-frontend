import { cn } from '../../utils/cn'

const TONES = {
  neutral: 'bg-slate-100 text-ink-muted',
  blue: 'bg-blue-700/10 text-blue-700',
  indigo: 'bg-indigo-400/15 text-indigo-400',
  amber: 'bg-amber-100 text-amber-500',
  coral: 'bg-coral-100 text-coral-500',
}

export default function Badge({ tone = 'neutral', className, children }) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium font-mono tracking-tight',
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}
