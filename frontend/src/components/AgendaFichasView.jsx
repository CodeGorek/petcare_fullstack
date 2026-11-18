import { useState } from 'react';
import {
  BellPlus,
  BellRing,
  CalendarClock,
  CalendarPlus,
  CheckCircle2,
  Clock,
  FilePlus2,
  MessageCircle,
  Plus,
  Printer,
  Scale,
  Stethoscope,
  Thermometer,
  X,
  XCircle,
} from 'lucide-react';
import { apiRequest, whatsappUrl } from '../api.js';
import { EstadoBadge, Panel, SearchBar, btnEmerald, inputCls } from './UiParts.jsx';

export function AgendaView({ token, mascotas = [], veterinarios = [], citas = [], onCreate, onPatch }) {
  const hoy = new Date().toISOString().slice(0, 10);
  const [busqueda, setBusqueda] = useState('');
  const [form, setForm] = useState({
    mascota: '',
    veterinario: '',
    fecha: hoy,
    hora: '10:00',
    motivo: '',
  });
  const [bloques, setBloques] = useState([]);
  const [busy, setBusy] = useState(false);

  async function cargarDisponibilidad(vetId, fecha) {
    if (!vetId || !fecha) return;
    try {
      const res = await apiRequest(`/disponibilidad/?veterinario_id=${vetId}&fecha=${fecha}`, { token });
      setBloques(res.bloques || []);
    } catch {
      setBloques([]);
    }
  }

  async function submitCita(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate(
        '/citas/',
        { ...form, mascota: Number(form.mascota), veterinario: Number(form.veterinario) },
        'Cita agendada sin conflictos de horario.'
      );
      setForm((f) => ({ ...f, motivo: '' }));
      cargarDisponibilidad(form.veterinario, form.fecha);
    } finally {
      setBusy(false);
    }
  }

  const q = busqueda.trim().toLowerCase();
  const citasFiltradas = citas.filter(
    (c) => !q || (c.mascota_nombre || '').toLowerCase().includes(q) || (c.veterinario_nombre || '').toLowerCase().includes(q) || (c.motivo || '').toLowerCase().includes(q)
  );

  return (
    <div className="space-y-6">
      <Panel title="Agendar Cita Médica" subtitle="Validación de jornada y anti-solapamiento en tiempo real" icon={CalendarPlus}>
        <form onSubmit={submitCita} className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-600">Paciente</label>
            <select className={inputCls} required value={form.mascota} onChange={(e) => setForm({ ...form, mascota: e.target.value })}>
              <option value="">Selecciona paciente...</option>
              {mascotas.filter((m) => m.activo).map((m) => (
                <option key={m.id} value={m.id}>{m.nombre} ({m.tutor_nombre})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Veterinario</label>
            <select
              className={inputCls}
              required
              value={form.veterinario}
              onChange={(e) => {
                const v = e.target.value;
                setForm({ ...form, veterinario: v });
                cargarDisponibilidad(v, form.fecha);
              }}
            >
              <option value="">Selecciona profesional...</option>
              {veterinarios.filter((v) => v.activo).map((v) => (
                <option key={v.id} value={v.id}>Dr(a). {v.nombre} ({v.especialidad})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Fecha</label>
            <input
              className={inputCls}
              type="date"
              required
              value={form.fecha}
              onChange={(e) => {
                const f = e.target.value;
                setForm({ ...form, fecha: f });
                cargarDisponibilidad(form.veterinario, f);
              }}
            />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Hora</label>
            <input className={inputCls} type="time" required value={form.hora} onChange={(e) => setForm({ ...form, hora: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Motivo de Consulta</label>
            <input className={inputCls} required placeholder="Control general, vacunación..." value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
          </div>
          {bloques.length > 0 && (
            <div className="sm:col-span-2 lg:col-span-3 bg-slate-50 p-3 rounded-xl border border-slate-200/80">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 mb-2">
                <Clock className="w-3.5 h-3.5 text-emerald-600" />
                Bloques disponibles (clic para elegir):
              </div>
              <div className="flex flex-wrap gap-1.5">
                {bloques.map((b) => (
                  <button
                    type="button"
                    key={b.hora}
                    disabled={!b.disponible}
                    onClick={() => setForm({ ...form, hora: b.hora })}
                    className={`px-2.5 py-1 rounded-lg text-xs font-mono border cursor-pointer ${
                      !b.disponible
                        ? 'bg-slate-100 text-slate-400 border-slate-200 line-through cursor-not-allowed'
                        : form.hora === b.hora
                          ? 'bg-emerald-600 text-white border-emerald-600 font-semibold'
                          : 'bg-white text-slate-700 border-slate-300 hover:border-emerald-500'
                    }`}
                  >
                    {b.hora}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div className="sm:col-span-2 lg:col-span-3 flex justify-end pt-1">
            <button disabled={busy} className={btnEmerald}>
              <Plus className="w-4 h-4" /> Agendar Cita
            </button>
          </div>
        </form>
      </Panel>

      <Panel
        title="Agenda de Citas Médicas"
        subtitle={`${citasFiltradas.length} citas en historial`}
        icon={CalendarClock}
        action={<SearchBar value={busqueda} onChange={setBusqueda} placeholder="Buscar paciente o veterinario..." />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Fecha / Hora</th>
                <th className="px-4 py-3">Paciente</th>
                <th className="px-4 py-3">Veterinario</th>
                <th className="px-4 py-3">Motivo</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Asistencia</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {citasFiltradas.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3">
                    <span className="font-semibold text-slate-800">{c.fecha}</span>{' '}
                    <span className="text-xs font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded">{String(c.hora).slice(0, 5)}</span>
                  </td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{c.mascota_nombre}</td>
                  <td className="px-4 py-3 text-slate-700">Dr(a). {c.veterinario_nombre}</td>
                  <td className="px-4 py-3 text-slate-600">{c.motivo}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={c.estado} /></td>
                  <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                    {whatsappUrl(
                      c.tutor_telefono,
                      `Hola ${c.tutor_nombre || 'tutor'}, te recordamos la cita de ${c.mascota_nombre} el ${c.fecha} a las ${String(c.hora).slice(0, 5)} hrs en Clínica PetCare.`
                    ) && (
                      <a
                        href={whatsappUrl(
                          c.tutor_telefono,
                          `Hola ${c.tutor_nombre || 'tutor'}, te recordamos la cita de ${c.mascota_nombre} el ${c.fecha} a las ${String(c.hora).slice(0, 5)} hrs en Clínica PetCare.`
                        )}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-semibold"
                      >
                        <MessageCircle className="w-3.5 h-3.5" /> WhatsApp
                      </a>
                    )}
                    {c.estado === 'PROGRAMADA' && (
                      <>
                        <button
                          onClick={() => onPatch(`/citas/${c.id}/`, { estado: 'ASISTIO' }, 'Asistencia marcada.')}
                          className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold cursor-pointer"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" /> Asistió
                        </button>
                        <button
                          onClick={() => onPatch(`/citas/${c.id}/`, { estado: 'NO_ASISTIO' }, 'Inasistencia registrada.')}
                          className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 font-semibold cursor-pointer"
                        >
                          <XCircle className="w-3.5 h-3.5" /> No Asistió
                        </button>
                      </>
                    )}
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

export function FichasView({ mascotas = [], veterinarios = [], lotes = [], fichas = [], onCreate }) {
  const [fichaModal, setFichaModal] = useState(null);
  const [form, setForm] = useState({
    mascota: '',
    veterinario: '',
    peso_registrado: '10.0',
    temperatura_c: '38.5',
    diagnostico: '',
    tratamiento: '',
    medicamento_fefo: '',
    cantidad_dispensada: 1,
    receta_medica: '',
  });
  const [busy, setBusy] = useState(false);

  const lotesDisponibles = lotes.filter((l) => l.activo && l.stock_disponible > 0 && l.estado_fefo !== 'BLOQUEADO_VENCIDO');

  async function submitFicha(e) {
    e.preventDefault();
    setBusy(true);
    try {
      const payload = {
        ...form,
        mascota: Number(form.mascota),
        veterinario: Number(form.veterinario),
        medicamento_fefo: form.medicamento_fefo ? Number(form.medicamento_fefo) : null,
        cantidad_dispensada: Number(form.cantidad_dispensada || 1),
      };
      await onCreate('/fichas/', payload, 'Ficha clínica emitida y stock FEFO actualizado.');
      setForm((f) => ({ ...f, diagnostico: '', tratamiento: '', receta_medica: '' }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {fichaModal && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-xl w-full shadow-2xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base">Reporte Ficha Clínica #{fichaModal.id}</h3>
                <p className="text-xs text-slate-300">Paciente: {fichaModal.mascota_nombre} · Dr(a). {fichaModal.veterinario_nombre}</p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => window.print()} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 font-semibold cursor-pointer">
                  <Printer className="w-3.5 h-3.5" /> Imprimir
                </button>
                <button onClick={() => setFichaModal(null)} className="p-1.5 rounded-lg hover:bg-white/10 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-3 text-sm">
              <div className="grid grid-cols-2 gap-3 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div><span className="text-xs text-slate-500">Peso registrado:</span> <strong className="font-mono">{fichaModal.peso_registrado} kg</strong></div>
                <div><span className="text-xs text-slate-500">Temperatura:</span> <strong className="font-mono">{fichaModal.temperatura_c} °C</strong></div>
              </div>
              <div><strong className="text-xs uppercase text-slate-500 block">Diagnóstico</strong><p className="text-slate-800 mt-0.5">{fichaModal.diagnostico}</p></div>
              <div><strong className="text-xs uppercase text-slate-500 block">Tratamiento</strong><p className="text-slate-800 mt-0.5">{fichaModal.tratamiento}</p></div>
              {fichaModal.receta_medica && (
                <div><strong className="text-xs uppercase text-slate-500 block">Receta / Posología</strong><p className="text-slate-800 mt-0.5">{fichaModal.receta_medica}</p></div>
              )}
              {fichaModal.lote_fefo_info && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-900 font-mono">
                  Dispensado Lote FEFO: {fichaModal.lote_fefo_info} · {fichaModal.cantidad_dispensada} u.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      <Panel title="Emitir Ficha Clínica Digital" subtitle="Descuenta automáticamente stock del lote FEFO seleccionado" icon={FilePlus2}>
        <form onSubmit={submitFicha} className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-600">Paciente</label>
            <select className={inputCls} required value={form.mascota} onChange={(e) => setForm({ ...form, mascota: e.target.value })}>
              <option value="">Selecciona paciente...</option>
              {mascotas.filter((m) => m.activo).map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Veterinario</label>
            <select className={inputCls} required value={form.veterinario} onChange={(e) => setForm({ ...form, veterinario: e.target.value })}>
              <option value="">Selecciona profesional...</option>
              {veterinarios.filter((v) => v.activo).map((v) => <option key={v.id} value={v.id}>Dr(a). {v.nombre}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Peso (kg)</label>
            <input className={inputCls} type="number" step="0.1" min="0.1" max="120" required value={form.peso_registrado} onChange={(e) => setForm({ ...form, peso_registrado: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Temperatura (°C)</label>
            <input className={inputCls} type="number" step="0.1" min="35" max="43" required value={form.temperatura_c} onChange={(e) => setForm({ ...form, temperatura_c: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Diagnóstico Clínico</label>
            <textarea className={inputCls} rows={2} required value={form.diagnostico} onChange={(e) => setForm({ ...form, diagnostico: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Tratamiento Indicado</label>
            <textarea className={inputCls} rows={2} required value={form.tratamiento} onChange={(e) => setForm({ ...form, tratamiento: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Medicamento / Insumo Utilizado (Orden FEFO)</label>
            <select className={inputCls} value={form.medicamento_fefo} onChange={(e) => setForm({ ...form, medicamento_fefo: e.target.value })}>
              <option value="">-- Sin dispensación de farmacia --</option>
              {lotesDisponibles.map((l) => (
                <option key={l.id} value={l.id}>[Vence {l.fecha_vencimiento}] {l.nombre} (Stock: {l.stock_disponible})</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Unidades</label>
            <input className={inputCls} type="number" min="1" max="50" value={form.cantidad_dispensada} onChange={(e) => setForm({ ...form, cantidad_dispensada: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Receta / Posología</label>
            <input className={inputCls} placeholder="Opcional" value={form.receta_medica} onChange={(e) => setForm({ ...form, receta_medica: e.target.value })} />
          </div>
          <div className="sm:col-span-2 lg:col-span-4 flex justify-end pt-1">
            <button disabled={busy} className={btnEmerald}>
              <Plus className="w-4 h-4" /> Emitir Ficha Clínica
            </button>
          </div>
        </form>
      </Panel>

      <Panel title="Historial de Fichas Clínicas" subtitle={`${fichas.length} atenciones registradas`} icon={Stethoscope}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Ficha</th>
                <th className="px-4 py-3">Paciente</th>
                <th className="px-4 py-3">Profesional</th>
                <th className="px-4 py-3">Signos</th>
                <th className="px-4 py-3">Diagnóstico</th>
                <th className="px-4 py-3">Lote FEFO</th>
                <th className="px-4 py-3 text-right">Reporte</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {fichas.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono font-bold text-slate-700">#{f.id}</td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{f.mascota_nombre}</td>
                  <td className="px-4 py-3 text-slate-600">Dr(a). {f.veterinario_nombre}</td>
                  <td className="px-4 py-3 text-xs font-mono text-slate-700">
                    <span className="inline-flex items-center gap-1 mr-2"><Scale className="w-3 h-3 text-slate-400" /> {f.peso_registrado}kg</span>
                    <span className={`inline-flex items-center gap-1 ${Number(f.temperatura_c) >= 39.2 ? 'text-rose-600 font-bold' : ''}`}>
                      <Thermometer className="w-3 h-3" /> {f.temperatura_c}°C{Number(f.temperatura_c) >= 39.2 ? ' (Fiebre)' : ''}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{f.diagnostico}</td>
                  <td className="px-4 py-3 font-mono text-xs text-emerald-700">{f.lote_fefo_info || '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => setFichaModal(f)}
                      className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 font-semibold cursor-pointer"
                    >
                      <Printer className="w-3.5 h-3.5" /> Detalle
                    </button>
                  </td>
                </tr>
              ))}
              {fichas.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-400">Sin fichas emitidas todavía.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

export function RecordatoriosView({ mascotas = [], recordatorios = [], onCreate, onPatch }) {
  const [form, setForm] = useState({
    mascota: '',
    tipo: 'VACUNA',
    nombre_vacuna_control: '',
    fecha_programada: new Date().toISOString().slice(0, 10),
    hora_programada: '10:00',
    observaciones: '',
  });
  const [busy, setBusy] = useState(false);

  async function submitRec(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate('/recordatorios/', { ...form, mascota: Number(form.mascota) }, 'Citatorio registrado.');
      setForm((f) => ({ ...f, nombre_vacuna_control: '', observaciones: '' }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <Panel title="Programar Vacuna, Examen o Control" subtitle="Alertas semafóricas de asistencia" icon={BellPlus}>
        <form onSubmit={submitRec} className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-600">Paciente</label>
            <select className={inputCls} required value={form.mascota} onChange={(e) => setForm({ ...form, mascota: e.target.value })}>
              <option value="">Selecciona paciente...</option>
              {mascotas.filter((m) => m.activo).map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Tipo</label>
            <select className={inputCls} value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
              <option value="VACUNA">Vacunación</option>
              <option value="EXAMEN">Examen Clínico</option>
              <option value="DESPARASITACION">Desparasitación</option>
              <option value="CONTROL">Control Periódico</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Vacuna / Control</label>
            <input className={inputCls} required placeholder="Vacuna Óctuple" value={form.nombre_vacuna_control} onChange={(e) => setForm({ ...form, nombre_vacuna_control: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Fecha Programada</label>
            <input className={inputCls} type="date" required value={form.fecha_programada} onChange={(e) => setForm({ ...form, fecha_programada: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Hora</label>
            <input className={inputCls} type="time" required value={form.hora_programada} onChange={(e) => setForm({ ...form, hora_programada: e.target.value })} />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-600">Observaciones</label>
            <input className={inputCls} placeholder="Indicaciones..." value={form.observaciones} onChange={(e) => setForm({ ...form, observaciones: e.target.value })} />
          </div>
          <div className="sm:col-span-2 lg:col-span-3 flex justify-end pt-1">
            <button disabled={busy} className={btnEmerald}>
              <Plus className="w-4 h-4" /> Programar Citatorio
            </button>
          </div>
        </form>
      </Panel>

      <Panel title="Recordatorios y Citatorios" subtitle={`${recordatorios.length} registros`} icon={BellRing}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Fecha / Hora</th>
                <th className="px-4 py-3">Paciente</th>
                <th className="px-4 py-3">Citatorio</th>
                <th className="px-4 py-3">Alerta</th>
                <th className="px-4 py-3 text-right">Marcar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {recordatorios.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3">{r.fecha_programada} <span className="text-xs font-mono text-slate-500">{String(r.hora_programada).slice(0, 5)}</span></td>
                  <td className="px-4 py-3 font-semibold text-slate-900">{r.mascota_nombre}</td>
                  <td className="px-4 py-3 text-slate-700">{r.nombre_vacuna_control}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={r.estado_asistencia} /></td>
                  <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                    {whatsappUrl(
                      r.tutor_telefono,
                      `Hola ${r.tutor_nombre || 'tutor'}, recordatorio PetCare: ${r.nombre_vacuna_control} para ${r.mascota_nombre} el ${r.fecha_programada} a las ${String(r.hora_programada).slice(0, 5)} hrs.`
                    ) && (
                      <a
                        href={whatsappUrl(
                          r.tutor_telefono,
                          `Hola ${r.tutor_nombre || 'tutor'}, recordatorio PetCare: ${r.nombre_vacuna_control} para ${r.mascota_nombre} el ${r.fecha_programada} a las ${String(r.hora_programada).slice(0, 5)} hrs.`
                        )}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-semibold"
                      >
                        <MessageCircle className="w-3.5 h-3.5" /> WhatsApp
                      </a>
                    )}
                    <button
                      onClick={() => onPatch(`/recordatorios/${r.id}/`, { estado: 'ASISTIO', notificado: true }, 'Asistencia registrada.')}
                      className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> Asistió
                    </button>
                    <button
                      onClick={() => onPatch(`/recordatorios/${r.id}/`, { estado: 'NO_ASISTIO', notificado: true }, 'Inasistencia registrada.')}
                      className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg bg-rose-50 text-rose-700 hover:bg-rose-100 font-semibold cursor-pointer"
                    >
                      <XCircle className="w-3.5 h-3.5" /> No Asistió
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
