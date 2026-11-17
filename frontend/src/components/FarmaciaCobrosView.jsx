import { useState } from 'react';
import { CreditCard, ExternalLink, Minus, PackagePlus, Pill, Plus, Receipt, Tags } from 'lucide-react';
import { BACKEND_ORIGIN, formatClp } from '../api.js';
import { EstadoBadge, Panel, SearchBar, btnEmerald, inputCls } from './UiParts.jsx';

export function FarmaciaView({ lotes = [], onCreate, onPatch }) {
  const [busqueda, setBusqueda] = useState('');
  const [form, setForm] = useState({
    nombre: '',
    categoria: 'MEDICAMENTO',
    codigo_lote: '',
    presentacion: 'Comprimidos / Frasco Ampolla',
    fecha_vencimiento: '',
    tiempo_limite_uso: 'Usar hasta fecha de vencimiento (Envase sellado)',
    stock_disponible: 10,
    precio_unitario: 2000,
  });
  const [busy, setBusy] = useState(false);

  async function submitLote(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate('/medicamentos-fefo/', {
        ...form,
        stock_disponible: Number(form.stock_disponible),
        precio_unitario: form.precio_unitario ? Number(form.precio_unitario) : null,
      }, 'Lote ingresado y ordenado por Norma FEFO.');
      setForm((f) => ({ ...f, nombre: '', codigo_lote: '' }));
    } finally {
      setBusy(false);
    }
  }

  const q = busqueda.trim().toLowerCase();
  const lotesFiltrados = lotes.filter(
    (l) => !q || l.nombre.toLowerCase().includes(q) || l.codigo_lote.toLowerCase().includes(q)
  );

  return (
    <div className="space-y-6">
      <Panel title="Ingresar Lote a Farmacia (Norma FEFO)" subtitle="Ordenamiento automático por fecha más próxima a vencer" icon={PackagePlus}>
        <form onSubmit={submitLote} className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Medicamento / Insumo</label>
            <input className={inputCls} required placeholder="Meloxicam Inyectable 2%" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Categoría</label>
            <select className={inputCls} value={form.categoria} onChange={(e) => setForm({ ...form, categoria: e.target.value })}>
              <option value="MEDICAMENTO">Medicamento</option>
              <option value="VACUNA_BIO">Biológico / Vacuna</option>
              <option value="INSUMO">Insumo Clínico</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Código de Lote</label>
            <input className={inputCls} required placeholder="FEFO-2026-M12" value={form.codigo_lote} onChange={(e) => setForm({ ...form, codigo_lote: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Fecha Vencimiento</label>
            <input className={inputCls} type="date" required value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Stock Inicial</label>
            <input className={inputCls} type="number" min="1" required value={form.stock_disponible} onChange={(e) => setForm({ ...form, stock_disponible: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Precio Unitario (CLP)</label>
            <input className={inputCls} type="number" min="1" value={form.precio_unitario} onChange={(e) => setForm({ ...form, precio_unitario: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Presentación</label>
            <input className={inputCls} value={form.presentacion} onChange={(e) => setForm({ ...form, presentacion: e.target.value })} />
          </div>
          <div className="sm:col-span-2 lg:col-span-4 flex justify-end pt-1">
            <button disabled={busy} className={btnEmerald}>
              <Plus className="w-4 h-4" /> Registrar Lote FEFO
            </button>
          </div>
        </form>
      </Panel>

      <Panel
        title="Inventario FEFO"
        subtitle={`${lotesFiltrados.length} lotes registrados`}
        icon={Pill}
        action={<SearchBar value={busqueda} onChange={setBusqueda} placeholder="Buscar lote o fármaco..." />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Lote</th>
                <th className="px-4 py-3">Producto</th>
                <th className="px-4 py-3">Vencimiento</th>
                <th className="px-4 py-3">Stock</th>
                <th className="px-4 py-3">Precio</th>
                <th className="px-4 py-3">Prioridad FEFO</th>
                <th className="px-4 py-3 text-right">Stock</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {lotesFiltrados.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono text-xs font-bold text-slate-700">{l.codigo_lote}</td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-900">{l.nombre}</div>
                    <div className="text-[11px] text-slate-500">{l.presentacion}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{l.fecha_vencimiento}</td>
                  <td className="px-4 py-3 font-bold text-slate-900">{l.stock_disponible}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{l.precio_unitario ? formatClp(l.precio_unitario) : 'Pendiente'}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={l.estado_fefo} /></td>
                  <td className="px-4 py-3 text-right space-x-1.5">
                    <button
                      disabled={l.estado_fefo === 'BLOQUEADO_VENCIDO' || l.stock_disponible < 1}
                      onClick={() => onPatch(`/medicamentos-fefo/${l.id}/`, { stock_disponible: l.stock_disponible - 1 }, `Se dispensó 1 u. de ${l.codigo_lote}.`)}
                      className="inline-flex items-center gap-0.5 text-xs px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 disabled:opacity-40 font-semibold cursor-pointer"
                    >
                      <Minus className="w-3 h-3" /> 1
                    </button>
                    <button
                      onClick={() => onPatch(`/medicamentos-fefo/${l.id}/`, { stock_disponible: l.stock_disponible + 5 }, `Se agregaron +5 u. a ${l.codigo_lote}.`)}
                      className="inline-flex items-center gap-0.5 text-xs px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold cursor-pointer"
                    >
                      <Plus className="w-3 h-3" /> 5
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

export function CobrosView({ servicios = [], cuentas = [], onCreate }) {
  const [servicioForm, setServicioForm] = useState({ nombre: '', precio: 15000 });
  const [busy, setBusy] = useState(false);

  async function submitServicio(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate('/servicios/', { nombre: servicioForm.nombre, precio: Number(servicioForm.precio), activo: true }, 'Servicio clínico agregado.');
      setServicioForm({ nombre: '', precio: 15000 });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="Agregar Servicio Clínico" subtitle="Catálogo de prestaciones para cuentas de atención" icon={Tags}>
          <form onSubmit={submitServicio} className="p-5 grid grid-cols-1 sm:grid-cols-3 gap-3 items-end">
            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-600">Nombre del Servicio</label>
              <input className={inputCls} required placeholder="Ecografía Abdominal" value={servicioForm.nombre} onChange={(e) => setServicioForm({ ...servicioForm, nombre: e.target.value })} />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Precio (CLP)</label>
              <input className={inputCls} type="number" min="1" required value={servicioForm.precio} onChange={(e) => setServicioForm({ ...servicioForm, precio: e.target.value })} />
            </div>
            <div className="sm:col-span-3 flex justify-end pt-1">
              <button disabled={busy} className={btnEmerald}>
                <Plus className="w-4 h-4" /> Guardar Servicio
              </button>
            </div>
          </form>
        </Panel>

        <Panel
          title="Portal de Pagos Webpay (Integración)"
          subtitle="Pagos simulados en ambiente TEST Transbank"
          icon={CreditCard}
          action={
            <a href={`${BACKEND_ORIGIN}/cuentas/`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-900 text-white hover:bg-slate-800">
              Abrir Cobros Webpay <ExternalLink className="w-3.5 h-3.5" />
            </a>
          }
        >
          <div className="p-5 grid grid-cols-2 gap-4">
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/70">
              <p className="text-xs font-semibold text-slate-500">Servicios activos</p>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">{servicios.length}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/70">
              <p className="text-xs font-semibold text-slate-500">Cuentas emitidas</p>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">{cuentas.length}</p>
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Catálogo de Servicios Clínicos" subtitle="Precios vigentes en CLP" icon={Tags}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Servicio</th>
                <th className="px-4 py-3">Precio CLP</th>
                <th className="px-4 py-3">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {servicios.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-semibold text-slate-900">{s.nombre}</td>
                  <td className="px-4 py-3 font-mono text-slate-700">{formatClp(s.precio)}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={s.activo ? 'ACTIVO' : 'INACTIVO'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Cuentas de Atención" subtitle="Detalle de cobros generados desde fichas clínicas" icon={Receipt}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Cuenta</th>
                <th className="px-4 py-3">Ficha</th>
                <th className="px-4 py-3">Total CLP</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Webpay</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cuentas.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono font-bold text-slate-800">#{c.id}</td>
                  <td className="px-4 py-3 font-mono text-slate-600">#{c.ficha}</td>
                  <td className="px-4 py-3 font-bold text-slate-900">{formatClp(c.total)}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={c.pagada ? 'PAGADA' : 'PENDIENTE'} /></td>
                  <td className="px-4 py-3 text-right">
                    <a href={`${BACKEND_ORIGIN}/cuentas/${c.id}/`} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 font-semibold">
                      Ver / Pagar <ExternalLink className="w-3 h-3" />
                    </a>
                  </td>
                </tr>
              ))}
              {cuentas.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">Sin cuentas generadas aún.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
