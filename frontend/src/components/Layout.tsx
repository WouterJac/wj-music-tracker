import { Link, NavLink, Outlet } from "react-router-dom";

import { HealthStatus } from "../features/health/HealthStatus";

export function Layout() {
  return (
    <>
      <header className="site-header">
        <Link to="/albums" className="brand">
          WJ Music Tracker
        </Link>
        <nav aria-label="Main">
          <NavLink to="/albums">Albums</NavLink>
          <NavLink to="/artists">Artists</NavLink>
          <NavLink to="/lyrics">Lyrics</NavLink>
        </nav>
      </header>
      <main>
        <Outlet />
      </main>
      <footer className="site-footer">
        <HealthStatus />
      </footer>
    </>
  );
}
