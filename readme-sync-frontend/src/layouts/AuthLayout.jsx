import { Outlet } from 'react-router-dom'
import { BookText } from 'lucide-react'

/**
 * Layout des pages d'authentification : panneau de marque (navy/étoilé,
 * clin d'œil à la palette Ilyaa Digital) à gauche, formulaire à droite.
 */
export default function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-navy-900 lg:flex lg:flex-col lg:justify-between lg:p-12">
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            backgroundImage:
              'radial-gradient(1px 1px at 20% 30%, white, transparent), radial-gradient(1px 1px at 70% 20%, white, transparent), radial-gradient(1.5px 1.5px at 40% 70%, white, transparent), radial-gradient(1px 1px at 85% 60%, white, transparent), radial-gradient(1px 1px at 55% 85%, white, transparent), radial-gradient(1.5px 1.5px at 10% 65%, white, transparent), radial-gradient(1px 1px at 90% 90%, white, transparent)',
          }}
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(ellipse at 30% 100%, rgba(124,128,183,0.35), transparent 60%)',
          }}
        />
        <div className="relative flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-700">
            <BookText size={18} className="text-white" strokeWidth={2.25} />
          </div>
          <span className="font-display text-lg font-semibold text-white">
            README<span className="text-indigo-300"> Sync</span>
          </span>
        </div>

        <div className="relative max-w-md space-y-4">
          <h2 className="font-display text-3xl font-semibold leading-tight text-white">
            Votre documentation se met à jour pendant que vous codez.
          </h2>
          <p className="text-sm leading-relaxed text-slate-300">
            Chaque commit est analysé, chaque section réécrite avec précision,
            chaque changement tracé — sans jamais réinventer votre README.
          </p>
        </div>

        <p className="relative font-mono text-xs text-indigo-300/70">
          sync engine · propulsé par une génération section par section
        </p>
      </div>

      <div className="flex items-center justify-center bg-bg px-6 py-12">
        <div className="w-full max-w-sm">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
