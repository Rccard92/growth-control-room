import { Link, useNavigate } from "react-router-dom";
import { BrandLogo } from "./BrandLogo";
import { useAuth } from "./AuthProvider";
import { APP_ROUTES } from "../routes/config";

export function Topbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate(APP_ROUTES.login, { replace: true });
  };

  return (
    <header className="gcr-topbar">
      <Link to={APP_ROUTES.projects} className="gcr-topbar__logo">
        <BrandLogo variant="full" size="sm" />
      </Link>
      <nav className="gcr-topbar__nav">
        <Link to={APP_ROUTES.projects} className="gcr-topbar__link">
          Progetti
        </Link>
        {user && (
          <>
            <span className="gcr-topbar__user" title={user.email}>
              {user.email}
            </span>
            <button type="button" className="gcr-topbar__link" onClick={handleLogout}>
              Esci
            </button>
          </>
        )}
      </nav>
    </header>
  );
}
