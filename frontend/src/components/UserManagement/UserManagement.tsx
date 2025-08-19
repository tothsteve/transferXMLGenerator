import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import {
  PersonAdd as PersonAddIcon,
  Delete as DeleteIcon,
  AdminPanelSettings as AdminIcon,
  Person as UserIcon,
} from '@mui/icons-material';
import { useAuth, useIsCompanyAdmin } from '../../hooks/useAuth';

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

interface InviteUserData {
  email: string;
  role: 'ADMIN' | 'USER';
  message?: string;
}

const UserManagement: React.FC = () => {
  const { state } = useAuth();
  const isAdmin = useIsCompanyAdmin();
  const [users, setUsers] = useState<CompanyUser[]>([]);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviteData, setInviteData] = useState<InviteUserData>({
    email: '',
    role: 'USER',
    message: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock data for demonstration - in real app this would come from API
  React.useEffect(() => {
    if (state.currentCompany) {
      // Mock users data
      setUsers([
        {
          id: 1,
          user: {
            id: 1,
            username: 'admin',
            email: 'admin@company.com',
            first_name: 'Admin',
            last_name: 'User',
          },
          role: 'ADMIN',
          is_active: true,
          joined_at: '2025-01-01T00:00:00Z',
        },
        {
          id: 2,
          user: {
            id: 2,
            username: 'user1',
            email: 'user1@company.com',
            first_name: 'John',
            last_name: 'Doe',
          },
          role: 'USER',
          is_active: true,
          joined_at: '2025-01-15T00:00:00Z',
        },
      ]);
    }
  }, [state.currentCompany]);

  const handleInviteUser = async () => {
    if (!inviteData.email.trim()) {
      setError('E-mail cím kötelező');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // In a real app, this would call the API
      // await userManagementApi.inviteUser({
      //   company_id: state.currentCompany!.id,
      //   email: inviteData.email,
      //   role: inviteData.role,
      //   message: inviteData.message,
      // });
      
      // Mock success
      console.log('Inviting user:', inviteData);
      setInviteDialogOpen(false);
      setInviteData({ email: '', role: 'USER', message: '' });
      
    } catch (error: any) {
      setError(error.message || 'Failed to invite user');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: number, newRole: 'ADMIN' | 'USER') => {
    try {
      // In a real app, this would call the API
      // await userManagementApi.updateUserRole(userId, newRole);
      
      setUsers(prev => prev.map(user => 
        user.id === userId ? { ...user, role: newRole } : user
      ));
    } catch (error: any) {
      setError(error.message || 'Failed to update user role');
    }
  };

  const handleRemoveUser = async (userId: number) => {
    if (!window.confirm('Biztosan el szeretné távolítani ezt a felhasználót?')) {
      return;
    }

    try {
      // In a real app, this would call the API
      // await userManagementApi.removeUser(userId);
      
      setUsers(prev => prev.filter(user => user.id !== userId));
    } catch (error: any) {
      setError(error.message || 'Failed to remove user');
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
        <Button
          variant="contained"
          startIcon={<PersonAddIcon />}
          onClick={() => setInviteDialogOpen(true)}
        >
          Felhasználó meghívása
        </Button>
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
            {users.map((companyUser) => (
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
                      onChange={(e) => handleRoleChange(companyUser.id, e.target.value as 'ADMIN' | 'USER')}
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
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Invite User Dialog */}
      <Dialog open={inviteDialogOpen} onClose={() => setInviteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Felhasználó meghívása</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 1 }}>
            <TextField
              autoFocus
              margin="normal"
              id="email"
              label="E-mail cím"
              type="email"
              fullWidth
              variant="outlined"
              value={inviteData.email}
              onChange={(e) => setInviteData(prev => ({ ...prev, email: e.target.value }))}
              required
            />
            <FormControl fullWidth margin="normal">
              <InputLabel id="role-label">Szerepkör</InputLabel>
              <Select
                labelId="role-label"
                id="role"
                value={inviteData.role}
                label="Szerepkör"
                onChange={(e) => setInviteData(prev => ({ ...prev, role: e.target.value as 'ADMIN' | 'USER' }))}
              >
                <MenuItem value="USER">User</MenuItem>
                <MenuItem value="ADMIN">Admin</MenuItem>
              </Select>
            </FormControl>
            <TextField
              margin="normal"
              id="message"
              label="Üzenet (opcionális)"
              multiline
              rows={3}
              fullWidth
              variant="outlined"
              value={inviteData.message}
              onChange={(e) => setInviteData(prev => ({ ...prev, message: e.target.value }))}
              placeholder="Egyéni üzenet a meghívóhoz..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInviteDialogOpen(false)}>Mégse</Button>
          <Button 
            onClick={handleInviteUser} 
            variant="contained"
            disabled={loading || !inviteData.email.trim()}
          >
            {loading ? 'Küldés...' : 'Meghívó küldése'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default UserManagement;