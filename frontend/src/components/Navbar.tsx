import { useState } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

function toggleTheme(): boolean {
  const dark = document.documentElement.classList.toggle("dark");
  try { localStorage.setItem("lotkeeper-theme", dark ? "dark" : "light"); } catch { /* storage unavailable */ }
  return dark;
}

export function Navbar() {
  const { user, logout } = useAuth();
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  const link = ({ isActive }: { isActive: boolean }) =>
    `rounded px-3 py-1.5 text-sm font-semibold ${isActive ? "bg-ink text-floor" : "text-muted hover:text-ink"}`;

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3">
        <NavLink to="/" className="flex items-center gap-2 font-display text-xl font-extrabold">
          <span className="plate px-1.5 py-0.5 text-xs">LOT</span> Lotkeeper
        </NavLink>
        <nav className="ml-4 flex gap-1">
          <NavLink to="/" end className={link}>The lot</NavLink>
          <NavLink to="/orders" className={link}>My orders</NavLink>
          {user?.role === "admin" && <NavLink to="/admin" className={link}>Back office</NavLink>}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          <button className="btn-ghost !px-2.5" onClick={() => setDark(toggleTheme())} aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}>
            {dark ? "☀" : "☾"}
          </button>
          {user && (
            <>
              <span className="hidden text-sm text-muted sm:inline">{user.email}</span>
              <button className="btn-ghost" onClick={logout}>Sign out</button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
