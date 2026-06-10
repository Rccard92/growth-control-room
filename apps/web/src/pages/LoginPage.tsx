import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { APP_ROUTES } from "../routes/config";

export function LoginPage() {
  const navigate = useNavigate();

  return (
    <div className="gcr-login">
      <motion.div
        className="gcr-login__panel"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="gcr-login__logo">G</div>
        <h1 className="gcr-login__title">Growth Control Room</h1>
        <p className="gcr-login__claim">
          La control room AI per governare crescita, dati e contenuti dei tuoi brand.
        </p>
        <button
          type="button"
          className="gcr-btn gcr-btn--primary"
          style={{ width: "100%", padding: "0.75rem 1.5rem", fontSize: "0.9375rem" }}
          onClick={() => navigate(APP_ROUTES.projects)}
        >
          Entra nella Control Room
        </button>
        <p style={{ marginTop: "1.25rem", fontSize: "0.8125rem" }}>
          <Link className="gcr-legal__link" to={APP_ROUTES.privacy}>
            Privacy Policy
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
