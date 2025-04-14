import { createContext, useState, useEffect } from 'react';
import axios from '../axiosInstance';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [originalUser, setOriginalUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const isImpersonating = !!originalUser;

  const login = (userData) => {
    setUser(userData);
  };

  const logout = async () => {
    try {
      await axios.get('/api/v1/auth/logout');
      setUser(null);
      setOriginalUser(null);
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const impersonate = async (userId) => {
    try {
      const res = await axios.post(`/api/v1/auth/impersonate/${userId}`);
      if (!originalUser) {
        setOriginalUser(user._id);
      }
      setUser(res.data);
    } catch (err) {
      console.error('Impersonation failed:', err);
    }
  };

  const stopImpersonating = async () => {
    try {
      const res = await axios.get('/api/v1/auth/me', {
        headers: {
          'x-impersonate-user': originalUser
        }
      });
      setUser(res.data);
      setOriginalUser(null);
    } catch (err) {
      console.error('Failed to stop impersonation:', err);
    }
  };

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await axios.get('/api/v1/auth/me');
        setUser(res.data);
      } catch (err) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        logout,
        impersonate,
        stopImpersonating,
        isImpersonating,
        loading
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  return useContext(AuthContext);
};
