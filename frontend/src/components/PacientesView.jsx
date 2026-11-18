import { useState } from 'react';
import { FolderOpen, Mail, MapPin, PawPrint, Phone, Plus, Power, Printer, UserPlus, Users, X } from 'lucide-react';
import { validarRutChileno } from '../api.js';
import { EstadoBadge, Panel, SearchBar, btnEmerald, inputCls } from './UiParts.jsx';

export default function PacientesView({
  tutores = [],
  mascotas = [],
  citas = [],
  fichas = [],
  recordatorios = [],
  onCreate,
  onPatch,
}) {
  const [busqueda, setBusqueda] = useState('');
  const [rutError, setRutError] = useState('');
  const [expedienteMascota, setExpedienteMascota] = useState(null);
  const [tutorForm, setTutorForm] = useState({
    rut: '',
    nombre_completo: '',
    telefono: '+569',
    email: '',
    direccion: '',
  });
  const [mascotaForm, setMascotaForm] = useState({
    tutor: '',
    nombre: '',
    especie: 'CANINO',
    raza: '',
    sexo: 'M',
    fecha_nacimiento: '2022-01-01',
    peso_kg: '10.0',
    alergias_conocidas: '',
    foto_url: '',
  });
  const [busy, setBusy] = useState(false);

  async function submitTutor(e) {
    e.preventDefault();
    const err = validarRutChileno(tutorForm.rut);
    if (err) {
      setRutError(err);
      return;
    }
    setRutError('');
    setBusy(true);
    try {
      await onCreate('/tutores/', tutorForm, 'Tutor registrado correctamente.');
      setTutorForm({ rut: '', nombre_completo: '', telefono: '+569', email: '', direccion: '' });
    } finally {
      setBusy(false);
    }
  }

  async function submitMascota(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate('/mascotas/', { ...mascotaForm, tutor: Number(mascotaForm.tutor) }, 'Mascota registrada correctamente.');
      setMascotaForm((m) => ({ ...m, nombre: '', raza: '', alergias_conocidas: '', foto_url: '' }));
    } finally {
      setBusy(false);
    }
  }

  const q = busqueda.trim().toLowerCase();
  const mascotasFiltradas = mascotas.filter(
    (m) => !q || m.nombre.toLowerCase().includes(q) || m.raza.toLowerCase().includes(q) || (m.tutor_nombre || '').toLowerCase().includes(q)
  );
  const tutoresFiltrados = tutores.filter(
    (t) => !q || t.nombre_completo.toLowerCase().includes(q) || t.rut.toLowerCase().includes(q) || t.email.toLowerCase().includes(q)
  );
  const tutoresActivos = tutores.filter((t) => t.activo);

  const citasExp = expedienteMascota ? citas.filter((c) => c.mascota === expedienteMascota.id) : [];
  const fichasExp = expedienteMascota ? fichas.filter((f) => f.mascota === expedienteMascota.id) : [];
  const recExp = expedienteMascota ? recordatorios.filter((r) => r.mascota === expedienteMascota.id) : [];

  return (
    <div className="space-y-6">
      {expedienteMascota && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-900 text-white rounded-t-3xl">
              <div>
                <h3 className="font-bold text-base">Expediente Clínico · {expedienteMascota.nombre}</h3>
                <p className="text-xs text-slate-300">
                  {expedienteMascota.especie} · {expedienteMascota.raza} · Peso: {expedienteMascota.peso_kg} kg · Tutor: {expedienteMascota.tutor_nombre}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => window.print()} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 font-semibold cursor-pointer">
                  <Printer className="w-3.5 h-3.5" /> Imprimir
                </button>
                <button onClick={() => setExpedienteMascota(null)} className="p-1.5 rounded-lg hover:bg-white/10 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-5 text-sm">
              {expedienteMascota.alergias_conocidas && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                  <strong>Alergias / Observaciones:</strong> {expedienteMascota.alergias_conocidas}
                </div>
              )}

              <div>
                <h4 className="font-bold text-slate-800 mb-2">Fichas Clínicas ({fichasExp.length})</h4>
                {fichasExp.length === 0 ? (
                  <p className="text-xs text-slate-400">Sin fichas registradas.</p>
                ) : (
                  <div className="space-y-2">
                    {fichasExp.map((f) => (
                      <div key={f.id} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/70 space-y-1">
                        <div className="flex justify-between text-xs text-slate-500">
                          <span className="font-mono font-bold text-slate-800">Ficha #{f.id} · Dr(a). {f.veterinario_nombre}</span>
                          <span>Peso {f.peso_registrado} kg · {f.temperatura_c} °C</span>
                        </div>
                        <p className="text-xs"><strong>Diagnóstico:</strong> {f.diagnostico}</p>
                        <p className="text-xs"><strong>Tratamiento:</strong> {f.tratamiento}</p>
                        {f.lote_fefo_info && <p className="text-xs text-emerald-700 font-mono">Dispensación FEFO: {f.lote_fefo_info} ({f.cantidad_dispensada} u.)</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-bold text-slate-800 mb-2">Citas ({citasExp.length})</h4>
                  <div className="space-y-1.5">
                    {citasExp.map((c) => (
                      <div key={c.id} className="text-xs p-2.5 rounded-xl border border-slate-200 flex items-center justify-between">
                        <span>{c.fecha} {String(c.hora).slice(0, 5)} · {c.motivo}</span>
                        <EstadoBadge estado={c.estado} />
                      </div>
                    ))}
                    {citasExp.length === 0 && <p className="text-xs text-slate-400">Sin citas registradas.</p>}
                  </div>
                </div>
                <div>
                  <h4 className="font-bold text-slate-800 mb-2">Vacunas y Controles ({recExp.length})</h4>
                  <div className="space-y-1.5">
                    {recExp.map((r) => (
                      <div key={r.id} className="text-xs p-2.5 rounded-xl border border-slate-200 flex items-center justify-between">
                        <span>{r.fecha_programada} · {r.nombre_vacuna_control}</span>
                        <EstadoBadge estado={r.estado_asistencia} />
                      </div>
                    ))}
                    {recExp.length === 0 && <p className="text-xs text-slate-400">Sin recordatorios registrados.</p>}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Panel title="Registrar Tutor" subtitle="Validación chilena de RUT Módulo 11 en vivo" icon={UserPlus}>
          <form onSubmit={submitTutor} className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-600">RUT</label>
              <input
                className={`${inputCls} ${rutError ? 'border-rose-400' : ''}`}
                required
                placeholder="18456789-K"
                value={tutorForm.rut}
                onChange={(e) => {
                  setTutorForm({ ...tutorForm, rut: e.target.value });
                  if (rutError) setRutError(validarRutChileno(e.target.value));
                }}
                onBlur={(e) => setRutError(e.target.value ? validarRutChileno(e.target.value) : '')}
              />
              {rutError && <p className="text-[11px] text-rose-600 mt-1">{rutError}</p>}
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Nombre y Apellidos</label>
              <input className={inputCls} required placeholder="Camila Soto" value={tutorForm.nombre_completo} onChange={(e) => setTutorForm({ ...tutorForm, nombre_completo: e.target.value })} />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Teléfono</label>
              <input className={inputCls} required placeholder="+56912345678" value={tutorForm.telefono} onChange={(e) => setTutorForm({ ...tutorForm, telefono: e.target.value })} />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Correo</label>
              <input className={inputCls} type="email" required placeholder="tutor@correo.cl" value={tutorForm.email} onChange={(e) => setTutorForm({ ...tutorForm, email: e.target.value })} />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-600">Dirección</label>
              <input className={inputCls} required placeholder="Av. Alemania 0840, Temuco" value={tutorForm.direccion} onChange={(e) => setTutorForm({ ...tutorForm, direccion: e.target.value })} />
            </div>
            <div className="sm:col-span-2 flex justify-end pt-1">
              <button disabled={busy} className={btnEmerald}>
                <Plus className="w-4 h-4" /> Guardar Tutor
              </button>
            </div>
          </form>
        </Panel>

        <Panel title="Registrar Paciente (Mascota)" subtitle="Asociado a un tutor activo" icon={PawPrint}>
          <form onSubmit={submitMascota} className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-600">Tutor Responsable</label>
              <select className={inputCls} required value={mascotaForm.tutor} onChange={(e) => setMascotaForm({ ...mascotaForm, tutor: e.target.value })}>
                <option value="">Selecciona un tutor...</option>
                {tutoresActivos.map((t) => (
                  <option key={t.id} value={t.id}>{t.nombre_completo} ({t.rut})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Nombre</label>
              <input className={inputCls} required placeholder="Thor" value={mascotaForm.nombre} onChange={(e) => setMascotaForm({ ...mascotaForm, nombre: e.target.value })} />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Especie</label>
              <select className={inputCls} value={mascotaForm.especie} onChange={(e) => setMascotaForm({ ...mascotaForm, especie: e.target.value })}>
                <option value="CANINO">Canino</option>
                <option value="FELINO">Felino</option>
                <option value="EXOTICO">Exótico</option>
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Raza</label>
              <input className={inputCls} required placeholder="Pastor Alemán" value={mascotaForm.raza} onChange={(e) => setMascotaForm({ ...mascotaForm, raza: e.target.value })} />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Sexo / Peso (kg)</label>
              <div className="flex gap-2">
                <select className={inputCls} value={mascotaForm.sexo} onChange={(e) => setMascotaForm({ ...mascotaForm, sexo: e.target.value })}>
                  <option value="M">Macho</option>
                  <option value="H">Hembra</option>
                </select>
                <input className={inputCls} type="number" step="0.1" min="0.1" max="120" required value={mascotaForm.peso_kg} onChange={(e) => setMascotaForm({ ...mascotaForm, peso_kg: e.target.value })} />
              </div>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Fecha Nacimiento</label>
              <input className={inputCls} type="date" required value={mascotaForm.fecha_nacimiento} onChange={(e) => setMascotaForm({ ...mascotaForm, fecha_nacimiento: e.target.value })} />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Alergias</label>
              <input className={inputCls} placeholder="Opcional" value={mascotaForm.alergias_conocidas} onChange={(e) => setMascotaForm({ ...mascotaForm, alergias_conocidas: e.target.value })} />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-600">URL Foto S3 / CDN (opcional)</label>
              <input className={inputCls} type="url" placeholder="https://tu-bucket.s3.amazonaws.com/fotos/thor.jpg" value={mascotaForm.foto_url} onChange={(e) => setMascotaForm({ ...mascotaForm, foto_url: e.target.value })} />
            </div>
            <div className="sm:col-span-2 flex justify-end pt-1">
              <button disabled={busy} className={btnEmerald}>
                <Plus className="w-4 h-4" /> Guardar Paciente
              </button>
            </div>
          </form>
        </Panel>
      </div>

      <Panel
        title="Pacientes Registrados"
        subtitle={`${mascotasFiltradas.length} de ${mascotas.length} pacientes`}
        icon={PawPrint}
        action={<SearchBar value={busqueda} onChange={setBusqueda} placeholder="Filtrar paciente, raza o tutor..." />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Paciente</th>
                <th className="px-4 py-3">Especie / Raza</th>
                <th className="px-4 py-3">Peso</th>
                <th className="px-4 py-3">Tutor</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {mascotasFiltradas.map((m) => (
                <tr key={m.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-semibold text-slate-900">
                    <div className="flex items-center gap-2.5">
                      {m.foto_url ? (
                        <img src={m.foto_url} alt={m.nombre} className="w-8 h-8 rounded-lg object-cover border border-slate-200" />
                      ) : (
                        <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center">
                          <PawPrint className="w-4 h-4" />
                        </div>
                      )}
                      <span>{m.nombre}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{m.especie} · {m.raza}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{m.peso_kg} kg</td>
                  <td className="px-4 py-3 text-slate-700">{m.tutor_nombre}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={m.activo ? 'ACTIVO' : 'INACTIVO'} /></td>
                  <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                    <button
                      onClick={() => setExpedienteMascota(m)}
                      className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-50 text-emerald-700 hover:bg-emerald-100 font-semibold cursor-pointer"
                    >
                      <FolderOpen className="w-3.5 h-3.5" /> Expediente
                    </button>
                    <button
                      onClick={() => onPatch(`/mascotas/${m.id}/`, { activo: !m.activo }, `Estado de ${m.nombre} actualizado.`)}
                      className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 font-semibold cursor-pointer"
                    >
                      <Power className="w-3.5 h-3.5" />
                      {m.activo ? 'Deshabilitar' : 'Reactivar'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel title="Directorio de Tutores" subtitle={`${tutoresFiltrados.length} tutores registrados`} icon={Users}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">RUT</th>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Contacto</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tutoresFiltrados.map((t) => (
                <tr key={t.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-700">{t.rut}</td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-900">{t.nombre_completo}</div>
                    <div className="flex items-center gap-1 text-[11px] text-slate-500">
                      <MapPin className="w-3 h-3" /> {t.direccion}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600 space-y-0.5">
                    <div className="flex items-center gap-1.5"><Phone className="w-3 h-3 text-slate-400" /> {t.telefono}</div>
                    <div className="flex items-center gap-1.5"><Mail className="w-3 h-3 text-slate-400" /> {t.email}</div>
                  </td>
                  <td className="px-4 py-3"><EstadoBadge estado={t.activo ? 'ACTIVO' : 'INACTIVO'} /></td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => onPatch(`/tutores/${t.id}/`, { activo: !t.activo }, `Estado de ${t.nombre_completo} actualizado.`)}
                      className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 font-semibold cursor-pointer"
                    >
                      <Power className="w-3.5 h-3.5" />
                      {t.activo ? 'Deshabilitar' : 'Reactivar'}
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
