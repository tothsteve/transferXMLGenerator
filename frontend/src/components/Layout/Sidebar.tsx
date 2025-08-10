import React from 'react';
import { NavLink } from 'react-router-dom';
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
} from '@mui/material';
import {
  Close as CloseIcon,
  Home as HomeIcon,
  People as PeopleIcon,
  Description as DescriptionIcon,
  SwapHoriz as SwapHorizIcon,
} from '@mui/icons-material';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  width: number;
  isMobile: boolean;
}

const navigation = [
  { name: 'Főoldal', href: '/', icon: HomeIcon },
  { name: 'Kedvezményezettek', href: '/beneficiaries', icon: PeopleIcon },
  { name: 'Sablonok', href: '/templates', icon: DescriptionIcon },
  { name: 'Átutalások', href: '/transfers', icon: SwapHorizIcon },
];

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, width, isMobile }) => {
  const drawerContent = (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
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
        <Typography variant="h6" component="h1" fontWeight="bold">
          Transfer XML Generator
        </Typography>
        {isMobile && (
          <IconButton onClick={onClose} edge="end">
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      {/* Navigation */}
      <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
        <List sx={{ p: 1 }}>
          {navigation.map((item) => (
            <ListItem key={item.name} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                component={NavLink}
                to={item.href}
                onClick={isMobile ? onClose : undefined}
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