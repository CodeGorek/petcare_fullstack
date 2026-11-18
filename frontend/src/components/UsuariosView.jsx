import { useState } from 'react';
import {
  CalendarClock,
  ClipboardCheck,
  Clock,
  MessageCircle,
  Power,
  ShieldCheck,
  Trash2,
  UserCheck,
  UserPlus,
  Users,
} from 'lucide-react';
import { apiRequest, validarEmail, validarRutChileno, whatsappUrl } from '../api.js';
import { EstadoBadge, Panel, SearchBar, btnEmerald, inputCls } from './UiParts.jsx';

const ESTADO_LABORAL_STYLE = {
  ACTIVO: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  FALTA: 'bg-amber-50 text-amber-800 border-amber-200',
  LICENCIA: 'bg-sky-50 text-sky-700 border-sky-200',
  VACACIONES: 'bg-violet-50 text-violet-700 border-violet-200',
  RENUNCIA: 'bg-rose-50 text-rose-700 border-rose-200',
  DESPIDO: 'bg-rose-100 text-rose-800 border-rose-300',
  DESHABILITADO: 'bg-slate-100 text-slate-600 border-slate-200',
};

const TIPOS_NOVEDAD = [
  { id: 'FALTA', label: 'Falta / Inasistencia' },
  { id: 'LICENCIA', label: 'Licencia Médica' },
  { id: 'VACACIONES', label: 'Vacaciones' },
  { id: 'RENUNCIA', label: 'Renuncia' },
  { id: 'DESPIDO', label: 'Despido / Desvinculación' },
  { id: 'REINTEGRO', label: 'Reintegro / Activo' },
];

