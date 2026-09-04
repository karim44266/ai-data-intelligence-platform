import { useState } from "react";
import Dashboard from "./components/Dashboard";
import CustomerList from "./components/CustomerList";
import Login from "./components/Login";
import ChurnLookup from "./components/ChurnLookup";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "customers", label: "Clients" },
  { id: "churn", label: "Risque de churn" },
];

export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [token, setToken] = useState(null);
  const [role, setRole] = useState(null);

  function handleLogin(newToken, newRole) {
    setToken(newToken);
    setRole(newRole);
    setTab("churn");
  }

  function handleLogout() {
    setToken(null);
    setRole(null);
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-dot" />
          <span className="brand-name">Data Intelligence</span>
        </div>

        <nav className="nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${tab === item.id ? "active" : ""}`}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          {token ? (
            <div className="session-row">
              <span className="role-tag">{role}</span>
              <button className="link-button" onClick={handleLogout}>
                deconnexion
              </button>
            </div>
          ) : (
            <button className="link-button" onClick={() => setTab("login")}>
              se connecter →
            </button>
          )}
        </div>
      </aside>

      <main className="main">
        {tab === "dashboard" && (
          <>
            <h1 className="page-title">Vue d'ensemble</h1>
            <p className="page-subtitle">Ventes et catalogue, mis a jour depuis le data warehouse.</p>
            <Dashboard />
          </>
        )}

        {tab === "customers" && (
          <>
            <h1 className="page-title">Clients</h1>
            <p className="page-subtitle">20 comptes les plus recents.</p>
            <CustomerList />
          </>
        )}

        {tab === "login" && (
          <>
            <h1 className="page-title">Connexion</h1>
            <p className="page-subtitle">Requis pour consulter le risque de churn.</p>
            <Login onLogin={handleLogin} />
          </>
        )}

        {tab === "churn" && (
          <>
            <h1 className="page-title">Risque de churn</h1>
            <p className="page-subtitle">Reserve aux comptes avec le role admin.</p>
            {token ? (
              <ChurnLookup token={token} />
            ) : (
              <div className="panel">
                <p className="empty-state">
                  Connecte-toi pour acceder a cette section.{" "}
                  <button className="link-button" onClick={() => setTab("login")}>
                    Se connecter
                  </button>
                </p>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
