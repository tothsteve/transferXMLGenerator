import React, { useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  IconButton, 
  Typography, 
  Box, 
  useTheme, 
  useMediaQuery,
  Avatar,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip
} from '@mui/material';
import { 
  Menu as MenuIcon,
  Logout,
  Settings,
  Business
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

interface HeaderProps {
  onMenuClick: () => void;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));
  const { state, logout } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const menuOpen = Boolean(anchorEl);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleMenuClose();
  };

  const handleSettings = () => {
    navigate('/settings');
    handleMenuClose();
  };

  const getUserInitials = () => {
    if (!state.user) return 'U';
    const { first_name, last_name } = state.user;
    return `${first_name?.charAt(0) || ''}${last_name?.charAt(0) || ''}`.toUpperCase() || 'U';
  };

  return (
    <AppBar 
      position="sticky" 
      elevation={1}
      sx={{ 
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Toolbar variant="dense">
        {isMobile && (
          <IconButton
            edge="start"
            color="inherit"
            aria-label="open menu"
            onClick={onMenuClick}
            sx={{ mr: 2, color: 'text.primary' }}
          >
            <MenuIcon />
          </IconButton>
        )}

        <Typography 
          variant="h6" 
          sx={{ 
            color: 'text.primary',
            fontWeight: 600,
            mr: 2
          }}
        >
          Transfer Generator
        </Typography>

        <Box sx={{ flexGrow: 1 }} />

        {/* Company Info and Switcher */}
        {state.currentCompany && (
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
            <Chip
              icon={<Business />}
              label={state.currentCompany.name}
              variant="outlined"
              size="small"
              sx={{ mr: 1 }}
            />
          </Box>
        )}

        {/* User Menu */}
        <IconButton
          onClick={handleMenuClick}
          size="small"
          sx={{ ml: 2 }}
          aria-controls={menuOpen ? 'user-menu' : undefined}
          aria-haspopup="true"
          aria-expanded={menuOpen ? 'true' : undefined}
        >
          <Avatar sx={{ bgcolor: 'primary.main', width: 32, height: 32 }}>
            {getUserInitials()}
          </Avatar>
        </IconButton>

        <Menu
          anchorEl={anchorEl}
          id="user-menu"
          open={menuOpen}
          onClose={handleMenuClose}
          onClick={handleMenuClose}
          PaperProps={{
            elevation: 0,
            sx: {
              overflow: 'visible',
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.32))',
              mt: 1.5,
              '& .MuiAvatar-root': {
                width: 32,
                height: 32,
                ml: -0.5,
                mr: 1,
              },
              '&:before': {
                content: '""',
                display: 'block',
                position: 'absolute',
                top: 0,
                right: 14,
                width: 10,
                height: 10,
                bgcolor: 'background.paper',
                transform: 'translateY(-50%) rotate(45deg)',
                zIndex: 0,
              },
            },
          }}
          transformOrigin={{ horizontal: 'right', vertical: 'top' }}
          anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        >
          {/* User Info */}
          <MenuItem disabled>
            <Avatar sx={{ bgcolor: 'primary.main' }}>{getUserInitials()}</Avatar>
            <Box>
              <Typography variant="body2" fontWeight={600}>
                {state.user?.first_name} {state.user?.last_name}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {state.user?.email}
              </Typography>
            </Box>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={handleSettings}>
            <ListItemIcon>
              <Settings fontSize="small" />
            </ListItemIcon>
            <ListItemText>Beállítások</ListItemText>
          </MenuItem>
          
          <Divider />
          
          <MenuItem onClick={handleLogout}>
            <ListItemIcon>
              <Logout fontSize="small" />
            </ListItemIcon>
            <ListItemText>Kijelentkezés</ListItemText>
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
};

export default Header;