export default function UsuariosView({
  token,
  usuarios = [],
  novedades = [],
  currentUserId,
  onCreate,
  onNotify,
  onReload,
}) {
  const hoy = new Date().toISOString().slice(0, 10);
  const [busqueda, setBusqueda] = useState('');
  const [filtroNovedad, setFiltroNovedad] = useState('TODOS');
  const [rutError, setRutError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({
    username: '',
    password: '',
    nombre_completo: '',
    rut: '',
    email: '',
    telefono: '+569',
    rol: 'VETERINARIO',
    especialidad: 'GENERAL',
    fecha_ingreso: hoy,
    hora_inicio: '09:00',
    hora_fin: '18:00',
  });

  const [novForm, setNovForm] = useState({
    usuario: '',
    tipo: 'FALTA',
    fecha_inicio: hoy,
    hora_inicio: '09:00',
    fecha_fin: hoy,
    hora_fin: '18:00',
    observaciones: '',
  });

  const filtrados = usuarios.filter((u) => {
    const q = busqueda.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      (u.first_name || '').toLowerCase().includes(q) ||
      (u.email || '').toLowerCase().includes(q)
    );
  });

  const novedadesFiltradas = novedades.filter(
    (n) => filtroNovedad === 'TODOS' || n.tipo === filtroNovedad
  );

  const personalGestionable = usuarios.filter((u) => !u.is_superuser);
  const conteoEstados = {
    activos: usuarios.filter((u) => u.is_active && (!u.estado_laboral || u.estado_laboral === 'ACTIVO')).length,
    permisos: usuarios.filter((u) => ['LICENCIA', 'VACACIONES'].includes(u.estado_laboral)).length,
    faltas: novedades.filter((n) => n.tipo === 'FALTA').length,
    bajas: novedades.filter((n) => ['RENUNCIA', 'DESPIDO'].includes(n.tipo)).length,
  };

  async function submitUsuario(e) {
    e.preventDefault();
    const rErr = validarRutChileno(form.rut);
    const eErr = validarEmail(form.email);
    if (rErr || eErr) {
      setRutError(rErr);
      setEmailError(eErr);
      return;
    }
    setBusy(true);
    try {
      await onCreate('/usuarios/', form, `Cuenta "${form.username}" habilitada correctamente.`);
      setForm({
        username: '',
        password: '',
        nombre_completo: '',
        rut: '',
        email: '',
        telefono: '+569',
        rol: 'VETERINARIO',
        especialidad: 'GENERAL',
        fecha_ingreso: hoy,
        hora_inicio: '09:00',
        hora_fin: '18:00',
      });
      setRutError('');
      setEmailError('');
    } finally {
      setBusy(false);
    }
  }

  async function submitNovedad(e) {
    e.preventDefault();
    if (!novForm.usuario) {
      onNotify?.('error', 'Selecciona el colaborador.');
      return;
    }
    setBusy(true);
    try {
      const payload = {
        ...novForm,
        usuario: Number(novForm.usuario),
        fecha_fin: novForm.fecha_fin || null,
        hora_fin: novForm.hora_fin || null,
      };
      await onCreate('/novedades-personal/', payload, 'Registro laboral guardado con fecha y horario.');
      setNovForm((prev) => ({ ...prev, observaciones: '' }));
    } finally {
      setBusy(false);
    }
  }

  async function toggleActivo(u) {
    setBusy(true);
    try {
      await apiRequest(`/usuarios/${u.id}/toggle-activo/`, { method: 'POST', token });
      onNotify?.('ok', `Cuenta "${u.username}" ${u.is_active ? 'deshabilitada' : 'habilitada'}.`);
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    } finally {
      setBusy(false);
    }
  }

  async function eliminarNovedad(id) {
    setBusy(true);
    try {
      await apiRequest(`/novedades-personal/${id}/`, { method: 'DELETE', token });
      onNotify?.('ok', 'Registro eliminado del historial de personal.');
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <p className="text-xs font-semibold text-slate-500">Colaboradores Activos</p>
          <p className="text-2xl font-extrabold text-emerald-700 mt-1">{conteoEstados.activos}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <p className="text-xs font-semibold text-slate-500">Licencia / Vacaciones</p>
          <p className="text-2xl font-extrabold text-sky-700 mt-1">{conteoEstados.permisos}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <p className="text-xs font-semibold text-slate-500">Faltas Registradas</p>
          <p className="text-2xl font-extrabold text-amber-600 mt-1">{conteoEstados.faltas}</p>
        </div>
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs">
          <p className="text-xs font-semibold text-slate-500">Renuncias y Despidos</p>
          <p className="text-2xl font-extrabold text-rose-600 mt-1">{conteoEstados.bajas}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <Panel
          title="Crear Cuenta de Usuario o Veterinario"
          subtitle="Exclusivo Administrador Root · Validación chilena de RUT y correo"
          icon={UserPlus}
        >
          <form onSubmit={submitUsuario} className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-600">Usuario (Login)</label>
              <input
                className={inputCls}
                required
                placeholder="Ej: dr.valdes"
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Contraseña (mín. 8 caracteres)</label>
              <input
                className={inputCls}
                type="password"
                required
                minLength={8}
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Nombre Completo</label>
              <input
                className={inputCls}
                required
                placeholder="Dr. Sebastián Valdés"
                value={form.nombre_completo}
                onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">RUT Profesional</label>
              <input
                className={`${inputCls} ${rutError ? 'border-rose-400' : ''}`}
                required
                placeholder="14222888-2"
                value={form.rut}
                onChange={(e) => {
                  const val = e.target.value;
                  setForm({ ...form, rut: val });
                  if (rutError) setRutError(validarRutChileno(val));
                }}
                onBlur={(e) => setRutError(e.target.value ? validarRutChileno(e.target.value) : '')}
              />
              {rutError && <p className="text-[11px] text-rose-600 mt-1">{rutError}</p>}
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Correo Institucional</label>
              <input
                className={`${inputCls} ${emailError ? 'border-rose-400' : ''}`}
                type="email"
                required
                placeholder="profesional@petcare.cl"
                value={form.email}
                onChange={(e) => {
                  const val = e.target.value;
                  setForm({ ...form, email: val });
                  if (emailError) setEmailError(validarEmail(val));
                }}
                onBlur={(e) => setEmailError(e.target.value ? validarEmail(e.target.value) : '')}
              />
              {emailError && <p className="text-[11px] text-rose-600 mt-1">{emailError}</p>}
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">WhatsApp / Teléfono Especialista</label>
              <input
                className={inputCls}
                placeholder="+56912345678"
                value={form.telefono}
                onChange={(e) => setForm({ ...form, telefono: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Rol en el Sistema</label>
              <select className={inputCls} value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value })}>
                <option value="VETERINARIO">Médico Veterinario (Con Agenda)</option>
                <option value="RECEPCION">Recepción / Asistente Clínico</option>
              </select>
            </div>
            {form.rol === 'VETERINARIO' && (
              <>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Especialidad Médica</label>
                  <select className={inputCls} value={form.especialidad} onChange={(e) => setForm({ ...form, especialidad: e.target.value })}>
                    <option value="GENERAL">Medicina General</option>
                    <option value="CIRUGIA">Cirugía y Traumatología</option>
                    <option value="DERMATOLOGIA">Dermatología</option>
                    <option value="EXOTICOS">Medicina de Exóticos</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-600">Fecha de Ingreso</label>
                  <input className={inputCls} type="date" value={form.fecha_ingreso} onChange={(e) => setForm({ ...form, fecha_ingreso: e.target.value })} />
                </div>
                <div className="sm:col-span-2 grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs font-semibold text-slate-600">Horario Inicio</label>
                    <input className={inputCls} type="time" value={form.hora_inicio} onChange={(e) => setForm({ ...form, hora_inicio: e.target.value })} />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-600">Horario Fin</label>
                    <input className={inputCls} type="time" value={form.hora_fin} onChange={(e) => setForm({ ...form, hora_fin: e.target.value })} />
                  </div>
                </div>
              </>
            )}
            <div className="sm:col-span-2 flex justify-end pt-1">
              <button disabled={busy} className={btnEmerald}>
                <UserCheck className="w-4 h-4" /> Crear y Habilitar Cuenta
              </button>
            </div>
          </form>
        </Panel>

        <Panel
          title="Control de Asistencias, Licencias, Vacaciones y Bajas"
          subtitle="Registra fecha y horario exacto · Renuncia o Despido bloquean el acceso automáticamente"
          icon={ClipboardCheck}
        >
          <form onSubmit={submitNovedad} className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-xs font-semibold text-slate-600">Colaborador</label>
              <select
                className={inputCls}
                required
                value={novForm.usuario}
                onChange={(e) => setNovForm({ ...novForm, usuario: e.target.value })}
              >
                <option value="">Selecciona personal...</option>
                {personalGestionable.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.first_name || u.username} ({u.username})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Tipo de Evento Laboral</label>
              <select
                className={inputCls}
                value={novForm.tipo}
                onChange={(e) => setNovForm({ ...novForm, tipo: e.target.value })}
              >
                {TIPOS_NOVEDAD.map((t) => (
                  <option key={t.id} value={t.id}>{t.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Fecha Inicio</label>
              <input
                className={inputCls}
                type="date"
                required
                value={novForm.fecha_inicio}
                onChange={(e) => setNovForm({ ...novForm, fecha_inicio: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Horario Inicio</label>
              <input
                className={inputCls}
                type="time"
                required
                value={novForm.hora_inicio}
                onChange={(e) => setNovForm({ ...novForm, hora_inicio: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Fecha Término (opcional)</label>
              <input
                className={inputCls}
                type="date"
                value={novForm.fecha_fin}
                onChange={(e) => setNovForm({ ...novForm, fecha_fin: e.target.value })}
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-600">Horario Término (opcional)</label>
              <input
                className={inputCls}
                type="time"
                value={novForm.hora_fin}
                onChange={(e) => setNovForm({ ...novForm, hora_fin: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-600">Motivo / Observaciones</label>
              <input
                className={inputCls}
                placeholder="Ej: Licencia médica 5 días / Faltó turno mañana / Renuncia voluntaria"
                value={novForm.observaciones}
                onChange={(e) => setNovForm({ ...novForm, observaciones: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2 flex justify-end pt-1">
              <button disabled={busy} className={btnEmerald}>
                <CalendarClock className="w-4 h-4" /> Registrar con Fecha y Horario
              </button>
            </div>
          </form>
        </Panel>
      </div>

      <Panel
        title={`Cuentas Registradas (${filtrados.length})`}
        subtitle="Acceso exclusivo Admin Root · Estado de cuenta y situación laboral"
        icon={Users}
        action={<SearchBar value={busqueda} onChange={setBusqueda} placeholder="Buscar usuario o correo..." />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Nombre y Correo</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Situación Laboral</th>
                <th className="px-4 py-3">Acceso</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtrados.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3 font-mono font-semibold text-slate-900">{u.username}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-slate-800">{u.first_name || '—'}</div>
                    <div className="text-xs text-slate-500">{u.email || '—'}</div>
                    {u.veterinario_fecha_ingreso && (
                      <div className="text-[11px] font-mono text-slate-400">Ingreso: {u.veterinario_fecha_ingreso}</div>
                    )}
                    {whatsappUrl(u.veterinario_telefono, `Hola ${u.first_name || u.username}, coordinación Clínica PetCare.`) && (
                      <a
                        href={whatsappUrl(u.veterinario_telefono, `Hola ${u.first_name || u.username}, coordinación Clínica PetCare.`)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 hover:underline mt-0.5"
                      >
                        <MessageCircle className="w-3 h-3" /> {u.veterinario_telefono}
                      </a>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {u.is_superuser ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-violet-50 text-violet-700 border border-violet-200">
                        <ShieldCheck className="w-3 h-3" /> Administrador Root
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-sky-50 text-sky-700 border border-sky-200">
                        Equipo Clínico
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                        ESTADO_LABORAL_STYLE[u.estado_laboral] || ESTADO_LABORAL_STYLE.ACTIVO
                      }`}
                    >
                      {u.ultima_novedad?.tipo_display || u.estado_laboral || 'ACTIVO'}
                    </span>
                    {u.ultima_novedad && (
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">
                        {u.ultima_novedad.fecha_inicio} · {u.ultima_novedad.hora_inicio}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <EstadoBadge estado={u.is_active ? 'ACTIVO' : 'INACTIVO'} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    {u.is_superuser || u.id === currentUserId ? (
                      <span className="text-xs text-slate-400">Protegido</span>
                    ) : (
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => toggleActivo(u)}
                        className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 font-semibold cursor-pointer"
                      >
                        <Power className="w-3.5 h-3.5" /> {u.is_active ? 'Deshabilitar' : 'Habilitar'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel
        title={`Historial de Faltas, Licencias, Vacaciones y Egresos (${novedadesFiltradas.length})`}
        subtitle="Registro auditable con fecha, horario y usuario que autorizó"
        icon={Clock}
        action={
          <div className="flex flex-wrap gap-1.5">
            {[{ id: 'TODOS', label: 'Todos' }, ...TIPOS_NOVEDAD].map((t) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setFiltroNovedad(t.id)}
                className={`text-[11px] px-2.5 py-1 rounded-lg font-semibold border cursor-pointer ${
                  filtroNovedad === t.id
                    ? 'bg-slate-900 text-white border-slate-900'
                    : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
                }`}
              >
                {t.label.split(' / ')[0]}
              </button>
            ))}
          </div>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Colaborador</th>
                <th className="px-4 py-3">Evento</th>
                <th className="px-4 py-3">Fecha y Horario Inicio</th>
                <th className="px-4 py-3">Fecha y Horario Término</th>
                <th className="px-4 py-3">Observaciones</th>
                <th className="px-4 py-3 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {novedadesFiltradas.map((n) => (
                <tr key={n.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-900">{n.usuario_nombre || n.usuario_username}</div>
                    <div className="text-[11px] font-mono text-slate-500">{n.usuario_username}</div>
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                        ESTADO_LABORAL_STYLE[n.tipo] || ESTADO_LABORAL_STYLE.ACTIVO
                      }`}
                    >
                      {n.tipo_display}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-800 whitespace-nowrap">
                    {n.fecha_inicio} · {String(n.hora_inicio || '').slice(0, 5)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-600 whitespace-nowrap">
                    {n.fecha_fin ? `${n.fecha_fin}${n.hora_fin ? ` · ${String(n.hora_fin).slice(0, 5)}` : ''}` : 'Indefinido / Hasta reintegro'}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">{n.observaciones || '—'}</td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => eliminarNovedad(n.id)}
                      className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg border border-slate-200 hover:bg-rose-50 hover:text-rose-700 cursor-pointer"
                      title="Eliminar registro"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
              {novedadesFiltradas.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    Sin faltas, licencias, vacaciones o bajas registradas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
