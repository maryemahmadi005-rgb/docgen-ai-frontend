/**
 * Affiche un contenu de section README (before/after) en style "diff" —
 * réutilisé sur ScanDetails et PendingUpdates.
 */
export default function SectionCode({ before, after }) {
  const changed = before !== after
  return (
    <div className="rounded-lg border border-slate-200 overflow-hidden font-mono text-xs">
      <div
        className={
          changed
            ? 'bg-coral-100/60 px-3.5 py-2.5 whitespace-pre-wrap text-ink-muted line-through decoration-coral-500/40'
            : 'bg-slate-100 px-3.5 py-2.5 whitespace-pre-wrap text-ink-muted'
        }
      >
        {before}
      </div>
      {changed && (
        <div className="bg-blue-700/[0.06] px-3.5 py-2.5 whitespace-pre-wrap text-navy-800 border-t border-slate-200">
          {after}
        </div>
      )}
    </div>
  )
}
