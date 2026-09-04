import { useState } from "react";
import { login } from "../api";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    try {
      const data = await login(username, password);
      onLogin(data.access_token, data.role);
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="panel" style={{ maxWidth: 340 }}>
      <form onSubmit={handleSubmit}>
        <div className="field">
          <label>Utilisateur</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} />
        </div>
        <div className="field">
          <label>Mot de passe</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="error-text">{error}</p>}
        <button type="submit" className="btn">Se connecter</button>
      </form>
      <p className="hint">admin / admin123 (accès churn) · viewer / viewer123 (accès refusé)</p>
    </div>
  );
}
