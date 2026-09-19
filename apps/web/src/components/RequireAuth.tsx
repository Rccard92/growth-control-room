import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { APP_ROUTES } from "../routes/config";

/** Gate for every route that needs a signed-in user. */
export function RequireAuth() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <div className="gcr-auth-loading" role="status" aria-live="polite">
        Verifica sessione…
      </div>
    );
  }

  if (status === "anonymous") {
    return <Navigate to={APP_ROUTES.login} replace state={{ from: location }} />;
  }

  return <Outlet />;
}
