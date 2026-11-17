import { useCallback, useEffect, useState } from 'react';
import { API_URL, apiRequest } from './api.js';
import Layout from './components/Layout.jsx';
import DashboardView from './components/DashboardView.jsx';
import PacientesView from './components/PacientesView.jsx';
import { AgendaView, FichasView, RecordatoriosView } from './components/AgendaFichasView.jsx';
import { CobrosView, FarmaciaView } from './components/FarmaciaCobrosView.jsx';
import { btnEmerald, inputCls } from './components/UiParts.jsx';

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
  const [aviso, setAviso] = useState(null);
  const [credenciales, setCredenciales] = useState({ username: '', password: '' });
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    apiRequest('/health/').then(setHealth).catch(() => setHealth({ status: 'offline' }));
  }, []);

  const cargarTodo = useCallback(async (activeToken) => {
    if (!activeToken) return;
    setCargando(true);
    try {
      const metricas = await apiRequest('/metricas/', { token: activeToken });
      let extra = {};
      try {
        const [tutores, mascotas, veterinarios, citas, fichas, recordatorios, lotes, servicios, cuentas] = await Promise.all([
          apiRequest('/tutores/', { token: activeToken }),
          apiRequest('/mascotas/', { token: activeToken }),
          apiRequest('/veterinarios/', { token: activeToken }),
          apiRequest('/citas/', { token: activeToken }),
          apiRequest('/fichas/', { token: activeToken }),
          apiRequest('/recordatorios/', { token: activeToken }),
          apiRequest('/medicamentos-fefo/', { token: activeToken }),
          apiRequest('/servicios/', { token: activeToken }),
          apiRequest('/cuentas/', { token: activeToken }),
        ]);
        extra = { tutores, mascotas, veterinarios, citas, fichas, recordatorios, lotes, servicios, cuentas };
      } catch (err) {
        if (err.status === 403) {
          setAviso({ tipo: 'warn', texto: 'Tu cuenta no tiene permisos administrativos para listar recursos CRUD en /api/.' });
        } else {
          throw err;
        }
      }
      setDatos({ metricas, ...extra });
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message });
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      cargarTodo(token);
    }
  }, [token, cargarTodo]);

  async function handleCreate(endpoint, body, successMsg) {
    setAviso(null);
    try {
      await apiRequest(endpoint, { method: 'POST', token, body });
      setAviso({ tipo: 'ok', texto: successMsg });
      await cargarTodo(token);
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message });
      throw err;
    }
  }

  async function handlePatch(endpoint, body, successMsg) {
    setAviso(null);
    try {
      await apiRequest(endpoint, { method: 'PATCH', token, body });
      setAviso({ tipo: 'ok', texto: successMsg });
      await cargarTodo(token);
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message });
    }
  }

  async function handleLogin(e) {
    e.preventDefault();
    setAviso(null);
    setCargando(true);
    try {
      const resp = await apiRequest('/auth/login/', { method: 'POST', body: credenciales });
      localStorage.setItem('petcare_token', resp.token);
      localStorage.setItem('petcare_user', JSON.stringify(resp.user));
      setToken(resp.token);
      setUser(resp.user);
      setCredenciales({ username: '', password: '' });
    } catch (err) {
      setAviso({ tipo: 'error', texto: err.message });
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
      setAviso(null);
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen bg-[#0b1120] flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl overflow-hidden border border-slate-200">
          <div className="bg-gradient-to-r from-[#0b1120] to-slate-800 px-7 py-6 text-white flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-600 text-slate-950 flex items-center justify-center text-xl font-extrabold shadow-lg">
                🐾
              </div>
              <div>
                <h1 className="text-lg font-bold">PetCare Cloud</h1>
                <p className="text-xs text-slate-300">Suite Clínica Veterinaria Modular</p>
              </div>
            </div>
            <span className={`text-[11px] px-2.5 py-1 rounded-full font-semibold ${health?.status === 'ok' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}`}>
              {health?.status === 'ok' ? '● En línea' : '● Offline'}
            </span>
          </div>

          <form onSubmit={handleLogin} className="p-7 space-y-4">
            <p className="text-xs text-slate-500">Conectado a <span className="font-mono">{API_URL}</span></p>
            {aviso && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm">
                {aviso.texto}
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Usuario</label>
              <input
                type="text"
                required
                value={credenciales.username}
                onChange={(e) => setCredenciales((c) => ({ ...c, username: e.target.value }))}
                className={inputCls}
                placeholder="admin"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Contraseña</label>
              <input
                type="password"
                required
                value={credenciales.password}
                onChange={(e) => setCredenciales((c) => ({ ...c, password: e.target.value }))}
                className={inputCls}
                placeholder="••••••••"
              />
            </div>
            <button type="submit" disabled={cargando} className={`${btnEmerald} w-full py-2.5`}>
              {cargando ? 'Ingresando...' : 'Iniciar sesión en PetCare'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <Layout
      modulo={modulo}
      setModulo={setModulo}
      user={user}
      health={health}
      onLogout={handleLogout}
      onRefresh={() => cargarTodo(token)}
    >
      {aviso && (
        <div
          className={`mb-5 px-4 py-3 rounded-2xl border text-sm font-medium flex items-center justify-between ${
            aviso.tipo === 'error'
              ? 'bg-rose-50 border-rose-200 text-rose-800'
              : aviso.tipo === 'warn'
                ? 'bg-amber-50 border-amber-200 text-amber-800'
                : 'bg-emerald-50 border-emerald-200 text-emerald-800'
          }`}
        >
          <span>{aviso.texto}</span>
          <button onClick={() => setAviso(null)} className="text-xs opacity-60 hover:opacity-100">✕</button>
        </div>
      )}

      {cargando && !datos.metricas ? (
        <div className="py-16 text-center text-slate-500 text-sm">Cargando módulos clínicos desde RDS...</div>
      ) : (
        <>
          {modulo === 'resumen' && (
            <DashboardView
              metricas={datos.metricas}
              citas={datos.citas}
              lotes={datos.lotes}
              fichas={datos.fichas}
              onNavigate={setModulo}
            />
          )}
          {modulo === 'pacientes' && (
            <PacientesView tutores={datos.tutores} mascotas={datos.mascotas} onCreate={handleCreate} onPatch={handlePatch} />
          )}
          {modulo === 'agenda' && (
            <AgendaView token={token} mascotas={datos.mascotas} veterinarios={datos.veterinarios} citas={datos.citas} onCreate={handleCreate} onPatch={handlePatch} />
          )}
          {modulo === 'fichas' && (
            <FichasView mascotas={datos.mascotas} veterinarios={datos.veterinarios} lotes={datos.lotes} fichas={datos.fichas} onCreate={handleCreate} />
          )}
          {modulo === 'recordatorios' && (
            <RecordatoriosView mascotas={datos.mascotas} recordatorios={datos.recordatorios} onCreate={handleCreate} onPatch={handlePatch} />
          )}
          {modulo === 'farmacia' && (
            <FarmaciaView lotes={datos.lotes} onCreate={handleCreate} onPatch={handlePatch} />
          )}
          {modulo === 'cobros' && (
            <CobrosView servicios={datos.servicios} cuentas={datos.cuentas} onCreate={handleCreate} />
          )}
        </>
      )}
    </Layout>
  );
}
