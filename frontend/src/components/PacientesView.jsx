import { useRef, useState } from 'react';
import {
  Camera,
  Cpu,
  FolderOpen,
  Mail,
  MapPin,
  MessageCircle,
  PawPrint,
  Phone,
  Plus,
  Power,
  Printer,
  Search,
  Upload,
  UserPlus,
  Users,
  X,
} from 'lucide-react';
import { apiRequest, apiUploadFile, resolveMediaUrl, validarEmail, validarRutChileno, whatsappUrl } from '../api.js';
import { EstadoBadge, Panel, SearchBar, btnEmerald, inputCls } from './UiParts.jsx';

export default function PacientesView({
  token = '',
  tutores = [],
  mascotas = [],
  citas = [],
  fichas = [],
  recordatorios = [],
  onCreate,
  onPatch,
  onNotify,
  onReload,
}) {
  const [busqueda, setBusqueda] = useState('');
  const [rutError, setRutError] = useState('');
  const [emailError, setEmailError] = useState('');
  const [expedienteMascota, setExpedienteMascota] = useState(null);
  const [lectorChipActivo, setLectorChipActivo] = useState(false);
  const [chipScan, setChipScan] = useState('');
  const [resultadoChip, setResultadoChip] = useState(null);
  const [fotoArchivoForm, setFotoArchivoForm] = useState(null);
  const [fotoPreviewForm, setFotoPreviewForm] = useState('');
  const [fotoArchivoExp, setFotoArchivoExp] = useState(null);
  const formNombreRef = useRef(null);
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
    microchip: '',
  });
  const [busy, setBusy] = useState(false);

  async function buscarChipRfid(e) {
    if (e) e.preventDefault();
    const codigo = chipScan.trim();
    if (!codigo) return;
    try {
      const res = await apiRequest(`/mascotas/buscar-chip/?chip=${encodeURIComponent(codigo)}`, { token });
      setResultadoChip(res);
    } catch {
      setResultadoChip({ encontrado: false, chip_consultado: codigo, mascota: null });
    }
  }

  async function submitTutor(e) {
    e.preventDefault();
    const err = validarRutChileno(tutorForm.rut);
    const eErr = validarEmail(tutorForm.email);
    if (err || eErr) {
      setRutError(err);
      setEmailError(eErr);
      return;
    }
    setRutError('');
    setEmailError('');
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
      const creada = await onCreate(
        '/mascotas/',
        { ...mascotaForm, tutor: Number(mascotaForm.tutor) },
        'Mascota registrada correctamente.'
      );
      if (fotoArchivoForm && creada?.id) {
        await apiUploadFile(`/mascotas/${creada.id}/subir-foto/`, { token, file: fotoArchivoForm });
        onNotify?.('ok', `Paciente ${creada.nombre} y fotografía cargados correctamente.`);
        await onReload?.();
      }
      setMascotaForm((m) => ({ ...m, nombre: '', raza: '', alergias_conocidas: '', microchip: '' }));
      setFotoArchivoForm(null);
      if (fotoPreviewForm) URL.revokeObjectURL(fotoPreviewForm);
      setFotoPreviewForm('');
    } catch (err) {
      onNotify?.('error', err.message);
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

  const mascotaExp = expedienteMascota
    ? (mascotas.find((m) => m.id === expedienteMascota.id) || expedienteMascota)
    : null;
  const citasExp = mascotaExp ? citas.filter((c) => c.mascota === mascotaExp.id) : [];
  const fichasExp = mascotaExp ? fichas.filter((f) => f.mascota === mascotaExp.id) : [];
  const recExp = mascotaExp ? recordatorios.filter((r) => r.mascota === mascotaExp.id) : [];
  const tutorExp = mascotaExp ? tutores.find((t) => t.id === mascotaExp.tutor) : null;
  const waExp = tutorExp
    ? whatsappUrl(tutorExp.telefono, `Hola ${tutorExp.nombre_completo}, te escribimos de Clínica PetCare por el expediente de ${mascotaExp?.nombre}.`)
    : '';

  async function guardarFotoExpediente(e) {
    e.preventDefault();
    if (!mascotaExp || !fotoArchivoExp) {
      onNotify?.('error', 'Selecciona una imagen desde tu dispositivo o teléfono.');
      return;
    }
    setBusy(true);
    try {
      await apiUploadFile(`/mascotas/${mascotaExp.id}/subir-foto/`, { token, file: fotoArchivoExp });
      onNotify?.('ok', `Foto de ${mascotaExp.nombre} subida correctamente al expediente.`);
      setFotoArchivoExp(null);
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-wrap items-center justify-between gap-3 shadow-2xs">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Lector Rápido de Microchip RFID (Opción Pistola 134.2 kHz USB/Bluetooth)</h3>
            <p className="text-xs text-slate-500">Escanea el chip ISO (15 dígitos) para abrir el expediente o pre-llenar un nuevo ingreso.</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setLectorChipActivo((v) => !v)}
          className={`inline-flex items-center gap-1.5 text-xs font-semibold px-3.5 py-2 rounded-xl border transition cursor-pointer ${
            lectorChipActivo ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" /> {lectorChipActivo ? 'Ocultar Lector Chip' : 'Activar Lector Chip'}
        </button>
      </div>

      {lectorChipActivo && (
        <Panel title="Lectura RFID de Microchip Animal" subtitle="Acerca el lector RFID USB/Bluetooth con el cursor en la casilla" icon={Cpu}>
          <div className="p-5 space-y-3">
            <form onSubmit={buscarChipRfid} className="flex flex-col sm:flex-row gap-2.5">
              <input
                type="text"
                autoFocus
                className={`${inputCls} font-mono flex-1`}
                placeholder="Escanea o escribe el código RFID de 15 dígitos (ej: 900012345678901)"
                value={chipScan}
                onChange={(e) => setChipScan(e.target.value)}
              />
              <button type="submit" className={btnEmerald}>
                <Search className="w-4 h-4" /> Buscar Microchip
              </button>
            </form>
            {resultadoChip && (
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 flex flex-wrap items-center justify-between gap-3">
                {resultadoChip.encontrado && resultadoChip.mascota ? (
                  <>
                    <div>
                      <p className="text-xs font-bold uppercase text-emerald-700">Microchip Registrado</p>
                      <p className="text-sm font-bold text-slate-900">
                        {resultadoChip.mascota.nombre} · {resultadoChip.mascota.especie} ({resultadoChip.mascota.raza})
                      </p>
                      <p className="text-xs text-slate-500">Tutor: {resultadoChip.mascota.tutor_nombre}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setExpedienteMascota(resultadoChip.mascota)}
                      className={btnEmerald}
                    >
                      <FolderOpen className="w-4 h-4" /> Abrir Expediente
                    </button>
                  </>
                ) : (
                  <>
                    <p className="text-sm text-slate-700">
                      El chip <span className="font-mono font-bold">{resultadoChip.chip_consultado}</span> aún no pertenece a un paciente.
                    </p>
                    <button
                      type="button"
                      onClick={() => {
                        setMascotaForm((f) => ({ ...f, microchip: resultadoChip.chip_consultado }));
                        formNombreRef.current?.focus();
                      }}
                      className={btnEmerald}
                    >
                      <Plus className="w-4 h-4" /> Usar para Registro Rápido
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </Panel>
      )}
      {mascotaExp && (
        <div className="fixed inset-0 z-50 bg-slate-950/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200">
            <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-4 bg-slate-900 text-white rounded-t-3xl">
              <div className="flex items-center gap-3.5 min-w-0">
                {mascotaExp.foto_url ? (
                  <img
                    src={resolveMediaUrl(mascotaExp.foto_url)}
                    alt={mascotaExp.nombre}
                    className="w-14 h-14 rounded-2xl object-cover border border-white/20 shrink-0 bg-slate-800"
                  />
                ) : (
                  <div className="w-14 h-14 rounded-2xl bg-white/10 text-emerald-300 flex items-center justify-center shrink-0">
                    <PawPrint className="w-6 h-6" />
                  </div>
                )}
                <div className="min-w-0">
                  <h3 className="font-bold text-base truncate">Expediente Clínico · {mascotaExp.nombre}</h3>
                  <p className="text-xs text-slate-300 truncate">
                    {mascotaExp.especie} · {mascotaExp.raza} · Peso: {mascotaExp.peso_kg} kg · Tutor: {mascotaExp.tutor_nombre}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {waExp && (
                  <a
                    href={waExp}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-[#25D366] text-slate-950 hover:opacity-90 font-bold"
                  >
                    <MessageCircle className="w-3.5 h-3.5" /> WhatsApp Tutor
                  </a>
                )}
                <button onClick={() => window.print()} className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 font-semibold cursor-pointer">
                  <Printer className="w-3.5 h-3.5" /> Imprimir
                </button>
                <button onClick={() => setExpedienteMascota(null)} className="p-1.5 rounded-lg hover:bg-white/10 cursor-pointer">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-5 text-sm">
              <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                {mascotaExp.foto_url ? (
                  <a href={resolveMediaUrl(mascotaExp.foto_url)} target="_blank" rel="noreferrer" className="shrink-0">
                    <img
                      src={resolveMediaUrl(mascotaExp.foto_url)}
                      alt={mascotaExp.nombre}
                      className="w-24 h-24 rounded-2xl object-cover border border-slate-200 shadow-xs bg-white"
                    />
                  </a>
                ) : (
                  <div className="w-24 h-24 rounded-2xl border border-dashed border-slate-300 bg-white text-slate-400 flex flex-col items-center justify-center gap-1 shrink-0">
                    <Camera className="w-5 h-5" />
                    <span className="text-[10px] font-medium">Sin foto aún</span>
                  </div>
                )}
                <form onSubmit={guardarFotoExpediente} className="flex-1 w-full space-y-2">
                  <label className="text-xs font-bold text-slate-700 block">
                    Subir Fotografía Directa de {mascotaExp.nombre} (Cámara / WhatsApp / Galería)
                  </label>
                  <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
                    <input
                      type="file"
                      accept="image/*"
                      className="block w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-900 file:text-white hover:file:bg-slate-800 cursor-pointer"
                      onChange={(e) => setFotoArchivoExp(e.target.files?.[0] || null)}
                    />
                    <button type="submit" disabled={busy || !fotoArchivoExp} className={`${btnEmerald} whitespace-nowrap`}>
                      <Upload className="w-4 h-4" /> Subir Foto
                    </button>
                  </div>
                </form>
              </div>
              {mascotaExp.alergias_conocidas && (
                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs">
                  <strong>Alergias / Observaciones:</strong> {mascotaExp.alergias_conocidas}
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
              <input
                className={`${inputCls} ${emailError ? 'border-rose-400' : ''}`}
                type="email"
                required
                placeholder="tutor@correo.cl"
                value={tutorForm.email}
                onChange={(e) => {
                  setTutorForm({ ...tutorForm, email: e.target.value });
                  if (emailError) setEmailError(validarEmail(e.target.value));
                }}
                onBlur={(e) => setEmailError(e.target.value ? validarEmail(e.target.value) : '')}
              />
              {emailError && <p className="text-[11px] text-rose-600 mt-1">{emailError}</p>}
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
              <input ref={formNombreRef} className={inputCls} required placeholder="Thor" value={mascotaForm.nombre} onChange={(e) => setMascotaForm({ ...mascotaForm, nombre: e.target.value })} />
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
            <div>
              <label className="text-xs font-semibold text-slate-600">Microchip RFID (opcional)</label>
              <input
                className={`${inputCls} font-mono`}
                placeholder="Ej: 900012345678901"
                value={mascotaForm.microchip}
                onChange={(e) => setMascotaForm({ ...mascotaForm, microchip: e.target.value })}
              />
            </div>
            <div className="sm:col-span-2">
              <label className="text-xs font-semibold text-slate-600 block mb-1">
                Subir Fotografía Directa (desde móvil, cámara o imágenes de WhatsApp)
              </label>
              <div className="flex items-center gap-3">
                {fotoPreviewForm && (
                  <img src={fotoPreviewForm} alt="Vista previa" className="w-11 h-11 rounded-xl object-cover border border-slate-200 shrink-0" />
                )}
                <input
                  type="file"
                  accept="image/*"
                  className="block w-full text-xs text-slate-600 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-900 file:text-white hover:file:bg-slate-800 cursor-pointer"
                  onChange={(e) => {
                    const file = e.target.files?.[0] || null;
                    setFotoArchivoForm(file);
                    if (fotoPreviewForm) URL.revokeObjectURL(fotoPreviewForm);
                    setFotoPreviewForm(file ? URL.createObjectURL(file) : '');
                  }}
                />
              </div>
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
                        <img src={resolveMediaUrl(m.foto_url)} alt={m.nombre} className="w-8 h-8 rounded-lg object-cover border border-slate-200" />
                      ) : (
                        <div className="w-8 h-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center">
                          <PawPrint className="w-4 h-4" />
                        </div>
                      )}
                      <div>
                        <span>{m.nombre}</span>
                        {m.microchip && <div className="text-[10px] font-mono text-slate-400">Chip: {m.microchip}</div>}
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{m.especie} · {m.raza}</td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700">{m.peso_kg} kg</td>
                  <td className="px-4 py-3 text-slate-700">{m.tutor_nombre}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={m.activo ? 'ACTIVO' : 'INACTIVO'} /></td>
                  <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                    <button
                      onClick={() => {
                        setExpedienteMascota(m);
                        setFotoArchivoExp(null);
                      }}
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
                  <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                    {whatsappUrl(t.telefono, `Hola ${t.nombre_completo}, te contactamos desde Clínica Veterinaria PetCare.`) && (
                      <a
                        href={whatsappUrl(t.telefono, `Hola ${t.nombre_completo}, te contactamos desde Clínica Veterinaria PetCare.`)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs px-3 py-1.5 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 font-semibold"
                      >
                        <MessageCircle className="w-3.5 h-3.5" /> WhatsApp
                      </a>
                    )}
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
