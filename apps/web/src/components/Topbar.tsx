import { Link } from "react-router-dom";
import { BrandLogo } from "./BrandLogo";
import { APP_ROUTES } from "../routes/config";

export function Topbar() {
  return (
    <header className="gcr-topbar">
      <Link to={APP_ROUTES.projects} className="gcr-topbar__logo">
        <BrandLogo variant="full" size="sm" />
      </Link>
      <nav className="gcr-topbar__nav">
        <Link to={APP_ROUTES.projects} className="gcr-topbar__link">
          Progetti
        </Link>
      </nav>
    </header>
  );
}
