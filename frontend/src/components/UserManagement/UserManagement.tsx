import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  FormControl,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  AdminPanelSettings as AdminIcon,
  Person as UserIcon,
} from '@mui/icons-material';
import { useAuth, useIsCompanyAdmin } from '../../hooks/useAuth';
import { userManagementApi } from '../../services/api';
import { getErrorMessage } from '../../utils/errorTypeGuards';

interface CompanyUser {
  id: number;
  user: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  role: 'ADMIN' | 'USER';
  is_active: boolean;
  joined_at: string;
}

const UserManagement: React.FC = () => {
  const { state } = useAuth();
  const isAdmin = useIsCompanyAdmin();
  const [users, setUsers] = useState<CompanyUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load company users from API
  React.useEffect(() => {
    if (state.currentCompany) {
      void loadUsers();
    }
  }, [state.currentCompany]);

  const loadUsers = async (): Promise<void> => {
    setLoading(true);
    try {
      const response = await userManagementApi.getCompanyUsers();
      setUsers(response.data);
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Nem sikerült betölteni a felhasználókat'));
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: number, newRole: 'ADMIN' | 'USER'): Promise<void> => {
    try {
      await userManagementApi.updateUserRole(userId, newRole);
      setUsers((prev) =>
        prev.map((user) => (user.id === userId ? { ...user, role: newRole } : user))
      );
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Nem sikerült frissíteni a felhasználó szerepkörét'));
    }
  };

  const handleRemoveUser = async (userId: number): Promise<void> => {
    if (!window.confirm('Biztosan el szeretné távolítani ezt a felhasználót?')) {
      return;
    }

    try {
      await userManagementApi.removeUser(userId);
      setUsers((prev) => prev.filter((user) => user.id !== userId));
    } catch (error: unknown) {
      setError(getErrorMessage(error, 'Nem sikerült eltávolítani a felhasználót'));
    }
  };

  if (!isAdmin) {
    return (
      <Box p={3}>
        <Alert severity="warning">
          Csak adminisztrátorok férhetnek hozzá a felhasználókezeléshez.
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Felhasználókezelés
        </Typography>
      </Box>

      {state.currentCompany && (
        <Paper sx={{ mb: 3, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {state.currentCompany.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Adószám: {state.currentCompany.tax_id}
          </Typography>
        </Paper>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Név</TableCell>
              <TableCell>E-mail</TableCell>
              <TableCell>Felhasználónév</TableCell>
              <TableCell>Szerepkör</TableCell>
              <TableCell>Státusz</TableCell>
              <TableCell>Csatlakozott</TableCell>
              <TableCell align="center">Műveletek</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Betöltés...
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  Nincsenek felhasználók
                </TableCell>
              </TableRow>
            ) : (
              users.map((companyUser) => (
                <TableRow key={companyUser.id}>
                  <TableCell>
                    {companyUser.user.first_name} {companyUser.user.last_name}
                  </TableCell>
                  <TableCell>{companyUser.user.email}</TableCell>
                  <TableCell>{companyUser.user.username}</TableCell>
                  <TableCell>
                    <Chip
                      icon={companyUser.role === 'ADMIN' ? <AdminIcon /> : <UserIcon />}
                      label={companyUser.role === 'ADMIN' ? 'Admin' : 'User'}
                      color={companyUser.role === 'ADMIN' ? 'warning' : 'info'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={companyUser.is_active ? 'Aktív' : 'Inaktív'}
                      color={companyUser.is_active ? 'success' : 'default'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {new Date(companyUser.joined_at).toLocaleDateString('hu-HU')}
                  </TableCell>
                  <TableCell align="center">
                    <FormControl size="small" sx={{ minWidth: 80, mr: 1 }}>
                      <Select
                        value={companyUser.role}
                        onChange={(e) =>
                          handleRoleChange(companyUser.id, e.target.value as 'ADMIN' | 'USER')
                        }
                        disabled={companyUser.user.id === state.user?.id} // Can't change own role
                      >
                        <MenuItem value="USER">User</MenuItem>
                        <MenuItem value="ADMIN">Admin</MenuItem>
                      </Select>
                    </FormControl>
                    <IconButton
                      color="error"
                      onClick={() => handleRemoveUser(companyUser.id)}
                      disabled={companyUser.user.id === state.user?.id} // Can't remove self
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};

export default UserManagement;
