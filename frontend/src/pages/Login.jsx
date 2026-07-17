import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import GoogleButton from "../components/GoogleButton";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
      navigate("/home");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h1>Welcome back</h1>
      <p className="muted">Sign in to your account</p>

      {error && <div className="alert">{error}</div>}

      <form onSubmit={onSubmit}>
        <label>Email</label>
        <input type="email" value={email} required
          onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />

        <label>Password</label>
        <input type="password" value={password} required
          onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" />

        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <div className="divider"><span>or</span></div>
      <GoogleButton href={api.googleLoginUrl} label="Sign in with Google" />

      <p className="muted center">
        No account? <Link to="/signup">Create one</Link>
      </p>
    </div>
  );
}
