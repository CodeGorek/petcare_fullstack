import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CalendarCheck2,
  CalendarClock,
  FileText,
  PawPrint,
  PieChart,
  Pill,
  Users,
} from 'lucide-react';
import { EstadoBadge, KpiCard, Panel } from './UiParts.jsx';

const PALETTE = ['#10b981', '#0ea5e9', '#8b5cf6', '#f59e0b', '#f43f5e'];

function DonutChart({ items, emptyText }) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  if (!total) {
    return <p className="text-sm text-slate-400 py-8 text-center">{emptyText}</p>;
  }

  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6 p-5">
      <div className="relative w-36 h-36 shrink-0 flex items-center justify-center">
        <svg viewBox="0 0 140 140" className="w-full h-full -rotate-90">
          <circle cx="70" cy="70" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="18" />
          {items.map((item, idx) => {
            const pct = item.value / total;
            const dash = pct * circumference;
            const segOffset = offset;
            offset += dash;
            return (
              <circle
                key={item.label}
                cx="70"
                cy="70"
                r={radius}
                fill="none"
                stroke={PALETTE[idx % PALETTE.length]}
                strokeWidth="18"
                strokeDasharray={`${dash} ${circumference - dash}`}
                strokeDashoffset={-segOffset}
                strokeLinecap="butt"
              />
            );
          })}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-extrabold text-slate-900">{total}</span>
          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Total</span>
        </div>
      </div>

      <div className="flex-1 w-full space-y-2.5">
        {items.map((item, idx) => {
          const pct = Math.round((item.value / total) * 100);
          return (
            <div key={item.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="flex items-center gap-2 font-semibold text-slate-700">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PALETTE[idx % PALETTE.length] }} />
                  {item.label}
                </span>
                <span className="font-mono font-semibold text-slate-600">
                  {item.value} ({pct}%)
                </span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: PALETTE[idx % PALETTE.length] }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function DashboardView({ metricas, citas = [], lotes = [], fichas = [], onNavigate }) {
  const resumen = metricas?.resumen || {};
  const especiesItems = (metricas?.especies || []).map((e) => ({ label: e.especie, value: e.total }));
  const citasItems = (metricas?.estados_citas || []).map((c) => ({ label: c.estado, value: c.total }));

  const lotesCriticos = lotes.filter((l) => l.estado_fefo !== 'FEFO_NORMAL');
  const lotesVista = lotesCriticos.length > 0 ? lotesCriticos : lotes;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          title="Tutores Registrados"
          value={resumen.tutores_activos ?? 0}
          subtitle="Validados con RUT Módulo 11"
          icon={Users}
          tone="info"
        />
        <KpiCard
          title="Pacientes Activos"
          value={resumen.mascotas_activas ?? 0}
          subtitle="Expediente clínico digital"
          icon={PawPrint}
          tone="purple"
        />
        <KpiCard
          title="Citas Programadas Hoy"
          value={resumen.citas_hoy ?? 0}
          subtitle="Control anti-solapamiento"
          icon={CalendarCheck2}
          tone="emerald"
        />
        <KpiCard
          title="Alerta Medicamentos FEFO"
          value={resumen.lotes_por_vencer ?? 0}
          subtitle="Vencen en ≤45 días o bloqueados"
          icon={AlertTriangle}
          tone="danger"
          highlightRed
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel
          title="Distribución por Especie"
          subtitle="Pacientes activos en base de datos RDS"
          icon={PieChart}
          action={
            <button
              onClick={() => onNavigate('pacientes')}
              className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800 cursor-pointer"
            >
              Ver directorio <ArrowRight className="w-3.5 h-3.5" />
            </button>
          }
        >
          <DonutChart items={especiesItems} emptyText="Sin pacientes activos aún." />
        </Panel>

        <Panel
          title="Estado de Agenda Médica"
          subtitle="Cumplimiento y control de asistencia"
          icon={Activity}
          action={
            <button
              onClick={() => onNavigate('agenda')}
              className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 hover:text-emerald-800 cursor-pointer"
            >
              Gestionar citas <ArrowRight className="w-3.5 h-3.5" />
            </button>
          }
        >
          <DonutChart items={citasItems} emptyText="Sin citas registradas aún." />
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel
          title="Agenda Clínica Reciente"
          subtitle="Bloques horarios y estado de atención"
          icon={CalendarClock}
          action={
            <button
              onClick={() => onNavigate('agenda')}
              className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer"
            >
              Agenda Completa
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Fecha / Hora</th>
                  <th className="px-4 py-3">Paciente</th>
                  <th className="px-4 py-3">Veterinario</th>
                  <th className="px-4 py-3">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {citas.slice(0, 5).map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/80">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="font-semibold text-slate-800 text-xs">{c.fecha}</div>
                      <span className="inline-block text-[11px] font-mono bg-slate-900 text-white px-2 py-0.5 rounded-md mt-0.5">
                        {String(c.hora).slice(0, 5)}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-semibold text-slate-800">{c.mascota_nombre}</td>
                    <td className="px-4 py-3 text-slate-600 text-xs">Dr(a). {c.veterinario_nombre}</td>
                    <td className="px-4 py-3"><EstadoBadge estado={c.estado} /></td>
                  </tr>
                ))}
                {citas.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-400">Sin citas registradas.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="Prioridad de Salida (Norma FEFO)"
          subtitle="First Expired, First Out — alertas de vencimiento"
          icon={Pill}
          action={
            <button
              onClick={() => onNavigate('farmacia')}
              className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700 cursor-pointer"
            >
              Abrir Farmacia
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Lote / Fármaco</th>
                  <th className="px-4 py-3">Vencimiento</th>
                  <th className="px-4 py-3">Stock</th>
                  <th className="px-4 py-3">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lotesVista.slice(0, 5).map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/80">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800 text-xs sm:text-sm">{l.nombre}</div>
                      <div className="text-[11px] font-mono text-slate-500">{l.codigo_lote}</div>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-slate-700 whitespace-nowrap">{l.fecha_vencimiento}</td>
                    <td className="px-4 py-3 font-bold text-slate-900 whitespace-nowrap">{l.stock_disponible} u.</td>
                    <td className="px-4 py-3"><EstadoBadge estado={l.estado_fefo} /></td>
                  </tr>
                ))}
                {lotesVista.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-400">Sin lotes registrados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>

      <Panel
        title="Últimas Fichas Clínicas Emitidas"
        subtitle="Trazabilidad médica con control de peso y dispensación"
        icon={FileText}
        action={
          <button
            onClick={() => onNavigate('fichas')}
            className="text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer"
          >
            Ver Fichas
          </button>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Ficha</th>
                <th className="px-4 py-3">Paciente</th>
                <th className="px-4 py-3">Profesional</th>
                <th className="px-4 py-3">Signos Vitales</th>
                <th className="px-4 py-3">Diagnóstico</th>
                <th className="px-4 py-3">Lote FEFO</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {fichas.slice(0, 4).map((f) => (
                <tr key={f.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono font-bold text-slate-700">#{f.id}</td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{f.mascota_nombre}</td>
                  <td className="px-4 py-3 text-slate-600 text-xs">Dr(a). {f.veterinario_nombre}</td>
                  <td className="px-4 py-3 text-xs font-mono text-slate-700">
                    {f.peso_registrado} kg · {f.temperatura_c} °C
                  </td>
                  <td className="px-4 py-3 text-slate-700 max-w-xs truncate">{f.diagnostico}</td>
                  <td className="px-4 py-3 font-mono text-xs text-emerald-700">{f.lote_fefo_info || '—'}</td>
                </tr>
              ))}
              {fichas.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-6 text-center text-slate-400">Sin fichas emitidas todavía.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
