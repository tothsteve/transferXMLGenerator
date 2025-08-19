import { useAuth as useAuthContext } from '../contexts/AuthContext';

export const useAuth = () => {
  return useAuthContext();
};

export const useCurrentCompany = () => {
  const { state } = useAuthContext();
  return state.currentCompany;
};

export const useIsAuthenticated = () => {
  const { state } = useAuthContext();
  return state.isAuthenticated;
};

export const useUserRole = () => {
  const { state } = useAuthContext();
  return state.currentCompany?.user_role || null;
};

export const useIsCompanyAdmin = () => {
  const { state } = useAuthContext();
  return state.currentCompany?.user_role === 'ADMIN';
};