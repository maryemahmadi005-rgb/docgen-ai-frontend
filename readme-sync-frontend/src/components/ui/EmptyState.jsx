export default function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      {Icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-indigo-400">
          <Icon size={22} strokeWidth={1.75} />
        </div>
      )}
      <div className="space-y-1">
        <h3 className="text-base font-semibold text-navy-800">{title}</h3>
        {description && <p className="text-sm text-ink-muted max-w-sm">{description}</p>}
      </div>
      {action}
    </div>
  )
}
