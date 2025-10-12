import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  IconButton,
  Chip,
  Divider,
} from '@mui/material';
import {
  Close as CloseIcon,
  Home as HomeIcon,
  People as PeopleIcon,
  Description as DescriptionIcon,
  SwapHoriz as SwapHorizIcon,
  Folder as FolderIcon,
  CloudUpload as CloudUploadIcon,
  AdminPanelSettings as AdminIcon,
  Settings as SettingsIcon,
  Receipt as ReceiptIcon,
} from '@mui/icons-material';
import { useIsCompanyAdmin } from '../../hooks/useAuth';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  width: number;
  isMobile: boolean;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  adminOnly?: boolean;
}

const navigation = [
  { name: 'Főoldal', href: '/', icon: HomeIcon },
  { name: 'Kedvezményezettek', href: '/beneficiaries', icon: PeopleIcon },
  { name: 'Sablonok', href: '/templates', icon: DescriptionIcon },
  { name: 'PDF Importálás', href: '/pdf-import', icon: CloudUploadIcon },
  { name: 'Átutalások', href: '/transfers', icon: SwapHorizIcon },
  { name: 'Kötegek kezelése', href: '/batches', icon: FolderIcon },
  { name: 'NAV Számlák', href: '/nav-invoices', icon: ReceiptIcon },
  { name: 'Beállítások', href: '/settings', icon: SettingsIcon },
];

const adminNavigation: NavigationItem[] = [
  { name: 'Felhasználókezelés', href: '/users', icon: AdminIcon },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, width, isMobile }) => {
  const isAdmin = useIsCompanyAdmin();
  const navigate = useNavigate();
  const location = useLocation();

  const handleTransferClick = (e: React.MouseEvent): void => {
    e.preventDefault();

    // If already on transfers page, force a reset by navigating with reset flag
    if (location.pathname === '/transfers') {
      navigate('/transfers', {
        replace: true,
        state: { reset: true, timestamp: Date.now() },
      });
    } else {
      navigate('/transfers');
    }

    if (isMobile) onClose();
  };
  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header with Logo */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          minHeight: 64,
          borderBottom: 1,
          borderColor: 'divider',
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <img
            src="/logo192.png"
            alt="ITCardigan"
            style={{ width: 32, height: 32, borderRadius: '50%' }}
          />
          <Box>
            <Typography variant="h6" component="h1" fontWeight="bold" sx={{ lineHeight: 1.2 }}>
              Transfer Generator
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              by ITCardigan
            </Typography>
          </Box>
        </Box>
        {isMobile && (
          <IconButton onClick={onClose} edge="end">
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ p: 1 }}>
          {navigation.map((item: NavigationItem) => (
            <ListItem key={item.name} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                component={item.href === '/transfers' ? 'div' : NavLink}
                to={item.href === '/transfers' ? undefined : item.href}
                onClick={
                  item.href === '/transfers' ? handleTransferClick : isMobile ? onClose : undefined
                }
                sx={{
                  borderRadius: 1,
                  '&.active': {
                    bgcolor: 'primary.50',
                    color: 'primary.600',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.600',
                    },
                  },
                  '&:hover': {
                    bgcolor: 'grey.50',
                  },
                  ...(item.href === '/transfers' &&
                    location.pathname === '/transfers' && {
                      bgcolor: 'primary.50',
                      color: 'primary.600',
                      '& .MuiListItemIcon-root': {
                        color: 'primary.600',
                      },
                    }),
                }}
              >
                <ListItemIcon sx={{ minWidth: 40 }}>
                  <item.icon />
                </ListItemIcon>
                <ListItemText
                  primary={item.name}
                  primaryTypographyProps={{
                    fontWeight: 600,
                    fontSize: '0.875rem',
                  }}
                />
                {item.badge && (
                  <Chip
                    label={item.badge}
                    size="small"
                    color="primary"
                    variant="filled"
                    sx={{
                      height: 20,
                      fontSize: '0.7rem',
                      fontWeight: 'bold',
                    }}
                  />
                )}
              </ListItemButton>
            </ListItem>
          ))}

          {/* Admin Navigation */}
          {isAdmin && (
            <>
              <Divider sx={{ my: 1 }} />
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ px: 2, py: 1, fontWeight: 600, textTransform: 'uppercase' }}
              >
                Adminisztráció
              </Typography>
              {adminNavigation.map((item) => (
                <ListItem key={item.name} disablePadding sx={{ mb: 0.5 }}>
                  <ListItemButton
                    component={NavLink}
                    to={item.href}
                    onClick={isMobile ? onClose : undefined}
                    sx={{
                      borderRadius: 1,
                      '&.active': {
                        bgcolor: 'warning.50',
                        color: 'warning.600',
                        '& .MuiListItemIcon-root': {
                          color: 'warning.600',
                        },
                      },
                      '&:hover': {
                        bgcolor: 'grey.50',
                      },
                    }}
                  >
                    <ListItemIcon sx={{ minWidth: 40 }}>
                      <item.icon />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.name}
                      primaryTypographyProps={{
                        fontWeight: 600,
                        fontSize: '0.875rem',
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </>
          )}
        </List>
      </Box>
    </Box>
  );

  return (
    <>
      {/* Mobile Drawer */}
      {isMobile ? (
        <Drawer
          anchor="left"
          open={isOpen}
          onClose={onClose}
          ModalProps={{
            keepMounted: true, // Better open performance on mobile.
          }}
          sx={{
            '& .MuiDrawer-paper': {
              width: width,
              boxSizing: 'border-box',
              background:
                'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
              backdropFilter: 'blur(20px)',
              borderRight: '1px solid rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      ) : (
        /* Desktop Drawer */
        <Drawer
          variant="permanent"
          sx={{
            width: width,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: width,
              boxSizing: 'border-box',
              background:
                'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
              backdropFilter: 'blur(20px)',
              borderRight: '1px solid rgba(255, 255, 255, 0.2)',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      )}
    </>
  );
};

export default Sidebar;
