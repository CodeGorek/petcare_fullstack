import { Search } from 'lucide-react';

export function BrandMark({ size = 'md' }) {
  const dims = size === 'lg' ? 'w-11 h-11 rounded-2xl' : 'w-9 h-9 rounded-xl';
  return (
    <div
      className={`${dims} bg-gradient-to-br from-emerald-400 via-emerald-500 to-teal-600 text-slate-950 flex items-center justify-center shadow-lg shadow-emerald-500/25 shrink-0`}
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
        <path d="M12 21c-4.5-2.2-8-6-8-10.5V5.5L12 3l8 2.5v5c0 4.5-3.5 8.3-8 10.5z" />
        <path d="M9 12h6" />
        <path d="M12 9v6" />
      </svg>
    </div>
  );
}

export function KpiCard({ title, value, subtitle, icon: Icon, badge, tone = 'emerald', highlightRed = false }) {
  const iconStyles = {
    info: 'bg-sky-50 text-sky-600 ring-1 ring-sky-200/70',
    purple: 'bg-violet-50 text-violet-600 ring-1 ring-violet-200/70',
    emerald: 'bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200/70',
    danger: 'bg-rose-50 text-rose-600 ring-1 ring-rose-200/70',
  }[tone] || 'bg-emerald-50 text-emerald-600 ring-1 ring-emerald-200/70';

  return (
    <div
      className={`bg-white rounded-2xl p-5 border border-slate-200/90 shadow-sm hover:shadow-md transition-shadow flex items-start justify-between gap-4 ${
        highlightRed ? 'border-l-4 border-l-rose-500' : ''
      }`}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <p className={`text-xs font-semibold truncate ${highlightRed ? 'text-rose-600' : 'text-slate-500'}`}>
            {title}
          </p>
          {badge && (
            <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
              {badge}
            </span>
          )}
        </div>
        <p className={`text-3xl font-extrabold tracking-tight ${highlightRed ? 'text-rose-600' : 'text-slate-900'}`}>
          {value}
        </p>
        {subtitle && (
          <p className={`text-[11px] mt-1.5 font-medium truncate ${highlightRed ? 'text-rose-500' : 'text-slate-500'}`}>
            {subtitle}
          </p>
        )}
      </div>
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center shrink-0 ${iconStyles}`}>
        {Icon && <Icon className="w-5 h-5" />}
      </div>
    </div>
  );
}

export function Panel({ title, subtitle, icon: Icon, action, children }) {
  return (
    <section className="bg-white rounded-2xl border border-slate-200/90 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-3 bg-slate-50/40">
        <div className="flex items-center gap-2.5 min-w-0">
          {Icon && (
            <div className="w-8 h-8 rounded-lg bg-white border border-slate-200/80 text-slate-700 flex items-center justify-center shrink-0 shadow-2xs">
              <Icon className="w-4 h-4" />
            </div>
          )}
          <div className="min-w-0">
            <h2 className="text-sm sm:text-base font-bold text-slate-900 truncate">{title}</h2>
            {subtitle && <p className="text-xs text-slate-500 truncate">{subtitle}</p>}
          </div>
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      <div>{children}</div>
    </section>
  );
}

export function SearchBar({ value, onChange, placeholder = 'Buscar...' }) {
  return (
    <div className="relative w-full sm:w-64">
      <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-3 py-1.5 text-xs sm:text-sm rounded-xl border border-slate-200 bg-white text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/25 focus:border-emerald-500"
      />
    </div>
  );
}

export function EstadoBadge({ estado }) {
  const styles = {
    ASISTIO: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    FEFO_NORMAL: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    ACTIVO: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    PAGADA: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    PROGRAMADA: 'bg-sky-50 text-sky-700 border-sky-200',
    PENDIENTE: 'bg-sky-50 text-sky-700 border-sky-200',
    PROXIMO: 'bg-amber-50 text-amber-800 border-amber-200',
    PRIORIDAD_FEFO_ALTA: 'bg-amber-50 text-amber-800 border-amber-200',
    NO_ASISTIO: 'bg-rose-50 text-rose-700 border-rose-200',
    BLOQUEADO_VENCIDO: 'bg-rose-50 text-rose-700 border-rose-200',
    INACTIVO: 'bg-rose-50 text-rose-700 border-rose-200',
    CANCELADA: 'bg-slate-100 text-slate-600 border-slate-200',
  };
  const dotColor = {
    ASISTIO: 'bg-emerald-500',
    FEFO_NORMAL: 'bg-emerald-500',
    ACTIVO: 'bg-emerald-500',
    PAGADA: 'bg-emerald-500',
    PROGRAMADA: 'bg-sky-500',
    PENDIENTE: 'bg-sky-500',
    PROXIMO: 'bg-amber-500',
    PRIORIDAD_FEFO_ALTA: 'bg-amber-500',
    NO_ASISTIO: 'bg-rose-500',
    BLOQUEADO_VENCIDO: 'bg-rose-500',
    INACTIVO: 'bg-rose-500',
    CANCELADA: 'bg-slate-400',
  };
  const labels = {
    PRIORIDAD_FEFO_ALTA: '1° Salir · ≤30d',
    BLOQUEADO_VENCIDO: 'Vencido',
    FEFO_NORMAL: 'Vigente FEFO',
    NO_ASISTIO: 'No Asistió',
    ASISTIO: 'Asistió',
  };
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border whitespace-nowrap ${styles[estado] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${dotColor[estado] || 'bg-slate-400'}`} />
      {labels[estado] || estado}
    </span>
  );
}

export const inputCls =
  'w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/25 focus:border-emerald-500 transition';
export const btnEmerald =
  'inline-flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow-sm shadow-emerald-600/20 transition disabled:opacity-60 cursor-pointer';
