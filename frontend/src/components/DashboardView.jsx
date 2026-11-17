import { EstadoBadge, KpiCard, Panel } from './UiParts.jsx';

export default function DashboardView({ metricas, citas = [], lotes = [], fichas = [], onNavigate }) {
  const resumen = metricas?.resumen || {};
  const especies = metricas?.especies || [];
  const estadosCitas = metricas?.estados_citas || [];
  const totalEspecies = especies.reduce((acc, e) => acc + e.total, 0) || 1;
  const totalCitas = estadosCitas.reduce((acc, c) => acc + c.total, 0) || 1;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <KpiCard
          title="Tutores Registrados"
          value={resumen.tutores_activos ?? 0}
          subtitle="Validados con RUT Módulo 11"
          icon="👥"
          tone="info"
        />
        <KpiCard
          title="Pacientes Activos"
          value={resumen.mascotas_activas ?? 0}
          subtitle="Expediente clínico digital"
          icon="🐾"
          tone="purple"
        />
        <KpiCard
          title="Citas Programadas Hoy"
          value={resumen.citas_hoy ?? 0}
          subtitle="Control anti-solapamiento"
          icon="📅"
          tone="emerald"
        />
        <KpiCard
          title="Alerta Medicamentos FEFO"
          value={resumen.lotes_por_vencer ?? 0}
          subtitle="Por vencer (≤45 días) o vencidos"
          icon="⚠️"
          tone="danger"
          highlightRed
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel
          title="Agenda Clínica Reciente"
          subtitle="Citas registradas con horario y profesional"
          action={
            <button onClick={() => onNavigate('agenda')} className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50">
              Ver Agenda →
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
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
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{c.fecha}</div>
                      <span className="inline-block text-[11px] font-mono bg-slate-900 text-white px-2 py-0.5 rounded">
                        {String(c.hora).slice(0, 5)} hrs
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-800">{c.mascota_nombre}</td>
                    <td className="px-4 py-3 text-slate-600">Dr(a). {c.veterinario_nombre}</td>
                    <td className="px-4 py-3"><EstadoBadge estado={c.estado} /></td>
                  </tr>
                ))}
                {citas.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-6 text-center text-slate-400">Sin citas registradas.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel
          title="Inventario Prioritario (Norma FEFO)"
          subtitle="First Expired, First Out — orden estricto de vencimiento"
          action={
            <button onClick={() => onNavigate('farmacia')} className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700">
              Ir a Farmacia →
            </button>
          }
        >
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-4 py-3">Lote / Fármaco</th>
                  <th className="px-4 py-3">Vencimiento</th>
                  <th className="px-4 py-3">Stock</th>
                  <th className="px-4 py-3">Prioridad</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {lotes.slice(0, 5).map((l) => (
                  <tr key={l.id} className="hover:bg-slate-50/80">
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-800">{l.nombre}</div>
                      <div className="text-[11px] font-mono text-slate-500">{l.codigo_lote}</div>
                    </td>
                    <td className="px-4 py-3 text-slate-700">{l.fecha_vencimiento}</td>
                    <td className="px-4 py-3 font-bold text-slate-900">{l.stock_disponible} u.</td>
                    <td className="px-4 py-3"><EstadoBadge estado={l.estado_fefo} /></td>
                  </tr>
                ))}
                {lotes.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-6 text-center text-slate-400">Sin lotes registrados.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="Distribución por Especie" subtitle="Pacientes activos registrados en RDS">
          <div className="p-5 space-y-3">
            {especies.map((e) => (
              <div key={e.especie}>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>{e.especie}</span>
                  <span>{e.total} ({Math.round((e.total / totalEspecies) * 100)}%)</span>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${(e.total / totalEspecies) * 100}%` }} />
                </div>
              </div>
            ))}
            {especies.length === 0 && <p className="text-sm text-slate-400">Sin datos de pacientes aún.</p>}
          </div>
        </Panel>

        <Panel title="Estado de Citas y Últimas Fichas" subtitle={`Últimas ${fichas.length} atenciones clínicas`}>
          <div className="p-5 space-y-3">
            {estadosCitas.map((c) => (
              <div key={c.estado}>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>{c.estado}</span>
                  <span>{c.total}</span>
                </div>
                <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
                  <div className="h-full bg-sky-500 rounded-full" style={{ width: `${(c.total / totalCitas) * 100}%` }} />
                </div>
              </div>
            ))}
            {estadosCitas.length === 0 && <p className="text-sm text-slate-400">Sin citas registradas aún.</p>}
          </div>
        </Panel>
      </div>
    </div>
  );
}
