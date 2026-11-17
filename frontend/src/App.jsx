import { useEffect, useState } from 'react';
import { API_URL, S3_STATIC_URL, apiRequest } from './api.js';

const MODULOS = [
  { id: 'resumen', label: 'Dashboard' },
  { id: 'pacientes', label: 'Pacientes' },
  { id: 'agenda', label: 'Agenda' },
  { id: 'farmacia', label: 'Farmacia FEFO' },
  { id: 'cobros', label: 'Cobros' },
];

export default function App() {
  const [token, setToken] = useState(() => localStorage.getItem('petcare_token') || '');
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('petcare_user') || 'null');
    } catch {
      return null;
    }
  });
  const [health, setHealth] = useState(null);
  const [modulo, setModulo] = useState('resumen');
  const [datos, setDatos] = useState({});
  const [error, setError] = useState('');
  const [credenciales, setCredenciales] = useState({ username: '', password: '' });
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    apiRequest('/health/').then(setHealth).catch(() => setHealth({ status: 'offline' }));
  }, []);

  useEffect(() => {
    if (!token) return;
    cargarModulo(modulo, token);
  }, [token, modulo]);

  async function cargarModulo(tab, activeToken) {
    setCargando(true);
    setError('');
    try {
      if (tab === 'resumen') {
        const metricas = await apiRequest('/metricas/', { token: activeToken });
        setDatos((prev) => ({ ...prev, metricas }));
      } else if (tab === 'pacientes') {
        const [tutores, mascotas] = await Promise.all([
          apiRequest('/tutores/', { token: activeToken }),
          apiRequest('/mascotas/', { token: activeToken }),
        ]);
        setDatos((prev) => ({ ...prev, tutores, mascotas }));
      } else if (tab === 'agenda') {
        const [citas, veterinarios] = await Promise.all([
          apiRequest('/citas/', { token: activeToken }),
          apiRequest('/veterinarios/', { token: activeToken }),
        ]);
        setDatos((prev) => ({ ...prev, citas, veterinarios }));
      } else if (tab === 'farmacia') {
        const lotes = await apiRequest('/medicamentos-fefo/', { token: activeToken });
        setDatos((prev) => ({ ...prev, lotes }));
      } else if (tab === 'cobros') {
        const [cuentas, servicios] = await Promise.all([
          apiRequest('/cuentas/', { token: activeToken }),
          apiRequest('/servicios/', { token: activeToken }),
        ]);
        setDatos((prev) => ({ ...prev, cuentas, servicios }));
      }
    } catch (err) {
      setError(
        err.status === 403
          ? 'Tu cuenta no tiene permisos de administrador para consultar los recursos CRUD en /api/.'
          : err.message
      );
    } finally {
      setCargando(false);
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setError('');
    setCargando(true);
    try {
      const resp = await apiRequest('/auth/login/', { method: 'POST', body: credenciales });
      localStorage.setItem('petcare_token', resp.token);
      localStorage.setItem('petcare_user', JSON.stringify(resp.user));
      setToken(resp.token);
      setUser(resp.user);
      setCredenciales({ username: '', password: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setCargando(false);
    }
  }

  async function handleLogout() {
    try {
      if (token) await apiRequest('/auth/logout/', { method: 'POST', token });
    } finally {
      localStorage.removeItem('petcare_token');
      localStorage.removeItem('petcare_user');
      setToken('');
      setUser(null);
      setDatos({});
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-900 text-white px-6 py-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {S3_STATIC_URL && (
            <img
              src={`${S3_STATIC_URL}/logo-petcare.png`}
              alt="PetCare"
              className="h-9 w-9 rounded-lg object-cover bg-emerald-500/20"
            />
          )}
          <div>
            <h1 className="text-lg font-bold tracking-tight">PetCare Cloud · Frontend Modular</h1>
            <p className="text-xs text-slate-400">API Gateway / Backend: {API_URL}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${health?.status === 'ok' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
            Backend: {health?.status === 'ok' ? 'Conectado' : 'Sin conexión'}
          </span>
          {user && (
            <button
              onClick={handleLogout}
              className="text-xs bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-700"
            >
              Cerrar sesión ({user.username})
            </button>
          )}
        </div>
      </header>

      <main className="max-w-6xl mx-auto p-6">
        {!token ? (
          <form onSubmit={handleLogin} className="max-w-md mx-auto mt-10 bg-white p-6 rounded-2xl shadow-sm border border-slate-200 space-y-4">
            <h2 className="text-xl font-bold text-slate-800">Iniciar sesión vía API</h2>
            <p className="text-sm text-slate-500">Autenticación por Token DRF entre EC2 Frontend y EC2 Backend.</p>
            {error && <div className="p-3 rounded-lg bg-rose-50 text-rose-700 text-sm">{error}</div>}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Usuario</label>
              <input
                type="text"
                required
                value={credenciales.username}
                onChange={(e) => setCredenciales((c) => ({ ...c, username: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                placeholder="admin"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Contraseña</label>
              <input
                type="password"
                required
                value={credenciales.password}
                onChange={(e) => setCredenciales((c) => ({ ...c, password: e.target.value }))}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <button
              type="submit"
              disabled={cargando}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-lg text-sm"
            >
              {cargando ? 'Ingresando...' : 'Entrar al sistema'}
            </button>
          </form>
        ) : (
          <div className="space-y-6">
            <nav className="flex flex-wrap gap-2">
              {MODULOS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setModulo(m.id)}
                  className={`px-4 py-2 rounded-xl text-sm font-semibold transition ${
                    modulo === m.id
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'bg-white text-slate-700 border border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </nav>

            {error && <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-sm">{error}</div>}
            {cargando && <p className="text-sm text-slate-500">Consultando módulo {modulo}...</p>}

            {modulo === 'resumen' && datos.metricas && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card label="Tutores activos" value={datos.metricas.resumen.tutores_activos} />
                <Card label="Mascotas activas" value={datos.metricas.resumen.mascotas_activas} />
                <Card label="Citas hoy" value={datos.metricas.resumen.citas_hoy} />
                <Card label="Alertas FEFO (<=45d)" value={datos.metricas.resumen.lotes_por_vencer} />
              </div>
            )}

            {modulo === 'pacientes' && (
              <DataTable
                title="Mascotas registradas"
                rows={datos.mascotas || []}
                cols={[
                  ['nombre', 'Paciente'],
                  ['especie', 'Especie'],
                  ['raza', 'Raza'],
                  ['tutor_nombre', 'Tutor'],
                ]}
              />
            )}

            {modulo === 'agenda' && (
              <DataTable
                title="Citas médicas"
                rows={datos.citas || []}
                cols={[
                  ['fecha', 'Fecha'],
                  ['hora', 'Hora'],
                  ['mascota_nombre', 'Paciente'],
                  ['veterinario_nombre', 'Veterinario'],
                  ['estado', 'Estado'],
                ]}
              />
            )}

            {modulo === 'farmacia' && (
              <DataTable
                title="Inventario FEFO"
                rows={datos.lotes || []}
                cols={[
                  ['codigo_lote', 'Lote'],
                  ['nombre', 'Medicamento / Insumo'],
                  ['fecha_vencimiento', 'Vencimiento'],
                  ['stock_disponible', 'Stock'],
                  ['estado_fefo', 'Estado FEFO'],
                ]}
              />
            )}

            {modulo === 'cobros' && (
              <DataTable
                title="Cuentas de atención"
                rows={datos.cuentas || []}
                cols={[
                  ['id', 'Cuenta #'],
                  ['ficha', 'Ficha #'],
                  ['total', 'Total CLP'],
                  ['pagada', 'Pagada'],
                ]}
              />
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function Card({ label, value }) {
  return (
    <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
      <p className="text-xs font-medium text-slate-500 uppercase">{label}</p>
      <p className="text-3xl font-bold text-slate-900 mt-2">{value}</p>
    </div>
  );
}

function DataTable({ title, rows, cols }) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-200">
        <h3 className="font-bold text-slate-800">{title}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              {cols.map(([key, header]) => (
                <th key={key} className="px-4 py-3 font-semibold">{header}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {rows.length === 0 ? (
              <tr>
                <td colSpan={cols.length} className="px-4 py-6 text-center text-slate-400">
                  Sin registros disponibles.
                </td>
              </tr>
            ) : (
              rows.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50">
                  {cols.map(([key]) => (
                    <td key={key} className="px-4 py-3 text-slate-700">
                      {typeof row[key] === 'boolean' ? (row[key] ? 'Sí' : 'No') : String(row[key] ?? '—')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
