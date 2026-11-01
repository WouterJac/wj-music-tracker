import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="state">
      <h1>Page not found</h1>
      <p>That address does not exist in WJ Music Tracker.</p>
      <Link to="/albums">Back to albums</Link>
    </div>
  );
}
