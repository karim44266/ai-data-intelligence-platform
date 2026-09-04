import { useEffect, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { getMonthlyRevenue, getTopProducts } from "../api";

function formatCurrency(n) {
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(n);
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "#1c202b",
        border: "1px solid #333846",
        borderRadius: 4,
        padding: "8px 12px",
        fontFamily: "IBM Plex Mono, monospace",
        fontSize: 12,
      }}
    >
      <div style={{ color: "#8b909c", marginBottom: 2 }}>{label}</div>
      <div style={{ color: "#ecebe4" }}>{formatCurrency(payload[0].value)}</div>
    </div>
  );
}

export default function Dashboard() {
  const [revenue, setRevenue] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getMonthlyRevenue(), getTopProducts(5)])
      .then(([rev, top]) => {
        setRevenue(rev.map((r) => ({ label: `${r.month}/${r.year}`, revenue: r.revenue })));
        setTopProducts(top);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (error) return <p className="error-text">Erreur : {error}</p>;
  if (loading) return <p className="empty-state">Chargement…</p>;

  const totalRevenue = revenue.reduce((sum, r) => sum + r.revenue, 0);
  const bestMonth = revenue.reduce((a, b) => (b.revenue > (a?.revenue ?? -Infinity) ? b : a), null);
  const topProduct = topProducts[0];
  const maxProductRevenue = topProducts.length ? topProducts[0].revenue : 1;

  return (
    <div>
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-value">{formatCurrency(totalRevenue)}</div>
          <div className="kpi-label">Revenu total</div>
        </div>
        <div className="kpi">
          <div className="kpi-value">{bestMonth?.label ?? "—"}</div>
          <div className="kpi-label">Meilleur mois</div>
        </div>
        <div className="kpi">
          <div className="kpi-value">{revenue.length}</div>
          <div className="kpi-label">Mois suivis</div>
        </div>
        <div className="kpi">
          <div className="kpi-value" style={{ fontSize: 16 }}>{topProduct?.product_name ?? "—"}</div>
          <div className="kpi-label">Produit n°1</div>
        </div>
      </div>

      <div className="panel">
        <h2 className="panel-title">Revenu par mois</h2>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={revenue} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
            <defs>
              <linearGradient id="revenueFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4fd1c5" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#4fd1c5" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#262a35" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: "#5b616d", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={{ stroke: "#262a35" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: "#5b616d", fontSize: 11, fontFamily: "IBM Plex Mono" }}
              axisLine={false}
              tickLine={false}
              width={64}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#4fd1c5"
              strokeWidth={2}
              fill="url(#revenueFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h2 className="panel-title">Top 5 produits</h2>
        {topProducts.map((p) => (
          <div className="bar-row" key={p.product_name}>
            <span className="bar-name">{p.product_name}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${(p.revenue / maxProductRevenue) * 100}%` }}
              />
            </div>
            <span className="bar-value">{formatCurrency(p.revenue)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
