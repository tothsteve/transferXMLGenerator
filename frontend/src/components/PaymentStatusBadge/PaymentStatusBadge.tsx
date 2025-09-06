import React from 'react';
import { Chip, Tooltip, Box } from '@mui/material';
import {
  Pending as PendingIcon,
  Schedule as ScheduleIcon, 
  Done as DoneIcon,
  AccountBalance as AccountBalanceIcon,
  Verified as VerifiedIcon,
  Help as HelpIcon
} from '@mui/icons-material';

interface PaymentStatus {
  status: string;
  label: string;
  icon: string;
  class: string;
}

interface PaymentStatusBadgeProps {
  paymentStatus: PaymentStatus;
  paymentStatusDate?: string;
  size?: 'small' | 'medium';
}

const PaymentStatusBadge: React.FC<PaymentStatusBadgeProps> = ({ 
  paymentStatus, 
  paymentStatusDate,
  size = 'small' 
}) => {
  const getIcon = (iconName: string) => {
    const iconProps = { fontSize: size === 'small' ? 'small' : 'medium' as any };
    
    switch (iconName) {
      case 'pending':
        return <PendingIcon {...iconProps} />;
      case 'schedule':
        return <ScheduleIcon {...iconProps} />;
      case 'done':
        return <DoneIcon {...iconProps} />;
      case 'account_balance':
        return <AccountBalanceIcon {...iconProps} />;
      case 'verified':
        return <VerifiedIcon {...iconProps} />;
      default:
        return <HelpIcon {...iconProps} />;
    }
  };

  const getColor = (status: string) => {
    switch (status) {
      case 'UNPAID':
        return 'error';
      case 'PREPARED':
        return 'warning';
      case 'PAID_MANUAL':
        return 'success';
      case 'PAID_SYSTEM':
        return 'info';
      case 'PAID_TRUSTED':
        return 'secondary';
      default:
        return 'default';
    }
  };

  const getTooltip = (status: string) => {
    switch (status) {
      case 'UNPAID':
        return 'Számla még nincs kifizetve';
      case 'PREPARED':
        return 'Átutalás létrehozva, de még bankba nincs átadva';
      case 'PAID_MANUAL':
        return 'Manuálisan fizetettnek jelölve';
      case 'PAID_SYSTEM':
        return 'Rendszerben kifizetés legenerálva, bankba átadva';
      case 'PAID_TRUSTED':
        return 'Automatikusan fizetettnek jelölve (megbízható partner)';
      default:
        return paymentStatus.label;
    }
  };

  // Create display label with date if available and status needs it
  const getDisplayLabel = () => {
    const baseLabel = paymentStatus.label;
    if (paymentStatusDate && ['PREPARED', 'PAID_MANUAL', 'PAID_SYSTEM', 'PAID_TRUSTED'].includes(paymentStatus.status)) {
      return `${baseLabel} (${paymentStatusDate})`;
    }
    return baseLabel;
  };

  return (
    <Tooltip title={getTooltip(paymentStatus.status)} arrow>
      <Chip
        icon={getIcon(paymentStatus.icon)}
        label={getDisplayLabel()}
        color={getColor(paymentStatus.status) as any}
        size={size}
        variant="filled"
        sx={{
          fontWeight: 500,
          '& .MuiChip-icon': {
            marginLeft: '8px'
          },
          // Special styling for system payments
          ...(paymentStatus.status === 'PAID_SYSTEM' && {
            backgroundColor: '#1976d2',
            '& .MuiChip-icon': {
              color: '#fff'
            }
          }),
          // Special styling for trusted partner payments  
          ...(paymentStatus.status === 'PAID_TRUSTED' && {
            backgroundColor: '#9c27b0',
            '& .MuiChip-icon': {
              color: '#fff'
            }
          })
        }}
      />
    </Tooltip>
  );
};

export default PaymentStatusBadge;