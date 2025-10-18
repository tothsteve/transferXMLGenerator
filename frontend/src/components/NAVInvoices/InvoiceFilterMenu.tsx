import React from 'react';
import {
  Menu,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Divider,
} from '@mui/material';

interface InvoiceFilterMenuProps {
  anchorEl: HTMLElement | null;
  open: boolean;
  onClose: () => void;
  directionFilter: string;
  setDirectionFilter: (value: string) => void;
  paymentStatusFilter: string;
  setPaymentStatusFilter: (value: string) => void;
  hideStornoInvoices: boolean;
  setHideStornoInvoices: (value: boolean) => void;
  clearFilters: () => void;
}

const InvoiceFilterMenu: React.FC<InvoiceFilterMenuProps> = ({
  anchorEl,
  open,
  onClose,
  directionFilter,
  setDirectionFilter,
  paymentStatusFilter,
  setPaymentStatusFilter,
  hideStornoInvoices,
  setHideStornoInvoices,
  clearFilters,
}) => {
  return (
    <Menu
      anchorEl={anchorEl}
      open={open}
      onClose={onClose}
      anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      transformOrigin={{ vertical: 'top', horizontal: 'right' }}
    >
      <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(directionFilter === 'INBOUND')}
              onChange={(e) => setDirectionFilter(e.target.checked ? 'INBOUND' : '')}
              size="small"
            />
          }
          label="Csak bejövő számlák"
          sx={{ m: 0 }}
        />
      </MenuItem>
      <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(directionFilter === 'OUTBOUND')}
              onChange={(e) => setDirectionFilter(e.target.checked ? 'OUTBOUND' : '')}
              size="small"
            />
          }
          label="Csak kimenő számlák"
          sx={{ m: 0 }}
        />
      </MenuItem>
      <Divider />
      <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(paymentStatusFilter === 'UNPAID')}
              onChange={(e) => setPaymentStatusFilter(e.target.checked ? 'UNPAID' : '')}
              size="small"
            />
          }
          label="Csak fizetésre váró"
          sx={{ m: 0 }}
        />
      </MenuItem>
      <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(paymentStatusFilter === 'PREPARED')}
              onChange={(e) => setPaymentStatusFilter(e.target.checked ? 'PREPARED' : '')}
              size="small"
            />
          }
          label="Csak előkészített"
          sx={{ m: 0 }}
        />
      </MenuItem>
      <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(paymentStatusFilter === 'PAID')}
              onChange={(e) => setPaymentStatusFilter(e.target.checked ? 'PAID' : '')}
              size="small"
            />
          }
          label="Csak kifizetett"
          sx={{ m: 0 }}
        />
      </MenuItem>
      <Divider />
      <MenuItem disableRipple sx={{ '&:hover': { backgroundColor: 'transparent' } }}>
        <FormControlLabel
          control={
            <Checkbox
              checked={Boolean(hideStornoInvoices)}
              onChange={(e) => setHideStornoInvoices(e.target.checked)}
              size="small"
            />
          }
          label="Sztornózott számlák elrejtése"
          sx={{ m: 0 }}
        />
      </MenuItem>
      <Divider />
      <MenuItem
        onClick={() => {
          clearFilters();
          onClose();
        }}
      >
        Szűrők törlése
      </MenuItem>
    </Menu>
  );
};

export default InvoiceFilterMenu;
