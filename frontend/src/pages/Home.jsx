import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Home() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const onLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="card">
      <div className="badge">{user.oauth_provider ? "Google account" : "Password account"}</div>
      <h1>Hi{user.full_name ? `, ${user.full_name}` : ""} 👋</h1>
      <p className="muted">You are signed in and viewing the protected home page.</p>

      <div className="profile">
        <Row label="Email" value={user.email} />
        <Row label="Name" value={user.full_name || "—"} />
        <Row label="Verified" value={user.is_verified ? "Yes" : "No"} />
        <Row label="Sign-in method" value={user.oauth_provider || "email + password"} />
        <Row label="User ID" value={user.id} mono />
      </div>

      <button className="btn" onClick={onLogout}>Log out</button>
    </div>
  );
}

function Row({ label, value, mono }) {
  return (
    <div className="row">
      <span className="row-label">{label}</span>
      <span className={mono ? "row-value mono" : "row-value"}>{value}</span>
    </div>
  );
}
