import React, { useState } from 'react';
import {
  Button,
  Menu,
  MenuItem,
  Typography,
  Box,
  Chip,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Business as BusinessIcon,
  ExpandMore as ExpandMoreIcon,
  Check as CheckIcon,
  AdminPanelSettings as AdminIcon,
  Person as UserIcon,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';
import { Company } from '../../contexts/AuthContext';

const CompanySwitcher: React.FC = () => {
  const { state, switchCompany } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleSwitchCompany = async (company: Company) => {
    if (company.id === state.currentCompany?.id) {
      handleClose();
      return;
    }

    try {
      await switchCompany(company);
      handleClose();
    } catch (error) {
      console.error('Failed to switch company:', error);
      // Could show a toast notification here
    }
  };

  if (!state.currentCompany || state.companies.length === 0) {
    return null;
  }

  return (
    <>
      <Button
        onClick={handleClick}
        variant="outlined"
        endIcon={<ExpandMoreIcon />}
        startIcon={<BusinessIcon />}
        sx={{
          textTransform: 'none',
          color: 'inherit',
          borderColor: 'rgba(255, 255, 255, 0.23)',
          '&:hover': {
            borderColor: 'rgba(255, 255, 255, 0.5)',
          },
        }}
      >
        <Box display="flex" flexDirection="column" alignItems="flex-start">
          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
            {state.currentCompany.name}
          </Typography>
          <Box display="flex" alignItems="center" gap={0.5}>
            <Chip
              icon={state.currentCompany.user_role === 'ADMIN' ? <AdminIcon /> : <UserIcon />}
              label={state.currentCompany.user_role === 'ADMIN' ? 'Admin' : 'User'}
              size="small"
              color={state.currentCompany.user_role === 'ADMIN' ? 'warning' : 'info'}
              sx={{ height: 20, '& .MuiChip-label': { fontSize: '0.75rem' } }}
            />
          </Box>
        </Box>
      </Button>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        MenuListProps={{
          'aria-labelledby': 'company-switcher-button',
        }}
        PaperProps={{
          sx: {
            minWidth: 300,
            maxWidth: 400,
          },
        }}
      >
        <Typography variant="subtitle2" sx={{ px: 2, py: 1, color: 'text.secondary' }}>
          Válasszon céget
        </Typography>
        <Divider />

        {state.companies.map((company) => (
          <MenuItem
            key={company.id}
            onClick={() => handleSwitchCompany(company)}
            selected={company.id === state.currentCompany?.id}
            sx={{ py: 1.5 }}
          >
            <ListItemIcon>
              {company.id === state.currentCompany?.id ? (
                <CheckIcon color="primary" />
              ) : (
                <BusinessIcon />
              )}
            </ListItemIcon>
            <ListItemText>
              <Box>
                <Typography variant="body1" noWrap>
                  {company.name}
                </Typography>
                <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                  <Typography variant="caption" color="text.secondary">
                    {company.tax_id}
                  </Typography>
                  <Chip
                    icon={company.user_role === 'ADMIN' ? <AdminIcon /> : <UserIcon />}
                    label={company.user_role === 'ADMIN' ? 'Admin' : 'User'}
                    size="small"
                    color={company.user_role === 'ADMIN' ? 'warning' : 'info'}
                    sx={{ height: 18, '& .MuiChip-label': { fontSize: '0.7rem' } }}
                  />
                </Box>
              </Box>
            </ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </>
  );
};

export default CompanySwitcher;
