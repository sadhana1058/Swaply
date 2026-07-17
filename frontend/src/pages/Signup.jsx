import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { api } from "../api/client";
import GoogleButton from "../components/GoogleButton";

export default function Signup() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }
    setBusy(true);
    try {
      await signup(form);
      navigate("/home");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card">
      <h1>Create account</h1>
      <p className="muted">Start with email &amp; password</p>

      {error && <div className="alert">{error}</div>}

      <form onSubmit={onSubmit}>
        <label>Full name</label>
        <input type="text" value={form.full_name}
          onChange={update("full_name")} placeholder="Ada Lovelace" />

        <label>Email</label>
        <input type="email" value={form.email} required
          onChange={update("email")} placeholder="you@example.com" />

        <label>Password</label>
        <input type="password" value={form.password} required
          onChange={update("password")} placeholder="At least 8 characters" />

        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "Creating…" : "Sign up"}
        </button>
      </form>

      <div className="divider"><span>or</span></div>
      <GoogleButton href={api.googleLoginUrl} label="Sign up with Google" />

      <p className="muted center">
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}
