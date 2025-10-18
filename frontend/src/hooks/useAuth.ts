import { useAuth as useAuthContext, AuthContextType, Company } from '../contexts/AuthContext';

export const useAuth = (): AuthContextType => {
  return useAuthContext();
};

export const useCurrentCompany = (): Company | null => {
  const { state } = useAuthContext();
  return state.currentCompany;
};

export const useIsAuthenticated = (): boolean => {
  const { state } = useAuthContext();
  return state.isAuthenticated;
};

export const useUserRole = (): string | null => {
  const { state } = useAuthContext();
  return state.currentCompany?.user_role || null;
};

export const useIsCompanyAdmin = (): boolean => {
  const { state } = useAuthContext();
  return state.currentCompany?.user_role === 'ADMIN';
};
