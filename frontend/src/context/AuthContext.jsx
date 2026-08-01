import React, { createContext, useContext, useState, useEffect } from 'react';
import API from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(true);
  const [garageInfo, setGarageInfo] = useState(null);

  const fetchGarageInfo = async () => {
    try {
      const res = await API.get('/public/info/');
      setGarageInfo(res.data);
    } catch (err) {
      console.error('Failed to load garage info', err);
    }
  };

  const fetchCurrentUser = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }
    try {
      const res = await API.get('/auth/me/');
      setUser(res.data);
      localStorage.setItem('user', JSON.stringify(res.data));
    } catch (err) {
      console.error('Auth verification failed', err);
      logout();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGarageInfo();
    fetchCurrentUser();
  }, []);

  const login = async (username, password) => {
    const res = await API.post('/auth/token/', { username, password });
    localStorage.setItem('access_token', res.data.access);
    localStorage.setItem('refresh_token', res.data.refresh);
    
    // Fetch profile
    const userRes = await API.get('/auth/me/');
    setUser(userRes.data);
    localStorage.setItem('user', JSON.stringify(userRes.data));
    return userRes.data;
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  };

  const isAdmin = user?.role === 'ADMIN' || user?.profile?.role === 'ADMIN';
  const isStaff = user?.role === 'STAFF' || user?.profile?.role === 'STAFF';

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role || user?.profile?.role || 'STAFF',
        isAdmin,
        isStaff,
        login,
        logout,
        loading,
        garageInfo,
        fetchGarageInfo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
