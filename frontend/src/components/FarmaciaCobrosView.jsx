import { Fragment, useEffect, useRef, useState } from 'react';
import {
  AlertTriangle,
  Barcode,
  Boxes,
  Camera,
  CheckSquare,
  CreditCard,
  DollarSign,
  ExternalLink,
  Minus,
  PackagePlus,
  Pill,
  Plus,
  Receipt,
  RefreshCw,
  ScanBarcode,
  Search,
  Tags,
  Trash2,
  X,
} from 'lucide-react';
import { BACKEND_ORIGIN, apiRequest, formatClp } from '../api.js';
import { EstadoBadge, Panel, SearchBar, btnEmerald, inputCls } from './UiParts.jsx';

export function FarmaciaView({ token, lotes = [], onCreate, onPatch }) {
  const [busqueda, setBusqueda] = useState('');
  const [filtroFefo, setFiltroFefo] = useState('TODOS');
  const [codigoScan, setCodigoScan] = useState('');
  const [resultadoScan, setResultadoScan] = useState(null);
  const [buscandoScan, setBuscandoScan] = useState(false);
  const [camaraActiva, setCamaraActiva] = useState(false);
  const [errorCamara, setErrorCamara] = useState('');
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const nombreInputRef = useRef(null);

  const [form, setForm] = useState({
    nombre: '',
    categoria: 'MEDICAMENTO',
    codigo_barras: '',
    codigo_lote: '',
    presentacion: 'Comprimidos / Frasco Ampolla',
    fecha_vencimiento: '',
    tiempo_limite_uso: 'Usar hasta fecha de vencimiento (Envase sellado)',
    stock_disponible: 10,
    precio_unitario: 2000,
  });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  async function buscarPorCodigo(codigoParam) {
    const query = (codigoParam ?? codigoScan).trim();
    if (!query) return;
    setBuscandoScan(true);
    try {
      const data = await apiRequest(`/medicamentos-fefo/buscar-codigo/?codigo=${encodeURIComponent(query)}`, { token });
      setResultadoScan(data);
    } catch {
      setResultadoScan({ encontrado: false, codigo_consultado: query, total_stock: 0, precio_unitario: null, lotes: [] });
    } finally {
      setBuscandoScan(false);
    }
  }

  function prellenarDesdeCodigo(codigo) {
    const coincidencia = lotes.find((l) => l.codigo_barras && l.codigo_barras.toLowerCase() === codigo.toLowerCase());
    setForm((prev) => ({
      ...prev,
      codigo_barras: codigo,
      ...(coincidencia
        ? {
            nombre: coincidencia.nombre,
            categoria: coincidencia.categoria,
            presentacion: coincidencia.presentacion,
            precio_unitario: coincidencia.precio_unitario || prev.precio_unitario,
            tiempo_limite_uso: coincidencia.tiempo_limite_uso || prev.tiempo_limite_uso,
          }
        : {}),
    }));
    nombreInputRef.current?.focus();
  }

  function detenerCamara() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setCamaraActiva(false);
  }

  async function iniciarCamara() {
    setErrorCamara('');
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setErrorCamara('La cámara web requiere conexión HTTPS segura (ahora estás en HTTP). Usa un lector USB/Bluetooth HID o escribe el código manualmente.');
      return;
    }
    if (!('BarcodeDetector' in window)) {
      setErrorCamara('Este navegador de escritorio no tiene detector de barras nativo; usa lector USB/Bluetooth HID o ingresa el código.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      streamRef.current = stream;
      setCamaraActiva(true);
      const detector = new window.BarcodeDetector({ formats: ['ean_13', 'ean_8', 'code_128', 'code_39', 'qr_code'] });

      const scanLoop = async () => {
        if (!streamRef.current || !videoRef.current) return;
        if (videoRef.current.readyState >= 2) {
          try {
            const codes = await detector.detect(videoRef.current);
            if (codes.length > 0 && codes[0].rawValue) {
              const detectado = codes[0].rawValue;
              setCodigoScan(detectado);
              detenerCamara();
              buscarPorCodigo(detectado);
              return;
            }
          } catch {
            // Keep scanning on frame errors.
          }
        }
        requestAnimationFrame(scanLoop);
      };
      requestAnimationFrame(scanLoop);
    } catch {
      setErrorCamara('No se pudo acceder a la cámara. Verifica permisos o usa lector USB / teclado.');
    }
  }

  useEffect(() => {
    if (camaraActiva && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current;
    }
  }, [camaraActiva]);

  async function submitLote(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate('/medicamentos-fefo/', {
        ...form,
        stock_disponible: Number(form.stock_disponible),
        precio_unitario: form.precio_unitario ? Number(form.precio_unitario) : null,
      }, 'Lote ingresado y ordenado por Norma FEFO.');
      setForm((f) => ({ ...f, nombre: '', codigo_barras: '', codigo_lote: '' }));
      if (resultadoScan?.codigo_consultado) {
        buscarPorCodigo(resultadoScan.codigo_consultado);
      }
    } finally {
      setBusy(false);
    }
  }

  const q = busqueda.trim().toLowerCase();
  const lotesStockCritico = lotes.filter((l) => l.stock_disponible <= 5 && l.estado_fefo !== 'BLOQUEADO_VENCIDO');
  const lotesPorVencer = lotes.filter((l) => l.estado_fefo === 'PRIORIDAD_FEFO_ALTA');
  const lotesVencidos = lotes.filter((l) => l.estado_fefo === 'BLOQUEADO_VENCIDO');
  const stockTotalBodega = lotes
    .filter((l) => l.estado_fefo !== 'BLOQUEADO_VENCIDO')
    .reduce((sum, l) => sum + Number(l.stock_disponible || 0), 0);

  const lotesFiltrados = lotes.filter((l) => {
    const matchTexto =
      !q ||
      l.nombre.toLowerCase().includes(q) ||
      l.codigo_lote.toLowerCase().includes(q) ||
      (l.codigo_barras || '').toLowerCase().includes(q);
    if (!matchTexto) return false;
    if (filtroFefo === 'CRITICO') return l.stock_disponible <= 5 && l.estado_fefo !== 'BLOQUEADO_VENCIDO';
    if (filtroFefo === 'ALERTAS') return l.estado_fefo !== 'FEFO_NORMAL';
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          type="button"
          onClick={() => setFiltroFefo(filtroFefo === 'CRITICO' ? 'TODOS' : 'CRITICO')}
          className={`text-left rounded-2xl p-4 border transition cursor-pointer ${
            filtroFefo === 'CRITICO' ? 'bg-amber-50 border-amber-400 shadow-sm' : 'bg-white border-slate-200 hover:border-amber-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-amber-800">
            <span>Stock Crítico (≤ 5 u.)</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-extrabold text-amber-700 mt-1">{lotesStockCritico.length} lote(s)</p>
        </button>
        <button
          type="button"
          onClick={() => setFiltroFefo(filtroFefo === 'ALERTAS' ? 'TODOS' : 'ALERTAS')}
          className={`text-left rounded-2xl p-4 border transition cursor-pointer ${
            filtroFefo === 'ALERTAS' ? 'bg-rose-50 border-rose-400 shadow-sm' : 'bg-white border-slate-200 hover:border-rose-300'
          }`}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-rose-800">
            <span>Por Vencer (≤ 30d FEFO)</span>
            <AlertTriangle className="w-4 h-4 text-rose-500" />
          </div>
          <p className="text-2xl font-extrabold text-rose-700 mt-1">{lotesPorVencer.length} lote(s)</p>
        </button>
        <div className="bg-white rounded-2xl p-4 border border-slate-200">
          <div className="text-xs font-semibold text-slate-500">Bloqueados por Vencimiento</div>
          <p className="text-2xl font-extrabold text-slate-900 mt-1">{lotesVencidos.length} lote(s)</p>
        </div>
      </div>
      <Panel
        title="Escáner de Código de Barras y Consulta Rápida"
        subtitle="Consulta stock total vigente, valor unitario y lote prioritario FEFO al instante"
        icon={ScanBarcode}
        action={
          <button
            type="button"
            onClick={camaraActiva ? detenerCamara : iniciarCamara}
            className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 cursor-pointer"
          >
            {camaraActiva ? <X className="w-3.5 h-3.5 text-rose-600" /> : <Camera className="w-3.5 h-3.5 text-emerald-600" />}
            {camaraActiva ? 'Cerrar Cámara' : 'Escanear con Cámara'}
          </button>
        }
      >
        <div className="p-5 space-y-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              buscarPorCodigo();
            }}
            className="flex flex-col sm:flex-row gap-2.5"
          >
            <div className="relative flex-1">
              <Barcode className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={codigoScan}
                onChange={(e) => setCodigoScan(e.target.value)}
                placeholder="Escanea con lector USB o escribe código de barras / lote / medicamento (ej: 7801000001028)"
                className={`${inputCls} pl-10 font-mono`}
              />
            </div>
            <button type="submit" disabled={buscandoScan} className={btnEmerald}>
              <Search className="w-4 h-4" /> {buscandoScan ? 'Buscando...' : 'Consultar Stock y Valor'}
            </button>
          </form>

          {errorCamara && (
            <div className="text-xs text-amber-800 bg-amber-50 border border-amber-200 px-3 py-2 rounded-xl">{errorCamara}</div>
          )}

          {camaraActiva && (
            <div className="bg-slate-950 rounded-2xl p-3 flex flex-col items-center gap-2">
              <video ref={videoRef} autoPlay playsInline muted className="w-full max-w-md rounded-xl max-h-60 object-cover" />
              <p className="text-xs text-slate-300">Apunta el código de barras frente a la cámara...</p>
            </div>
          )}

          {resultadoScan && (
            <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 space-y-3">
              {resultadoScan.encontrado ? (
                <>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div className="bg-white rounded-xl p-3.5 border border-slate-200">
                      <p className="text-[11px] font-semibold text-slate-500 uppercase">Medicamento</p>
                      <p className="text-sm font-bold text-slate-900 mt-1">{resultadoScan.lotes[0]?.nombre}</p>
                      <p className="text-[11px] font-mono text-slate-500 mt-0.5">
                        EAN: {resultadoScan.lotes[0]?.codigo_barras || resultadoScan.codigo_consultado}
                      </p>
                    </div>
                    <div className="bg-white rounded-xl p-3.5 border border-slate-200 flex items-center justify-between">
                      <div>
                        <p className="text-[11px] font-semibold text-slate-500 uppercase">Stock Disponible</p>
                        <p className="text-2xl font-extrabold text-emerald-700 mt-0.5">{resultadoScan.total_stock} u.</p>
                      </div>
                      <Boxes className="w-7 h-7 text-emerald-500" />
                    </div>
                    <div className="bg-white rounded-xl p-3.5 border border-slate-200 flex items-center justify-between">
                      <div>
                        <p className="text-[11px] font-semibold text-slate-500 uppercase">Valor Unitario</p>
                        <p className="text-2xl font-extrabold text-slate-900 mt-0.5">
                          {resultadoScan.precio_unitario ? formatClp(resultadoScan.precio_unitario) : 'Sin precio'}
                        </p>
                      </div>
                      <DollarSign className="w-7 h-7 text-sky-500" />
                    </div>
                  </div>
                  <div className="text-xs text-slate-600 flex flex-wrap items-center justify-between gap-2">
                    <span>
                      Lotes en orden FEFO: <strong className="text-slate-900">{resultadoScan.lotes.length}</strong> (próximo en salir:{' '}
                      <span className="font-mono font-semibold">{resultadoScan.lotes[0]?.codigo_lote}</span> · vence {resultadoScan.lotes[0]?.fecha_vencimiento})
                    </span>
                    <button
                      type="button"
                      onClick={() => prellenarDesdeCodigo(resultadoScan.lotes[0]?.codigo_barras || resultadoScan.codigo_consultado)}
                      className="text-xs font-semibold text-emerald-700 hover:underline cursor-pointer"
                    >
                      + Ingresar nuevo lote de este producto
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <p className="text-sm text-slate-700">
                    No existe un lote registrado con <span className="font-mono font-bold">{resultadoScan.codigo_consultado}</span>.
                  </p>
                  <button
                    type="button"
                    onClick={() => prellenarDesdeCodigo(resultadoScan.codigo_consultado)}
                    className={btnEmerald}
                  >
                    <Plus className="w-4 h-4" /> Usar código para crear lote nuevo
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </Panel>

      <Panel title="Ingresar Lote a Farmacia (Norma FEFO)" subtitle="Escanea código de barras y ordena automáticamente por vencimiento" icon={PackagePlus}>
        <form onSubmit={submitLote} className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-600">Código de Barras (EAN / SKU)</label>
            <input
              className={`${inputCls} font-mono`}
              placeholder="Ej: 7801000001028"
              value={form.codigo_barras}
              onChange={(e) => setForm({ ...form, codigo_barras: e.target.value })}
              onBlur={(e) => {
                if (e.target.value && !form.nombre) prellenarDesdeCodigo(e.target.value);
              }}
            />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Medicamento / Insumo</label>
            <input ref={nombreInputRef} className={inputCls} required placeholder="Meloxicam Inyectable 2%" value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} />
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
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Presentación</label>
            <input className={inputCls} value={form.presentacion} onChange={(e) => setForm({ ...form, presentacion: e.target.value })} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-semibold text-slate-600">Tiempo Límite de Uso (Abierto)</label>
            <input className={inputCls} value={form.tiempo_limite_uso} onChange={(e) => setForm({ ...form, tiempo_limite_uso: e.target.value })} />
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
        subtitle={`${lotesFiltrados.length} lote(s) · Existencia vigente en bodega: ${stockTotalBodega} unidades`}
        icon={Pill}
        action={<SearchBar value={busqueda} onChange={setBusqueda} placeholder="Buscar código barras, lote o fármaco..." />}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Lote / Barras</th>
                <th className="px-4 py-3">Producto</th>
                <th className="px-4 py-3">Vencimiento</th>
                <th className="px-4 py-3">Stock Guardado</th>
                <th className="px-4 py-3">Precio</th>
                <th className="px-4 py-3">Prioridad FEFO</th>
                <th className="px-4 py-3 text-right">Ajuste Rápido</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {lotesFiltrados.map((l) => (
                <tr key={l.id} className="hover:bg-slate-50/80">
                  <td className="px-4 py-3">
                    <div className="font-mono text-xs font-bold text-slate-800">{l.codigo_lote}</div>
                    {l.codigo_barras && <div className="font-mono text-[11px] text-slate-500">{l.codigo_barras}</div>}
                  </td>
                  <td className="px-4 py-3">
                    <div className="font-semibold text-slate-900">{l.nombre}</div>
                    <div className="text-[11px] text-slate-500">{l.presentacion}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700 whitespace-nowrap">{l.fecha_vencimiento}</td>
                  <td className="px-4 py-3 font-bold whitespace-nowrap">
                    <span className={l.stock_disponible <= 5 ? 'text-rose-600' : 'text-slate-900'}>
                      {l.stock_disponible} u.
                    </span>
                    {l.stock_disponible <= 5 && (
                      <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">Crítico</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-700 whitespace-nowrap">{l.precio_unitario ? formatClp(l.precio_unitario) : 'Pendiente'}</td>
                  <td className="px-4 py-3"><EstadoBadge estado={l.estado_fefo} /></td>
                  <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
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

export function CobrosView({ token, isAdmin = false, servicios = [], cuentas = [], fichas = [], onCreate, onNotify, onReload }) {
  const [servicioForm, setServicioForm] = useState({ nombre: '', precio: 15000 });
  const [fichaSeleccionada, setFichaSeleccionada] = useState('');
  const [seleccionServicios, setSeleccionServicios] = useState({});
  const [cuentaExpandida, setCuentaExpandida] = useState(null);
  const [webpayTx, setWebpayTx] = useState(null);
  const [busy, setBusy] = useState(false);

  const serviciosActivos = servicios.filter((s) => s.activo);

  function toggleServicio(id) {
    setSeleccionServicios((prev) => {
      const next = { ...prev };
      if (next[id]) {
        delete next[id];
      } else {
        next[id] = 1;
      }
      return next;
    });
  }

  function cambiarCantidad(id, cant) {
    const val = Math.max(1, Math.min(100, Number(cant) || 1));
    setSeleccionServicios((prev) => ({ ...prev, [id]: val }));
  }

  const totalServiciosSeleccionados = Object.entries(seleccionServicios).reduce((acc, [id, cant]) => {
    const srv = serviciosActivos.find((s) => String(s.id) === String(id));
    return acc + (srv ? srv.precio * cant : 0);
  }, 0);

  async function submitServicio(e) {
    e.preventDefault();
    setBusy(true);
    try {
      await onCreate('/servicios/', { nombre: servicioForm.nombre, precio: Number(servicioForm.precio), activo: true }, 'Servicio clínico agregado al catálogo.');
      setServicioForm({ nombre: '', precio: 15000 });
    } finally {
      setBusy(false);
    }
  }

  async function submitCobroMultiple(e) {
    e.preventDefault();
    const items = Object.entries(seleccionServicios).map(([id, cantidad]) => ({
      servicio_id: Number(id),
      cantidad,
    }));
    if (!fichaSeleccionada || items.length === 0) {
      onNotify?.('error', 'Selecciona una ficha clínica y al menos un servicio para cobrar.');
      return;
    }
    setBusy(true);
    try {
      const cuenta = await apiRequest('/cuentas/crear-desde-ficha/', {
        method: 'POST',
        token,
        body: { ficha_id: Number(fichaSeleccionada), items },
      });
      setSeleccionServicios({});
      setFichaSeleccionada('');
      setCuentaExpandida(cuenta.id);
      onNotify?.('ok', `Cuenta #${cuenta.id} actualizada con ${items.length} servicio(s). Total: ${formatClp(cuenta.total)}.`);
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    } finally {
      setBusy(false);
    }
  }

  async function quitarDetalle(cuentaId, detalleId) {
    try {
      await apiRequest(`/cuentas/${cuentaId}/quitar-detalle/${detalleId}/`, { method: 'DELETE', token });
      onNotify?.('ok', 'Servicio quitado de la cuenta.');
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    }
  }

  async function iniciarWebpayApi(cuentaId) {
    setBusy(true);
    try {
      const tx = await apiRequest(`/cuentas/${cuentaId}/iniciar-webpay/`, { method: 'POST', token });
      setWebpayTx({ ...tx, cuentaId });
      onNotify?.('ok', `Transacción Transbank Test iniciada (${tx.orden_compra}). Completa el pago en la pestaña Webpay y presiona Verificar.`);
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    } finally {
      setBusy(false);
    }
  }

  async function verificarWebpayApi(cuentaId) {
    setBusy(true);
    try {
      const cuenta = await apiRequest(`/cuentas/${cuentaId}/verificar-pago/`, { method: 'POST', token });
      onNotify?.(
        cuenta.pagada ? 'ok' : 'warn',
        cuenta.pagada ? `Cuenta #${cuentaId} pagada y confirmada por Transbank Test.` : `Cuenta #${cuentaId}: pago aún pendiente de confirmación.`
      );
      if (cuenta.pagada && webpayTx?.cuentaId === cuentaId) {
        setWebpayTx(null);
      }
      await onReload?.();
    } catch (err) {
      onNotify?.('error', err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {webpayTx && (
        <div className="bg-slate-900 text-white rounded-3xl p-6 shadow-xl border border-emerald-500/30 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-emerald-400">Pasarela Transbank Webpay Plus (Ambiente Test)</div>
            <h3 className="text-lg font-extrabold">Cuenta #{webpayTx.cuentaId} · {formatClp(webpayTx.monto)}</h3>
            <p className="text-xs text-slate-300 font-mono">
              Orden: {webpayTx.orden_compra} · Token: {String(webpayTx.token).slice(0, 18)}…
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            <form action={webpayTx.url} method="POST" target="_blank" rel="noreferrer">
              <input type="hidden" name="token_ws" value={webpayTx.token} />
              <button type="submit" className={btnEmerald}>
                <CreditCard className="w-4 h-4" /> Ir a Pagar en Webpay Test
              </button>
            </form>
            <button
              type="button"
              disabled={busy}
              onClick={() => verificarWebpayApi(webpayTx.cuentaId)}
              className="inline-flex items-center gap-1.5 text-xs px-4 py-2.5 rounded-xl bg-white text-slate-900 hover:bg-slate-100 font-bold cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" /> Verificar Pago
            </button>
            <button
              type="button"
              onClick={() => setWebpayTx(null)}
              className="p-2 rounded-xl hover:bg-white/10 text-slate-300 cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
      <Panel
        title="Armar Cuenta con Múltiples Servicios"
        subtitle="Marca todos los servicios prestados en la atención y súmalos en un solo cobro Webpay"
        icon={CheckSquare}
      >
        <form onSubmit={submitCobroMultiple} className="p-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <div>
              <label className="text-xs font-semibold text-slate-600">Ficha Clínica a Cobrar</label>
              <select className={inputCls} required value={fichaSeleccionada} onChange={(e) => setFichaSeleccionada(e.target.value)}>
                <option value="">Selecciona una ficha clínica...</option>
                {fichas.map((f) => (
                  <option key={f.id} value={f.id}>
                    Ficha #{f.id} · {f.mascota_nombre} — {f.diagnostico.slice(0, 40)}
                  </option>
                ))}
              </select>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-600">Subtotal servicios marcados:</span>
              <span className="text-lg font-extrabold text-emerald-700 font-mono">{formatClp(totalServiciosSeleccionados)}</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
            {serviciosActivos.map((s) => {
              const checked = Boolean(seleccionServicios[s.id]);
              return (
                <div
                  key={s.id}
                  className={`rounded-xl border p-3 flex items-center justify-between gap-2 transition ${
                    checked ? 'border-emerald-500 bg-emerald-50/50' : 'border-slate-200 bg-white'
                  }`}
                >
                  <label className="flex items-center gap-2.5 cursor-pointer min-w-0 flex-1">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleServicio(s.id)}
                      className="w-4 h-4 accent-emerald-600 rounded"
                    />
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-slate-900 truncate">{s.nombre}</div>
                      <div className="text-[11px] font-mono text-slate-500">{formatClp(s.precio)}</div>
                    </div>
                  </label>
                  {checked && (
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={seleccionServicios[s.id]}
                      onChange={(e) => cambiarCantidad(s.id, e.target.value)}
                      className="w-16 rounded-lg border border-emerald-300 px-2 py-1 text-xs font-mono text-center bg-white"
                    />
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex justify-end">
            <button disabled={busy || Object.keys(seleccionServicios).length === 0} className={btnEmerald}>
              <Plus className="w-4 h-4" /> Cobrar Servicios Seleccionados
            </button>
          </div>
        </form>
      </Panel>

      <div className={`grid grid-cols-1 ${isAdmin ? 'lg:grid-cols-2' : ''} gap-6`}>
        {isAdmin && (
          <Panel title="Agregar Nuevo Servicio al Catálogo" subtitle="Puedes crear todos los servicios clínicos distintos que necesites" icon={Tags}>
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
                  <Plus className="w-4 h-4" /> Guardar en Catálogo
                </button>
              </div>
            </form>
          </Panel>
        )}

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
              <p className="text-2xl font-extrabold text-slate-900 mt-1">{serviciosActivos.length}</p>
            </div>
            <div className="bg-slate-50 rounded-xl p-4 border border-slate-200/70">
              <p className="text-xs font-semibold text-slate-500">Cuentas emitidas</p>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">{cuentas.length}</p>
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Cuentas de Atención" subtitle="Haz clic en Detalle para revisar ítems acumulados y pagar con Webpay" icon={Receipt}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Cuenta</th>
                <th className="px-4 py-3">Paciente / Tutor</th>
                <th className="px-4 py-3">Ítems</th>
                <th className="px-4 py-3">Total CLP</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {cuentas.map((c) => (
                <Fragment key={c.id}>
                  <tr className="hover:bg-slate-50/80">
                    <td className="px-4 py-3 font-mono font-bold text-slate-800">#{c.id} <span className="text-xs text-slate-400 font-normal">(Ficha #{c.ficha})</span></td>
                    <td className="px-4 py-3">
                      <div className="font-semibold text-slate-900">{c.mascota_nombre || `Ficha #${c.ficha}`}</div>
                      {c.tutor_nombre && <div className="text-xs text-slate-500">{c.tutor_nombre}</div>}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600">{(c.detalles || []).length} línea(s)</td>
                    <td className="px-4 py-3 font-bold text-slate-900 font-mono">{formatClp(c.total)}</td>
                    <td className="px-4 py-3"><EstadoBadge estado={c.pagada ? 'PAGADA' : 'PENDIENTE'} /></td>
                    <td className="px-4 py-3 text-right space-x-1.5 whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => setCuentaExpandida(cuentaExpandida === c.id ? null : c.id)}
                        className="text-xs px-3 py-1 rounded-lg border border-slate-200 hover:bg-slate-100 font-semibold cursor-pointer"
                      >
                        {cuentaExpandida === c.id ? 'Ocultar' : 'Ver Detalle'}
                      </button>
                      {!c.pagada && !c.pagos?.some((p) => p.estado === 'INICIADO') && (
                        <button
                          type="button"
                          disabled={busy || !c.total}
                          onClick={() => iniciarWebpayApi(c.id)}
                          className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 font-semibold cursor-pointer"
                        >
                          <CreditCard className="w-3 h-3" /> Pagar Webpay
                        </button>
                      )}
                      {!c.pagada && c.pagos?.some((p) => p.estado === 'INICIADO') && (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => verificarWebpayApi(c.id)}
                          className="inline-flex items-center gap-1 text-xs px-3 py-1 rounded-lg bg-amber-500 text-slate-950 hover:bg-amber-400 font-semibold cursor-pointer"
                        >
                          <RefreshCw className="w-3 h-3" /> Verificar Webpay
                        </button>
                      )}
                    </td>
                  </tr>
                  {cuentaExpandida === c.id && (
                    <tr key={`det-${c.id}`} className="bg-slate-50/70">
                      <td colSpan={6} className="px-6 py-3">
                        <div className="space-y-1.5">
                          {(c.detalles || []).map((d) => (
                            <div key={d.id} className="flex items-center justify-between text-xs bg-white px-3 py-2 rounded-lg border border-slate-200">
                              <span>
                                <strong className="text-slate-800">{d.descripcion}</strong> × {d.cantidad} ({formatClp(d.precio_unitario)} c/u)
                              </span>
                              <span className="flex items-center gap-3">
                                <span className="font-mono font-bold text-slate-900">{formatClp(d.subtotal)}</span>
                                {c.editable && !d.medicamento && (
                                  <button onClick={() => quitarDetalle(c.id, d.id)} className="text-rose-600 hover:text-rose-800 cursor-pointer" title="Quitar servicio">
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
              {cuentas.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-slate-400">Sin cuentas generadas aún. Selecciona una ficha arriba para crear una.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}
