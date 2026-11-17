import { useState } from 'react';
import {
  BellRing,
  CalendarClock,
  Code2,
  CreditCard,
  Database,
  ExternalLink,
  LayoutDashboard,
  LogOut,
  Menu,
  PawPrint,
  Pill,
  RefreshCw,
  ShieldCheck,
  Stethoscope,
  X,
} from 'lucide-react';
import { API_URL, BACKEND_ORIGIN, S3_STATIC_URL } from '../api.js';
import { BrandMark } from './UiParts.jsx';

const NAV_ITEMS = [
  {
    section: 'Gestión Clínica',
    items: [
      { id: 'resumen', label: 'Dashboard Clínico', icon: LayoutDashboard },
      { id: 'pacientes', label: 'Tutores y Pacientes', icon: PawPrint },
      { id: 'agenda', label: 'Agenda Médica', icon: CalendarClock },
      { id: 'fichas', label: 'Fichas Clínicas', icon: Stethoscope },
      { id: 'recordatorios', label: 'Vacunas y Controles', icon: BellRing },
    ],
  },
  {
    section: 'Farmacia y Cobros',
    items: [
      { id: 'farmacia', label: 'Farmacia FEFO', icon: Pill },
      { id: 'cobros', label: 'Servicios y Cobros', icon: CreditCard },
    ],
  },
];

export default function Layout({ modulo, setModulo, user, health, refreshing, onLogout, onRefresh, children }) {
  const [menuAbierto, setMenuAbierto] = useState(false);
  const [logoFallback, setLogoFallback] = useState(false);

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#0b1120] text-slate-400 border-r border-white/5">
      <div className="px-5 py-5 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          {S3_STATIC_URL && !logoFallback ? (
            <img
              src={`${S3_STATIC_URL}/logo-petcare.png`}
              alt="PetCare"
              onError={() => setLogoFallback(true)}
              className="w-9 h-9 rounded-xl object-cover shadow-lg shadow-emerald-500/20"
            />
          ) : (
            <BrandMark />
          )}
          <div className="min-w-0">
            <div className="text-white font-bold text-sm tracking-tight truncate">PetCare Cloud</div>
            <div className="text-[11px] text-emerald-400/90 font-medium truncate">Clinical Suite AWS</div>
          </div>
        </div>
        <button
          onClick={() => setMenuAbierto(false)}
          className="lg:hidden p-1 rounded-lg text-slate-400 hover:text-white"
          aria-label="Cerrar menú"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-4">
        {NAV_ITEMS.map((group) => (
          <div key={group.section} className="mb-4">
            <div className="px-5 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
              {group.section}
            </div>
            <nav className="px-3 space-y-1">
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = modulo === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setModulo(item.id);
                      setMenuAbierto(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13px] font-medium transition cursor-pointer ${
                      active
                        ? 'bg-emerald-500/15 text-emerald-300 border-l-2 border-emerald-400 font-semibold shadow-sm'
                        : 'text-slate-300/80 hover:bg-white/5 hover:text-white'
                    }`}
                  >
                    <Icon className={`w-4 h-4 shrink-0 ${active ? 'text-emerald-400' : 'text-slate-400'}`} />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>
        ))}

        <div className="px-3 mt-4 pt-3 border-t border-white/5">
          <div className="px-2 pb-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            Infraestructura & Admin
          </div>
          <a
            href={`${BACKEND_ORIGIN}/admin/`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between px-3.5 py-2 rounded-xl text-xs text-slate-300 hover:bg-white/5 hover:text-white transition"
          >
            <span className="flex items-center gap-2.5">
              <ShieldCheck className="w-4 h-4 text-slate-400" />
              Django Admin
            </span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          </a>
          <a
            href={`${API_URL}/`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-between px-3.5 py-2 rounded-xl text-xs text-slate-300 hover:bg-white/5 hover:text-white transition"
          >
            <span className="flex items-center gap-2.5">
              <Code2 className="w-4 h-4 text-slate-400" />
              API REST (DRF)
            </span>
            <ExternalLink className="w-3.5 h-3.5 text-slate-500" />
          </a>
        </div>
      </div>

      <div className="p-4 border-t border-white/10 bg-slate-950/50">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center justify-center text-xs font-bold uppercase shrink-0">
              {(user?.username || 'A').slice(0, 2)}
            </div>
            <div className="min-w-0">
              <div className="text-xs font-semibold text-white truncate">{user?.first_name || user?.username}</div>
              <div className="text-[11px] text-emerald-400">
                {user?.is_superuser ? 'Administrador Root' : 'Equipo Clínico'}
              </div>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-white/5 text-slate-300 border border-white/10">
            {health?.modules?.length || 6} apps
          </span>
        </div>
        <button
          onClick={onLogout}
          className="w-full py-2 px-3 rounded-xl bg-white/5 hover:bg-rose-500/20 hover:text-rose-200 text-slate-200 text-xs font-semibold border border-white/10 transition flex items-center justify-center gap-2 cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5" />
          Cerrar sesión
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen flex bg-slate-100">
      <aside className="hidden lg:block w-64 shrink-0 sticky top-0 h-screen">{sidebarContent}</aside>

      {menuAbierto && (
        <div className="fixed inset-0 z-50 lg:hidden flex">
          <div className="w-64 h-full shadow-2xl">{sidebarContent}</div>
          <div className="flex-1 bg-slate-950/60 backdrop-blur-xs" onClick={() => setMenuAbierto(false)} />
        </div>
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-4 sm:px-7 py-3.5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3 min-w-0">
            <button
              onClick={() => setMenuAbierto(true)}
              className="lg:hidden p-2 rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-100"
              aria-label="Abrir menú"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="min-w-0">
              <h1 className="text-sm sm:text-base font-bold text-slate-900 truncate">
                Centro de Control Clínico y Trazabilidad FEFO
              </h1>
              <p className="text-[11px] text-slate-500 hidden sm:block truncate">
                Arquitectura modular AWS · API: <span className="font-mono">{API_URL}</span>
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
              <Database className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{health?.status === 'ok' ? 'RDS + Backend Activos' : 'Sin conexión'}</span>
            </span>
            <button
              onClick={onRefresh}
              disabled={refreshing}
              className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 transition cursor-pointer disabled:opacity-60"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
              <span>Actualizar</span>
            </button>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-7 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
