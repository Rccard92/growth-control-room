import { motion } from "framer-motion";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { BrandLogo } from "../components/BrandLogo";
import { useAuth } from "../components/AuthProvider";
import { APP_ROUTES } from "../routes/config";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, status } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") {
    const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
    return <Navigate to={from ?? APP_ROUTES.projects} replace />;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      const from = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(from ?? APP_ROUTES.projects, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Accesso non riuscito.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="gcr-login">
      <motion.div
        className="gcr-login__panel"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="gcr-login__brand">
          <BrandLogo variant="full" size="lg" />
        </div>
        <h1 className="gcr-login__title">Growth Control Room</h1>
        <p className="gcr-login__claim">
          La control room AI per governare crescita, dati e contenuti dei tuoi brand.
        </p>

        <form className="gcr-login__form" onSubmit={handleSubmit}>
          <label className="gcr-login__label" htmlFor="login-email">
            Email
          </label>
          <input
            id="login-email"
            className="gcr-login__input"
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label className="gcr-login__label" htmlFor="login-password">
            Password
          </label>
          <input
            id="login-password"
            className="gcr-login__input"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          {error && (
            <p className="gcr-login__error" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="gcr-btn gcr-btn--primary gcr-login__submit"
            disabled={submitting}
          >
            {submitting ? "Accesso in corso…" : "Entra nella Control Room"}
          </button>
        </form>

        <p style={{ marginTop: "1.25rem", fontSize: "0.8125rem" }}>
          <Link className="gcr-legal__link" to={APP_ROUTES.privacy}>
            Privacy Policy
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
