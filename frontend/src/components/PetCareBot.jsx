import { useState } from 'react';
import { Bot, Send, Sparkles, X } from 'lucide-react';

export default function PetCareBot({ isAdmin = false, metricas, citas = [], lotes = [], recordatorios = [], cuentas = [], novedades = [], onNavigate }) {
  const [abierto, setAbierto] = useState(false);
  const [entrada, setEntrada] = useState('');
  const [mensajes, setMensajes] = useState([
    {
      autor: 'bot',
      texto: '¡Hola! Soy PetCare Assistant (100% gratuito y local). Pregúntame sobre citas de hoy, stock crítico FEFO, vacunas o escáner.',
    },
  ]);

  const chips = [
    'Citas de hoy',
    'Stock crítico FEFO',
    'Vacunas pendientes',
    '¿Cómo escanear códigos?',
    ...(isAdmin ? ['Cuentas pendientes Webpay', 'Estado del personal'] : []),
  ];

  function responder(textoOriginal) {
    const q = textoOriginal.toLowerCase();
    const resumen = metricas?.resumen || {};
    const criticos = lotes.filter((l) => l.stock_disponible <= 5 && l.estado_fefo !== 'BLOQUEADO_VENCIDO');
    const porVencer = lotes.filter((l) => l.estado_fefo !== 'FEFO_NORMAL');
    const recPend = recordatorios.filter((r) => r.estado_asistencia !== 'ASISTIO');

    if (q.includes('cita') || q.includes('agenda')) {
      const prox = citas.slice(0, 3).map((c) => `${c.mascota_nombre} (${c.fecha} ${String(c.hora).slice(0, 5)})`).join(', ');
      return `Hoy hay ${resumen.citas_hoy ?? 0} cita(s) programadas. ${prox ? `Próximas: ${prox}.` : 'Sin citas cargadas.'}`;
    }
    if (q.includes('stock') || q.includes('farmacia') || q.includes('fefo') || q.includes('medicamento')) {
      const lista = criticos.slice(0, 3).map((l) => `${l.nombre} (${l.stock_disponible} u.)`).join(', ');
      return `Hay ${criticos.length} lote(s) con stock crítico (≤5 u.) y ${porVencer.length} alerta(s) de vencimiento FEFO.${lista ? ` Urgentes: ${lista}.` : ''}`;
    }
    if (q.includes('vacuna') || q.includes('control') || q.includes('recordatorio')) {
      return `Tienes ${recPend.length} citatorio(s) pendientes o inasistentes. Puedes enviar recordatorio directo por WhatsApp desde "Vacunas y Controles".`;
    }
    if (q.includes('escan') || q.includes('barra') || q.includes('código')) {
      return 'Ve a "Farmacia FEFO": usa tu lector USB o haz clic en "Escanear con Cámara" para consultar stock total, precio unitario y lote prioritario FEFO al instante.';
    }
    if ((q.includes('cobro') || q.includes('webpay') || q.includes('pago') || q.includes('cuenta'))) {
      if (!isAdmin) {
        return 'Los módulos financieros y Webpay están restringidos al perfil Administrador Root por seguridad.';
      }
      const pend = cuentas.filter((c) => !c.pagada);
      return `Hay ${pend.length} cuenta(s) pendientes de pago. Entra a "Servicios y Cobros" para agregar múltiples prestaciones e iniciar la simulación Webpay Transbank.`;
    }
    if (q.includes('personal') || q.includes('licencia') || q.includes('vacacion') || q.includes('falta')) {
      if (!isAdmin) {
        return 'La gestión de personal, licencias y cuentas está restringida al Administrador Root.';
      }
      return `Hay ${novedades.length} novedad(es) de personal registradas (faltas, licencias, vacaciones y bajas) con fecha y horario en "Usuarios y Personal".`;
    }
    return `Resumen clínico actual: ${resumen.mascotas_activas ?? 0} pacientes activos, ${resumen.citas_hoy ?? 0} citas hoy y ${criticos.length} producto(s) con stock crítico. Usa los botones rápidos de abajo para consultar.`;
  }

  function enviar(texto) {
    const limpio = texto.trim();
    if (!limpio) return;
    const respuesta = responder(limpio);
    setMensajes((prev) => [...prev, { autor: 'user', texto: limpio }, { autor: 'bot', texto: respuesta }]);
    setEntrada('');
  }

  return (
    <div className="fixed bottom-5 right-5 z-40">
      {abierto ? (
        <div className="w-80 sm:w-96 bg-white rounded-3xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col max-h-[75vh]">
          <div className="px-4 py-3.5 bg-slate-900 text-white flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-emerald-500/20 text-emerald-300 flex items-center justify-center">
                <Bot className="w-4 h-4" />
              </div>
              <div>
                <div className="text-xs font-bold flex items-center gap-1.5">
                  Asistente PetCare <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300">Gratis</span>
                </div>
                <div className="text-[10px] text-slate-400">Consultas clínicas en tiempo real</div>
              </div>
            </div>
            <button onClick={() => setAbierto(false)} className="p-1 rounded-lg hover:bg-white/10 cursor-pointer" aria-label="Cerrar asistente">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-3.5 space-y-2.5 bg-slate-50/70">
            {mensajes.map((m, idx) => (
              <div key={idx} className={`flex ${m.autor === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-xs leading-relaxed ${
                    m.autor === 'user'
                      ? 'bg-emerald-600 text-white rounded-br-xs'
                      : 'bg-white text-slate-800 border border-slate-200 rounded-bl-xs shadow-2xs'
                  }`}
                >
                  {m.texto}
                </div>
              </div>
            ))}
          </div>

          <div className="px-3 py-2 border-t border-slate-100 bg-white flex flex-wrap gap-1.5">
            {chips.map((chip) => (
              <button
                key={chip}
                type="button"
                onClick={() => enviar(chip)}
                className="text-[11px] px-2.5 py-1 rounded-full bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-700 font-medium cursor-pointer transition"
              >
                {chip}
              </button>
            ))}
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              enviar(entrada);
            }}
            className="p-2.5 border-t border-slate-200 bg-white flex items-center gap-2"
          >
            <input
              type="text"
              value={entrada}
              onChange={(e) => setEntrada(e.target.value)}
              placeholder="Escribe tu consulta..."
              className="flex-1 text-xs rounded-xl border border-slate-200 px-3 py-2 focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              className="p-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer"
              aria-label="Enviar consulta"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
          {onNavigate && (
            <div className="px-3 pb-2 bg-white text-[10px] text-slate-400 flex justify-between">
              <button type="button" onClick={() => onNavigate('farmacia')} className="hover:text-emerald-600 cursor-pointer">
                Ir a Farmacia
              </button>
              <button type="button" onClick={() => onNavigate('agenda')} className="hover:text-emerald-600 cursor-pointer">
                Ir a Agenda
              </button>
            </div>
          )}
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setAbierto(true)}
          className="inline-flex items-center gap-2 px-4 py-3 rounded-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-xl shadow-slate-900/30 border border-white/10 cursor-pointer transition"
        >
          <Sparkles className="w-4 h-4 text-emerald-400" />
          Asistente Clínico
        </button>
      )}
    </div>
  );
}
