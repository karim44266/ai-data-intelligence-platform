import { useEffect, useState } from "react";
import { getCustomers } from "../api";

export default function CustomerList() {
  const [customers, setCustomers] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getCustomers(20)
      .then(setCustomers)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (error) return <p className="error-text">Erreur : {error}</p>;

  return (
    <div className="panel">
      {loading ? (
        <p className="empty-state">Chargement…</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nom</th>
              <th>Email</th>
              <th>Pays</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.customer_id}>
                <td className="mono">#{c.customer_id}</td>
                <td>{c.first_name} {c.last_name}</td>
                <td className="mono">{c.email}</td>
                <td>{c.country}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
