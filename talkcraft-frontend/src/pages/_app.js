import React, { createContext, useContext, useState, useEffect } from "react";
import "@/styles/globals.css";

export const AuthContext = createContext({
  user: null,
  token: null,
  loginUser: () => {},
  logoutUser: () => {},
  isAuthenticated: false,
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const savedToken = localStorage.getItem("talkcraft_token");
    const savedUser = localStorage.getItem("talkcraft_user");
    if (savedToken && savedUser) {
      try {
        setToken(savedToken);
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.removeItem("talkcraft_token");
        localStorage.removeItem("talkcraft_user");
      }
    }
    setLoading(false);
  }, []);

  const loginUser = (newToken, newUser) => {
    localStorage.setItem("talkcraft_token", newToken);
    localStorage.setItem("talkcraft_user", JSON.stringify(newUser));
    setToken(newToken);
    setUser(newUser);
  };

  const logoutUser = () => {
    localStorage.removeItem("talkcraft_token");
    localStorage.removeItem("talkcraft_user");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loginUser,
        logoutUser,
        isAuthenticated: !!token,
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export default function App({ Component, pageProps }) {
  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}
