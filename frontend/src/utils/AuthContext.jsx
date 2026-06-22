import { createContext, useContext, useEffect, useState } from 'react';
import { getUser, logout as doLogout } from './auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUserState] = useState(() => getUser());

  useEffect(() => {
    const onSessionLost = () => setUserState(null);
    window.addEventListener('auth:session-lost', onSessionLost);
    return () => window.removeEventListener('auth:session-lost', onSessionLost);
  }, []);

  const logout = () => {
    doLogout();
    setUserState(null);
  };

  const updateUser = (u) => {
    setUserState(u);
  };

  return (
    <AuthContext.Provider value={{ user, loading: false, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  return useContext(AuthContext);
}
