import { useState } from "react";
import { getChurnPrediction } from "../api";

function riskLevel(p) {
  // Encodage couleur qui porte du sens : sarcelle = faible risque
  // (coherent avec l'accent "actif" du reste de l'interface), ambre
  // = risque modere, corail = risque eleve. Jamais utilise ailleurs
  // dans l'app, pour que ce signal reste immediatement lisible.
  if (p < 0.4) return { color: "#4fd1c5", label: "Risque faible" };
  if (p < 0.7) return { color: "#f0a857", label: "Risque modere" };
  return { color: "#e8694f", label: "Risque eleve" };
}

export default function ChurnLookup({ token }) {
  const [customerId, setCustomerId] = useState("1");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleSearch(e) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const data = await getChurnPrediction(customerId, token);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const risk = result ? riskLevel(result.churn_probability) : null;

  return (
    <div className="panel" style={{ maxWidth: 420 }}>
      <form className="inline-form" onSubmit={handleSearch}>
        <div className="field">
          <label>ID client</label>
          <input
            type="number"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          />
        </div>
        <button type="submit" className="btn">Verifier</button>
      </form>

      {loading && <p className="empty-state">Calcul en cours…</p>}
      {error && <p className="error-text">{error}</p>}

      {result && risk && (
        <div className="risk-gauge">
          <div className="risk-header">
            <span style={{ color: risk.color, fontSize: 13, fontWeight: 500 }}>
              {risk.label} · Client #{result.customer_id}
            </span>
            <span className="risk-value" style={{ color: risk.color }}>
              {(result.churn_probability * 100).toFixed(0)}%
            </span>
          </div>
          <div className="risk-track">
            <div
              className="risk-fill"
              style={{
                width: `${result.churn_probability * 100}%`,
                background: risk.color,
              }}
            />
          </div>
          <ul className="risk-reasons">
            {result.reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
