import { cn } from '../../utils/cn'

/**
 * Élément signature du produit : une pastille façon "ligne de diff git"
 * (+ ajouts / - retraits), utilisée partout où l'on résume l'ampleur d'un
 * changement (Dashboard, Scans, Pending Updates) — pour rappeler que le
 * produit raisonne toujours en changements ciblés, jamais en régénération
 * complète.
 */
export default function DiffPill({ added = 0, removed = 0, className }) {
  if (added === 0 && removed === 0) {
    return (
      <span className={cn('font-mono text-xs text-ink-muted', className)}>
        aucun changement
      </span>
    )
  }
  return (
    <span className={cn('inline-flex items-center gap-2 font-mono text-xs', className)}>
      {added > 0 && (
        <span className="inline-flex items-center rounded bg-blue-700/10 text-blue-700 px-1.5 py-0.5">
          +{added}
        </span>
      )}
      {removed > 0 && (
        <span className="inline-flex items-center rounded bg-coral-100 text-coral-500 px-1.5 py-0.5">
          −{removed}
        </span>
      )}
    </span>
  )
}
