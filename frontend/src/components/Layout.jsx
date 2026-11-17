import { useState } from 'react';
import { API_URL, BACKEND_ORIGIN, S3_STATIC_URL } from '../api.js';

const NAV_ITEMS = [
  { section: 'Gestión Clínica', items: [
    { id: 'resumen', label: 'Dashboard Clínico', icon: '📊' },
    { id: 'pacientes', label: 'Tutores y Pacientes', icon: '🐾' },
    { id: 'agenda', label: 'Agenda Médica', icon: '📅' },
    { id: 'fichas', label: 'Fichas Clínicas', icon: '🩺' },
    { id: 'recordatorios', label: 'Vacunas y Controles', icon: '🔔' },
  ]},
  { section: 'Farmacia y Cobros', items: [
    { id: 'farmacia', label: 'Farmacia FEFO', icon: '💊' },
    { id: 'cobros', label: 'Servicios y Cobros', icon: '💳' },
  ]},
];

export default function Layout({ modulo, setModulo, user, health, onLogout, onRefresh, children }) {
  const [menuAbierto, setMenuAbierto] = useState(false);

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#0b1120] text-slate-400">
      <div className="px-5 py-5 border-b border-white/10 flex items-center gap-3">
        {S3_STATIC_URL ? (
          <img
            src={`${S3_STATIC_URL}/logo-petcare.png`}
            alt="PetCare"
            className="w-10 h-10 rounded-xl object-cover shadow-lg shadow-emerald-500/20"
          />
        ) : (
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-slate-950 flex items-center justify-center font-extrabold text-lg shadow-lg shadow-emerald-500/30">
            🐾
          </div>
        )}
        <div>
          <div className="text-white font-bold text-base tracking-tight">PetCare Cloud</div>
          <div className="text-[11px] text-slate-400">Suite Modular AWS</div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-3">
        {NAV_ITEMS.map((group) => (
          <div key={group.section} className="mb-3">
            <div className="px-5 pt-3 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              {group.section}
            </div>
            <nav className="px-3 space-y-1">
              {group.items.map((item) => {
                const active = modulo === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setModulo(item.id);
                      setMenuAbierto(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition ${
                      active
                        ? 'bg-emerald-500/15 text-emerald-300 border-l-4 border-emerald-400 font-semibold'
                        : 'text-slate-300/80 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <span className="text-base">{item.icon}</span>
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        ))}

        <div className="px-3 mt-4">
          <div className="px-2 pt-2 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            Accesos Directos
          </div>
          <a
            href={`${BACKEND_ORIGIN}/admin/`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between px-3.5 py-2 rounded-xl text-xs text-slate-300 hover:bg-white/5 hover:text-white transition"
          >
            <span>⚙️ Django Admin</span>
            <span className="text-slate-500">↗</span>
          </a>
          <a
            href={`${API_URL}/`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between px-3.5 py-2 rounded-xl text-xs text-slate-300 hover:bg-white/5 hover:text-white transition"
          >
            <span>🔌 API REST (DRF)</span>
            <span className="text-slate-500">↗</span>
          </a>
        </div>
      </div>

      <div className="p-4 border-t border-white/10 bg-slate-900/60">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="min-w-0">
            <div className="text-xs font-semibold text-white truncate">{user?.first_name || user?.username}</div>
            <div className="text-[11px] text-emerald-400">
              {user?.is_superuser ? 'Administrador Root' : 'Equipo Clínico'}
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-300">
            {health?.modules?.length || 6} módulos
          </span>
        </div>
        <button
          onClick={onLogout}
          className="w-full py-2 px-3 rounded-xl bg-white/5 hover:bg-rose-500/20 hover:text-rose-200 text-slate-200 text-xs font-semibold border border-white/10 transition"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="hidden lg:block w-64 shrink-0 sticky top-0 h-screen">
        {sidebarContent}
      </aside>

      {menuAbierto && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="w-64 h-full shadow-2xl">{sidebarContent}</div>
          <div className="flex-1 bg-slate-950/60" onClick={() => setMenuAbierto(false)} />
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur border-b border-slate-200 px-4 sm:px-7 py-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMenuAbierto(true)}
              className="lg:hidden p-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-100"
              aria-label="Abrir menú"
            >
              ☰
            </button>
            <div>
              <h1 className="text-sm sm:text-base font-bold text-slate-900">
                Centro de Control Clínico y Trazabilidad FEFO
              </h1>
              <p className="text-[11px] text-slate-500 hidden sm:block">
                Frontend desacoplado conectado a {API_URL}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <span
              className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-full ${
                health?.status === 'ok'
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-rose-50 text-rose-700 border border-rose-200'
              }`}
            >
              <span className={`w-2 h-2 rounded-full ${health?.status === 'ok' ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              {health?.status === 'ok' ? 'RDS + Backend Activos' : 'Backend sin conexión'}
            </span>
            <button
              onClick={onRefresh}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 text-slate-700"
            >
              ↻ Actualizar
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-7 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
