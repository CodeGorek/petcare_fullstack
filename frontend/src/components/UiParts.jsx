export function KpiCard({ title, value, subtitle, icon, tone = 'emerald', highlightRed = false }) {
  const iconBg = {
    info: 'bg-sky-50 text-sky-600',
    purple: 'bg-violet-50 text-violet-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    danger: 'bg-rose-50 text-rose-600',
  }[tone] || 'bg-emerald-50 text-emerald-600';

  return (
    <div
      className={`bg-white rounded-2xl p-5 border border-slate-200 shadow-sm flex items-center justify-between gap-3 ${
        highlightRed ? 'border-l-4 border-l-rose-500' : ''
      }`}
    >
      <div>
        <p className={`text-xs font-semibold mb-1 ${highlightRed ? 'text-rose-600' : 'text-slate-500'}`}>
          {title}
        </p>
        <p className={`text-3xl font-extrabold tracking-tight ${highlightRed ? 'text-rose-600' : 'text-slate-900'}`}>
          {value}
        </p>
        {subtitle && (
          <p className={`text-[11px] mt-1 font-medium ${highlightRed ? 'text-rose-500' : 'text-slate-500'}`}>
            {subtitle}
          </p>
        )}
      </div>
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl shrink-0 ${iconBg}`}>
        {icon}
      </div>
    </div>
  );
}

export function Panel({ title, subtitle, action, children }) {
  return (
    <section className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-sm sm:text-base font-bold text-slate-900">{title}</h2>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {action}
      </div>
      <div>{children}</div>
    </section>
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
  const labels = {
    PRIORIDAD_FEFO_ALTA: '1° en salir (FEFO ≤30d)',
    BLOQUEADO_VENCIDO: 'Vencido (Bloqueado)',
    FEFO_NORMAL: 'Vigente FEFO',
    NO_ASISTIO: 'No Asistió',
    ASISTIO: 'Asistió',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${styles[estado] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
      {labels[estado] || estado}
    </span>
  );
}

export const inputCls =
  'w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500';
export const btnEmerald =
  'px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow-sm transition disabled:opacity-60';
