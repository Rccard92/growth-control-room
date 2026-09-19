import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  fetchCurrentUser,
  getStoredToken,
  login as loginRequest,
  logout as logoutRequest,
  onTokenChange,
  type AuthUser,
} from "../lib/auth-api";

interface AuthContextValue {
  user: AuthUser | null;
  status: "loading" | "authenticated" | "anonymous";
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");

  const loadUser = useCallback(async () => {
    if (!getStoredToken()) {
      setUser(null);
      setStatus("anonymous");
      return;
    }
    try {
      setUser(await fetchCurrentUser());
      setStatus("authenticated");
    } catch {
      setUser(null);
      setStatus("anonymous");
    }
  }, []);

  useEffect(() => {
    void loadUser();
    // A 401 anywhere in the app clears the token; react to it here.
    return onTokenChange((token) => {
      if (!token) {
        setUser(null);
        setStatus("anonymous");
      }
    });
  }, [loadUser]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      login: async (email, password) => {
        const response = await loginRequest(email, password);
        setUser(response.user);
        setStatus("authenticated");
      },
      logout: async () => {
        await logoutRequest();
        setUser(null);
        setStatus("anonymous");
      },
    }),
    [user, status],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth deve essere usato dentro <AuthProvider>");
  }
  return context;
}
