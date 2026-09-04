/**
 * api.js
 * ======
 * Point unique d'appel au backend. Pourquoi centraliser ici plutot
 * que d'appeler `fetch` directement dans chaque composant : si
 * l'URL de l'API change (deploiement, port different), un seul
 * endroit a modifier. Ca centralise aussi la gestion du token
 * d'authentification -- chaque fonction l'ajoute automatiquement
 * si present, les composants n'ont pas a s'en soucier.
 */

const API_BASE = "http://localhost:8000";

async function request(path, { method = "GET", token, body } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    // On lit le message d'erreur renvoye par FastAPI (`detail`)
    // plutot que de laisser une erreur generique -- l'utilisateur
    // voit alors "Client introuvable" plutot que "Erreur 404".
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

export async function login(username, password) {
  // /auth/login attend un formulaire (OAuth2PasswordRequestForm cote
  // FastAPI), pas du JSON -- d'ou URLSearchParams plutot que
  // JSON.stringify ici, contrairement au reste de l'API.
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${API_BASE}/auth/login`, { method: "POST", body });
  if (!res.ok) throw new Error("Identifiants incorrects");
  return res.json();
}

export const getCustomers = (limit = 20) => request(`/customers/?limit=${limit}`);
export const getMonthlyRevenue = () => request("/analytics/monthly-revenue");
export const getTopProducts = (limit = 5) => request(`/analytics/top-products?limit=${limit}`);
export const getChurnPrediction = (customerId, token) =>
  request(`/ml/churn/${customerId}`, { token });
