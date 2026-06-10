import { Button, Card } from "@gcr/ui";

export function LoginPage() {
  return (
    <div className="login-page">
      <div className="login-page__card">
        <Card title="Accedi" description="Growth Control Room">
          <form className="login-page__form" onSubmit={(e) => e.preventDefault()}>
            <div className="login-page__field">
              <label htmlFor="email">Email</label>
              <input id="email" type="email" placeholder="nome@azienda.com" />
            </div>
            <div className="login-page__field">
              <label htmlFor="password">Password</label>
              <input id="password" type="password" placeholder="••••••••" />
            </div>
            <Button type="submit" style={{ width: "100%" }}>
              Accedi
            </Button>
          </form>
          <p style={{ marginTop: "1rem", fontSize: "0.75rem", color: "#9ca3af" }}>
            Autenticazione non ancora implementata — pagina placeholder.
          </p>
        </Card>
      </div>
    </div>
  );
}
