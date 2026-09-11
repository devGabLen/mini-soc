import React, { useState, useEffect, useCallback } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const API_BASE = "http://localhost:8080";
const SUPABASE_URL = "https://relglfpyctcldlbgsjdn.supabase.co";
const SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJlbGdsZnB5Y3RjbGRsYmdzamRuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODgzOTc1MzUsImV4cCI6MjEwMzk3MzUzNX0.gQAbakE_h-Lkq-te5eFF5mgie1_ie3NatBiGUn14fu0";

const SEVERITY_COLOR = {
  1: "#4C7A92",
  2: "#C9A227",
  3: "#D0702A",
  4: "#C4432C",
};

const CATEGORY_LABEL = {
  reconocimiento: "Reconocimiento",
  entrega_ataque: "Entrega / Ataque",
  explotacion: "Explotación",
  compromiso_sistema: "Compromiso de sistema",
  conciencia_ambiental: "Conciencia ambiental",
};

const STATUS_LABEL = {
  open: "Abierto",
  in_progress: "En progreso",
  contained: "Contenido",
  closed: "Cerrado",
  false_positive: "Falso positivo",
};

function fmtDuration(seconds) {
  if (seconds === null || seconds === undefined) return "—";
  const s = Math.round(Number(seconds));
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  const rem = s % 60;
  if (m < 60) return `${m}m ${rem}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString("es", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

const styles = {
  page: {
    minHeight: "100vh",
    background: "#0B0E14",
    color: "#E6E9EF",
    fontFamily:
      "ui-sans-serif, -apple-system, 'Segoe UI', Roboto, sans-serif",
    padding: "0",
  },
  mono: {
    fontFamily:
      "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 24px",
    borderBottom: "1px solid #232838",
    background: "#0D1017",
  },
  brand: {
    fontSize: "15px",
    fontWeight: 700,
    letterSpacing: "0.3px",
    color: "#E6E9EF",
  },
  brandSub: {
    fontSize: "11px",
    color: "#5B6373",
    marginTop: "2px",
  },
  panel: {
    background: "#12161F",
    border: "1px solid #232838",
    borderRadius: "3px",
  },
  panelTitle: {
    fontSize: "12px",
    fontWeight: 600,
    color: "#8B93A7",
    padding: "10px 14px",
    borderBottom: "1px solid #232838",
  },
  input: {
    background: "#0D1017",
    border: "1px solid #2C3244",
    borderRadius: "3px",
    color: "#E6E9EF",
    padding: "8px 10px",
    fontSize: "13px",
    outline: "none",
    width: "100%",
    boxSizing: "border-box",
  },
  button: {
    background: "#1E5A8A",
    color: "#fff",
    border: "none",
    borderRadius: "3px",
    padding: "8px 14px",
    fontSize: "13px",
    fontWeight: 600,
    cursor: "pointer",
  },
  buttonGhost: {
    background: "transparent",
    color: "#8B93A7",
    border: "1px solid #2C3244",
    borderRadius: "3px",
    padding: "7px 12px",
    fontSize: "12px",
    cursor: "pointer",
  },
  th: {
    textAlign: "left",
    fontSize: "11px",
    color: "#5B6373",
    fontWeight: 600,
    padding: "8px 14px",
    borderBottom: "1px solid #232838",
  },
  td: {
    padding: "9px 14px",
    fontSize: "13px",
    borderBottom: "1px solid #1A1E29",
    color: "#C4CAD6",
  },
  badge: (color) => ({
    display: "inline-block",
    width: "10px",
    height: "10px",
    borderRadius: "2px",
    background: color,
    marginRight: "7px",
    verticalAlign: "middle",
  }),
  statBlock: {
    flex: "1",
    borderRight: "1px solid #232838",
    padding: "14px 20px",
  },
  statLabel: {
    fontSize: "11px",
    color: "#5B6373",
    marginBottom: "6px",
  },
  statValue: {
    fontSize: "22px",
    fontWeight: 700,
    color: "#E6E9EF",
  },
  errorBox: {
    background: "#2A1414",
    border: "1px solid #5A2A2A",
    color: "#E8A0A0",
    padding: "8px 12px",
    borderRadius: "3px",
    fontSize: "12px",
    marginTop: "8px",
  },
};

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch(
        `${SUPABASE_URL}/auth/v1/token?grant_type=password`,
        {
          method: "POST",
          headers: {
            apikey: SUPABASE_ANON_KEY,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        }
      );
      const data = await res.json();
      if (!res.ok || !data.access_token) {
        throw new Error(
          data.error_description || data.msg || "No se pudo iniciar sesión."
        );
      }
      onLogin(data.access_token);
    } catch (err) {
      setError(err.message || "Error de conexión.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        ...styles.page,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{ ...styles.panel, width: "320px", padding: "28px" }}
      >
        <div style={{ marginBottom: "20px" }}>
          <div style={styles.brand}>mini-soc</div>
          <div style={styles.brandSub}>Panel de operaciones</div>
        </div>
        <div style={{ marginBottom: "12px" }}>
          <div style={{ ...styles.statLabel, marginBottom: "5px" }}>
            Correo
          </div>
          <input
            style={styles.input}
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div style={{ marginBottom: "18px" }}>
          <div style={{ ...styles.statLabel, marginBottom: "5px" }}>
            Contraseña
          </div>
          <input
            style={styles.input}
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        <button
          type="submit"
          style={{ ...styles.button, width: "100%" }}
          disabled={loading}
        >
          {loading ? "Entrando..." : "Entrar"}
        </button>
        {error && <div style={styles.errorBox}>{error}</div>}
        <div style={{ ...styles.brandSub, marginTop: "16px" }}>
          Se conecta directo a tu backend en localhost:8080
        </div>
      </form>
    </div>
  );
}

function NewIncidentForm({ token, onCreated }) {
  const [title, setTitle] = useState("");
  const [severity, setSeverity] = useState(2);
  const [tlp, setTlp] = useState("AMBER");
  const [pap, setPap] = useState("AMBER");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/api/v1/incidents`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ title, severity: Number(severity), tlp, pap }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Error ${res.status}`);
      }
      setTitle("");
      onCreated();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      style={{ padding: "12px 14px", borderTop: "1px solid #232838" }}
    >
      <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
        <input
          style={{ ...styles.input, flex: 1 }}
          placeholder="Título del incidente"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <select
          style={{ ...styles.input, width: "90px" }}
          value={severity}
          onChange={(e) => setSeverity(e.target.value)}
        >
          <option value={1}>Sev 1</option>
          <option value={2}>Sev 2</option>
          <option value={3}>Sev 3</option>
          <option value={4}>Sev 4</option>
        </select>
      </div>
      <div style={{ display: "flex", gap: "8px" }}>
        <select
          style={styles.input}
          value={tlp}
          onChange={(e) => setTlp(e.target.value)}
        >
          {["RED", "AMBER_STRICT", "AMBER", "GREEN", "CLEAR"].map((v) => (
            <option key={v} value={v}>
              TLP:{v}
            </option>
          ))}
        </select>
        <select
          style={styles.input}
          value={pap}
          onChange={(e) => setPap(e.target.value)}
        >
          {["RED", "AMBER", "GREEN", "WHITE"].map((v) => (
            <option key={v} value={v}>
              PAP:{v}
            </option>
          ))}
        </select>
        <button style={styles.button} disabled={submitting} type="submit">
          {submitting ? "..." : "Crear"}
        </button>
      </div>
      {error && <div style={styles.errorBox}>{error}</div>}
    </form>
  );
}

export default function SocDashboard() {
  const [token, setToken] = useState(null);
  const [profile, setProfile] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [mttd, setMttd] = useState(null);
  const [mttr, setMttr] = useState(null);
  const [geoOrigins, setGeoOrigins] = useState([]);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(false);

  const authHeaders = useCallback(
    () => ({ Authorization: `Bearer ${token}` }),
    [token]
  );

  const loadAll = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setLoadError(null);
    try {
      const [profRes, incRes, alertRes, mttdRes, mttrRes, geoRes] = await Promise.all(
        [
          fetch(`${API_BASE}/api/v1/profiles/me`, { headers: authHeaders() }),
          fetch(`${API_BASE}/api/v1/incidents?limit=50`, {
            headers: authHeaders(),
          }),
          fetch(`${API_BASE}/api/v1/alerts?limit=100`, {
            headers: authHeaders(),
          }),
          fetch(`${API_BASE}/api/v1/alerts/mttd`, { headers: authHeaders() }),
          fetch(`${API_BASE}/api/v1/incidents/mttr`, {
            headers: authHeaders(),
          }),
          fetch(`${API_BASE}/api/v1/alerts/geo`, { headers: authHeaders() }),
        ]
      );

      if (profRes.status === 401) {
        throw new Error(
          "Token inválido o expirado. Vuelve a iniciar sesión."
        );
      }

      const prof = await profRes.json();
      const inc = incRes.ok ? await incRes.json() : [];
      const alr = alertRes.ok ? await alertRes.json() : [];
      const mttdData = mttdRes.ok ? await mttdRes.json() : {};
      const mttrData = mttrRes.ok ? await mttrRes.json() : {};
      const geoData = geoRes.ok ? await geoRes.json() : [];

      setProfile(prof);
      setIncidents(inc);
      setAlerts(alr);
      setMttd(mttdData.mttd_seconds);
      setMttr(mttrData.mttr_seconds);
      setGeoOrigins(geoData);
    } catch (err) {
      setLoadError(err.message || "No se pudo conectar con el backend.");
    } finally {
      setLoading(false);
    }
  }, [token, authHeaders]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  if (!token) {
    return <LoginScreen onLogin={setToken} />;
  }

  const severityData = [1, 2, 3, 4].map((sev) => ({
    severity: `Sev ${sev}`,
    sevNum: sev,
    count: alerts.filter((a) => a.severity === sev).length,
  }));

  const categoryCounts = {};
  alerts.forEach((a) => {
    categoryCounts[a.category] = (categoryCounts[a.category] || 0) + 1;
  });
  const categoryData = Object.entries(categoryCounts).map(([cat, count]) => ({
    category: CATEGORY_LABEL[cat] || cat,
    count,
  }));

  const openIncidents = incidents.filter((i) => i.status !== "closed").length;
  const criticalAlerts = alerts.filter((a) => a.severity === 4).length;

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <div style={styles.brand}>mini-soc</div>
          <div style={styles.brandSub}>
            {profile
              ? `${profile.email} · ${profile.role}`
              : "cargando sesión..."}
          </div>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <button style={styles.buttonGhost} onClick={loadAll}>
            {loading ? "Actualizando..." : "Actualizar"}
          </button>
          <button
            style={styles.buttonGhost}
            onClick={() => {
              setToken(null);
              setProfile(null);
            }}
          >
            Salir
          </button>
        </div>
      </div>

      {loadError && (
        <div style={{ ...styles.errorBox, margin: "14px 24px" }}>
          {loadError}
        </div>
      )}

      <div style={{ display: "flex", borderBottom: "1px solid #232838" }}>
        <div style={styles.statBlock}>
          <div style={styles.statLabel}>MTTD promedio</div>
          <div style={{ ...styles.statValue, ...styles.mono }}>
            {fmtDuration(mttd)}
          </div>
        </div>
        <div style={styles.statBlock}>
          <div style={styles.statLabel}>MTTR promedio</div>
          <div style={{ ...styles.statValue, ...styles.mono }}>
            {fmtDuration(mttr)}
          </div>
        </div>
        <div style={styles.statBlock}>
          <div style={styles.statLabel}>Incidentes abiertos</div>
          <div style={styles.statValue}>{openIncidents}</div>
        </div>
        <div style={{ ...styles.statBlock, borderRight: "none" }}>
          <div style={styles.statLabel}>Alertas críticas (sev 4)</div>
          <div
            style={{
              ...styles.statValue,
              color: criticalAlerts > 0 ? SEVERITY_COLOR[4] : "#E6E9EF",
            }}
          >
            {criticalAlerts}
          </div>
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1.3fr 1fr",
          gap: "16px",
          padding: "16px 24px",
        }}
      >
        <div style={styles.panel}>
          <div style={styles.panelTitle}>INCIDENTES ({incidents.length})</div>
          <div style={{ maxHeight: "320px", overflowY: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={styles.th}>Sev</th>
                  <th style={styles.th}>Título</th>
                  <th style={styles.th}>Estado</th>
                  <th style={styles.th}>Creado</th>
                </tr>
              </thead>
              <tbody>
                {incidents.length === 0 && (
                  <tr>
                    <td style={styles.td} colSpan={4}>
                      Sin incidentes visibles para tu rol.
                    </td>
                  </tr>
                )}
                {incidents.map((inc) => (
                  <tr key={inc.id}>
                    <td style={styles.td}>
                      <span style={styles.badge(SEVERITY_COLOR[inc.severity])} />
                      {inc.severity}
                    </td>
                    <td style={styles.td}>{inc.title}</td>
                    <td style={styles.td}>
                      {STATUS_LABEL[inc.status] || inc.status}
                    </td>
                    <td style={{ ...styles.td, ...styles.mono, fontSize: "12px" }}>
                      {fmtTime(inc.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <NewIncidentForm token={token} onCreated={loadAll} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={styles.panel}>
            <div style={styles.panelTitle}>ALERTAS POR SEVERIDAD</div>
            <div style={{ padding: "12px" }}>
              <ResponsiveContainer width="100%" height={140}>
                <BarChart data={severityData}>
                  <CartesianGrid stroke="#1A1E29" vertical={false} />
                  <XAxis
                    dataKey="severity"
                    tick={{ fill: "#5B6373", fontSize: 11 }}
                    axisLine={{ stroke: "#232838" }}
                    tickLine={false}
                  />
                  <YAxis
                    allowDecimals={false}
                    tick={{ fill: "#5B6373", fontSize: 11 }}
                    axisLine={{ stroke: "#232838" }}
                    tickLine={false}
                    width={24}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "#12161F",
                      border: "1px solid #232838",
                      fontSize: "12px",
                    }}
                  />
                  <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                    {severityData.map((d) => (
                      <Cell key={d.severity} fill={SEVERITY_COLOR[d.sevNum]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div style={styles.panel}>
            <div style={styles.panelTitle}>ALERTAS POR CATEGORÍA MITRE</div>
            <div style={{ padding: "12px" }}>
              {categoryData.length === 0 ? (
                <div style={{ ...styles.statLabel, padding: "20px 0" }}>
                  Sin alertas todavía.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={140}>
                  <BarChart data={categoryData} layout="vertical">
                    <CartesianGrid stroke="#1A1E29" horizontal={false} />
                    <XAxis
                      type="number"
                      allowDecimals={false}
                      tick={{ fill: "#5B6373", fontSize: 11 }}
                      axisLine={{ stroke: "#232838" }}
                      tickLine={false}
                    />
                    <YAxis
                      type="category"
                      dataKey="category"
                      tick={{ fill: "#8B93A7", fontSize: 11 }}
                      axisLine={{ stroke: "#232838" }}
                      tickLine={false}
                      width={130}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#12161F",
                        border: "1px solid #232838",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="count" fill="#1E5A8A" radius={[0, 2, 2, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: "0 24px 16px" }}>
        <div style={styles.panel}>
          <div style={styles.panelTitle}>
            ORIGEN GEOGRÁFICO DE LAS AMENAZAS
          </div>
          <div style={{ padding: "12px 14px" }}>
            {geoOrigins.length === 0 ? (
              <div style={styles.statLabel}>Sin datos de origen todavía.</div>
            ) : (
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr>
                    <th style={styles.th}>IP origen</th>
                    <th style={styles.th}>Ubicación</th>
                    <th style={styles.th}>Alertas</th>
                    <th style={styles.th}>Sev. máx</th>
                  </tr>
                </thead>
                <tbody>
                  {geoOrigins.map((g) => (
                    <tr key={g.ip}>
                      <td style={{ ...styles.td, ...styles.mono }}>{g.ip}</td>
                      <td style={styles.td}>
                        {g.geolocatable ? (
                          <span>
                            {g.city ? `${g.city}, ` : ""}
                            {g.country}{" "}
                            <span style={{ ...styles.mono, color: "#5B6373", fontSize: "11px" }}>
                              ({g.lat?.toFixed(2)}, {g.lon?.toFixed(2)})
                            </span>
                          </span>
                        ) : (
                          <span style={{ color: "#5B6373", fontStyle: "italic" }}>
                            {g.reason}
                          </span>
                        )}
                      </td>
                      <td style={styles.td}>{g.count}</td>
                      <td style={styles.td}>
                        <span style={styles.badge(SEVERITY_COLOR[g.max_severity])} />
                        {g.max_severity}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            <div style={{ ...styles.brandSub, marginTop: "10px" }}>
              Nota: las IPs de red privada (192.168.x.x, 10.x.x.x) o de rangos
              reservados para documentación no tienen ubicación geográfica
              real — se muestran así en vez de inventar una.
            </div>
          </div>
        </div>
      </div>

      <div style={{ padding: "0 24px 24px" }}>
        <div style={styles.panel}>
          <div style={styles.panelTitle}>ALERTAS RECIENTES ({alerts.length})</div>
          <div style={{ maxHeight: "280px", overflowY: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  <th style={styles.th}>Sev</th>
                  <th style={styles.th}>Categoría</th>
                  <th style={styles.th}>Origen</th>
                  <th style={styles.th}>Destino</th>
                  <th style={styles.th}>Descripción</th>
                  <th style={styles.th}>Detectado</th>
                </tr>
              </thead>
              <tbody>
                {alerts.length === 0 && (
                  <tr>
                    <td style={styles.td} colSpan={6}>
                      Sin alertas visibles para tu rol.
                    </td>
                  </tr>
                )}
                {alerts.map((a) => (
                  <tr key={a.id}>
                    <td style={styles.td}>
                      <span style={styles.badge(SEVERITY_COLOR[a.severity])} />
                      {a.severity}
                    </td>
                    <td style={styles.td}>
                      {CATEGORY_LABEL[a.category] || a.category}
                    </td>
                    <td style={{ ...styles.td, ...styles.mono }}>{a.src_ip}</td>
                    <td style={{ ...styles.td, ...styles.mono }}>{a.dst_ip}</td>
                    <td style={{ ...styles.td, fontSize: "12px" }}>
                      {a.description || "—"}
                    </td>
                    <td style={{ ...styles.td, ...styles.mono, fontSize: "12px" }}>
                      {fmtTime(a.detected_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
