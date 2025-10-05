import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import TokenManager from '../utils/tokenManager';
import { authApi, apiClient } from '../services/api';

export interface Company {
  id: number;
  name: string;
  tax_id: string;
  user_role: 'ADMIN' | 'USER';
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone: string;
  preferred_language: string;
  timezone: string;
  last_active_company: number | null;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: User | null;
  companies: Company[];
  currentCompany: Company | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  error: string | null;
}

type AuthAction =
  | { type: 'AUTH_START' }
  | {
      type: 'AUTH_SUCCESS';
      payload: { user: User; companies: Company[]; accessToken: string; refreshToken: string };
    }
  | { type: 'AUTH_ERROR'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'SET_COMPANY'; payload: Company }
  | { type: 'TOKEN_REFRESH'; payload: { accessToken: string; refreshToken?: string } }
  | { type: 'CLEAR_ERROR' };

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  companies: [],
  currentCompany: null,
  accessToken: null,
  refreshToken: null,
  isLoading: false,
  error: null,
};

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'AUTH_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    case 'AUTH_SUCCESS':
      const currentCompany =
        action.payload.companies.find((c) => c.id === action.payload.user.last_active_company) ||
        action.payload.companies[0] ||
        null;

      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        companies: action.payload.companies,
        currentCompany,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken,
        isLoading: false,
        error: null,
      };
    case 'AUTH_ERROR':
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        companies: [],
        currentCompany: null,
        accessToken: null,
        refreshToken: null,
        isLoading: false,
        error: action.payload,
      };
    case 'LOGOUT':
      return {
        ...initialState,
      };
    case 'SET_COMPANY':
      return {
        ...state,
        currentCompany: action.payload,
      };
    case 'TOKEN_REFRESH':
      return {
        ...state,
        accessToken: action.payload.accessToken,
        refreshToken: action.payload.refreshToken || state.refreshToken,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

interface AuthContextType {
  state: AuthState;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  switchCompany: (company: Company) => Promise<void>;
  clearError: () => void;
}

export interface RegisterData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
  password_confirm: string;
  company_name: string;
  company_tax_id: string;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const tokenManager = TokenManager.getInstance();

  // Setup token manager interceptors
  useEffect(() => {
    console.log('🔧 Setting up TokenManager interceptors');

    const handleTokenRefresh = (accessToken: string, refreshToken?: string) => {
      console.log('🔄 Token refresh triggered');
      dispatch({
        type: 'TOKEN_REFRESH',
        payload: { accessToken, refreshToken },
      });
    };

    const handleLogout = () => {
      console.log('👋 Logout triggered by TokenManager');
      dispatch({ type: 'LOGOUT' });
    };

    tokenManager.setupInterceptors(handleTokenRefresh, handleLogout, apiClient);
    console.log('✅ TokenManager interceptors setup complete');
  }, [tokenManager]);

  // Load saved authentication state on mount
  useEffect(() => {
    const loadSavedAuth = () => {
      console.log('🔍 Loading saved authentication state...');
      try {
        const accessToken = localStorage.getItem('accessToken');
        const refreshToken = localStorage.getItem('refreshToken');
        const userData = localStorage.getItem('userData');
        const companiesData = localStorage.getItem('companiesData');
        const currentCompanyData = localStorage.getItem('currentCompany');

        console.log('📱 localStorage check:', {
          hasAccessToken: !!accessToken,
          hasRefreshToken: !!refreshToken,
          hasUserData: !!userData,
          hasCompaniesData: !!companiesData,
          hasCurrentCompany: !!currentCompanyData,
        });

        if (accessToken && refreshToken && userData && companiesData) {
          const user = JSON.parse(userData);
          const companies = JSON.parse(companiesData);
          const currentCompany = currentCompanyData ? JSON.parse(currentCompanyData) : companies[0];

          console.log('✅ Restoring authentication state for user:', user.username);
          console.log('🏢 Current company:', currentCompany?.name);

          dispatch({
            type: 'AUTH_SUCCESS',
            payload: { user, companies, accessToken, refreshToken },
          });

          if (currentCompany) {
            dispatch({ type: 'SET_COMPANY', payload: currentCompany });
          }
        } else {
          console.log('❌ Incomplete authentication data in localStorage');
        }
      } catch (error) {
        console.error('Error loading saved auth state:', error);
        tokenManager.clearTokens();
      }
    };

    loadSavedAuth();
  }, [tokenManager]);

  // Save authentication state to localStorage
  useEffect(() => {
    if (state.isAuthenticated && state.user && state.accessToken && state.refreshToken) {
      console.log('💾 Saving authentication state to localStorage');
      localStorage.setItem('accessToken', state.accessToken);
      localStorage.setItem('refreshToken', state.refreshToken);
      localStorage.setItem('userData', JSON.stringify(state.user));
      localStorage.setItem('companiesData', JSON.stringify(state.companies));
      if (state.currentCompany) {
        localStorage.setItem('currentCompany', JSON.stringify(state.currentCompany));
      }
    }
    // Note: We removed the automatic localStorage clearing to prevent race conditions
    // localStorage will only be cleared on explicit logout action
  }, [
    state.isAuthenticated,
    state.user,
    state.accessToken,
    state.refreshToken,
    state.currentCompany,
    state.companies,
  ]);

  const login = async (username: string, password: string) => {
    dispatch({ type: 'AUTH_START' });

    try {
      const response = await authApi.login(username, password);
      const data = response.data;

      dispatch({
        type: 'AUTH_SUCCESS',
        payload: {
          user: data.user,
          companies: data.companies,
          accessToken: data.access,
          refreshToken: data.refresh,
        },
      });
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.non_field_errors?.[0] ||
        error.message ||
        'Login failed';
      dispatch({
        type: 'AUTH_ERROR',
        payload: errorMessage,
      });
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    dispatch({ type: 'AUTH_START' });

    try {
      await authApi.register(data);

      // After successful registration, automatically login
      await login(data.username, data.password);
    } catch (error: any) {
      const errorData = error.response?.data;
      let errorMessage = 'Registration failed';

      if (errorData) {
        if (errorData.non_field_errors) {
          errorMessage = errorData.non_field_errors[0];
        } else if (errorData.username) {
          errorMessage = `Username: ${errorData.username[0]}`;
        } else if (errorData.email) {
          errorMessage = `Email: ${errorData.email[0]}`;
        } else if (errorData.company_tax_id) {
          errorMessage = `Company Tax ID: ${errorData.company_tax_id[0]}`;
        }
      }

      dispatch({
        type: 'AUTH_ERROR',
        payload: errorMessage,
      });
      throw error;
    }
  };

  const logout = () => {
    tokenManager.clearTokens();
    dispatch({ type: 'LOGOUT' });
  };

  const switchCompany = async (company: Company) => {
    if (!state.accessToken) {
      throw new Error('Not authenticated');
    }

    try {
      await authApi.switchCompany(company.id);
      dispatch({ type: 'SET_COMPANY', payload: company });
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Failed to switch company';
      console.error('Failed to switch company:', errorMessage);
      throw new Error(errorMessage);
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value: AuthContextType = {
    state,
    login,
    register,
    logout,
    switchCompany,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
