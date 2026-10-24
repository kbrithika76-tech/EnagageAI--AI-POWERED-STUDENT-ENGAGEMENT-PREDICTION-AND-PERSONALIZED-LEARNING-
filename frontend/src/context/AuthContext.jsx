import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('engageai_token');
    const savedUser = localStorage.getItem('engageai_user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
      // Optionally fetch fresh /auth/me
      api.get('/auth/me')
        .then(res => {
          setUser(res.data);
          localStorage.setItem('engageai_user', JSON.stringify(res.data));
        })
        .catch(() => logout())
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token } = res.data;
    
    localStorage.setItem('engageai_token', access_token);
    
    // Fetch complete user profile including onboarding details
    const meRes = await api.get('/auth/me');
    const userData = meRes.data;
    
    localStorage.setItem('engageai_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const register = async (name, email, password, role = 'student') => {
    const res = await api.post('/auth/register', { name, email, password, role });
    const { access_token } = res.data;

    localStorage.setItem('engageai_token', access_token);
    
    // Fetch complete user profile
    const meRes = await api.get('/auth/me');
    const userData = meRes.data;

    localStorage.setItem('engageai_user', JSON.stringify(userData));
    setUser(userData);
    return userData;
  };

  const refreshUser = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      localStorage.setItem('engageai_user', JSON.stringify(res.data));
      return res.data;
    } catch (e) {
      logout();
    }
  };

  const logout = () => {
    localStorage.removeItem('engageai_token');
    localStorage.removeItem('engageai_user');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
