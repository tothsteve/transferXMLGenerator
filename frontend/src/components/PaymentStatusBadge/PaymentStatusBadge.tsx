import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import {
  Schedule as ScheduleIcon, 
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Help as HelpIcon,
  Upload as UploadIcon
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
  compact?: boolean; // New prop for compact display
}

const PaymentStatusBadge: React.FC<PaymentStatusBadgeProps> = ({ 
  paymentStatus, 
  paymentStatusDate,
  size = 'small',
  compact = false
}) => {
  const getIcon = (iconName: string) => {
    const iconProps = { fontSize: size === 'small' ? 'small' : 'medium' as any };
    
    switch (iconName) {
      case 'schedule':
        return <ScheduleIcon {...iconProps} />;
      case 'assignment':
        return <AssignmentIcon {...iconProps} />;
      case 'upload':
        return <UploadIcon {...iconProps} />;
      case 'check_circle':
        return <CheckCircleIcon {...iconProps} />;
      default:
        return <HelpIcon {...iconProps} />;
    }
  };

  const getColor = (status: string) => {
    switch (status) {
      case 'UNPAID':
        return 'error';      // Red - needs payment
      case 'PREPARED':
        return 'info';       // Blue - prepared in system
      case 'PAID_MANUAL':
        return 'success';    // Green - manually paid  
      case 'PAID_SYSTEM':
        return 'info';       // Blue - paid through system
      case 'PAID_TRUSTED':
        return 'secondary';  // Purple - trusted partner auto-paid
      default:
        return 'default';
    }
  };

  const getTooltip = (status: string) => {
    const baseLabel = paymentStatus.label;
    const dateText = paymentStatusDate ? ` (${paymentStatusDate})` : '';
    
    const descriptions = {
      'UNPAID': 'Számla még nincs kifizetve',
      'PREPARED': 'Átutalás létrehozva, de még bankba nincs átadva', 
      'PAID_MANUAL': 'Manuálisan fizetettnek jelölve',
      'PAID_SYSTEM': 'Rendszerben kifizetés legenerálva, bankba átadva',
      'PAID_TRUSTED': 'Automatikusan fizetettnek jelölve'
    };
    
    const description = descriptions[status as keyof typeof descriptions] || baseLabel;
    
    return compact 
      ? `${baseLabel}${dateText}\n\n${description}`
      : description;
  };

  // Create display label with date if available and status needs it
  const getDisplayLabel = () => {
    const baseLabel = paymentStatus.label;
    if (paymentStatusDate && ['PREPARED', 'PAID_MANUAL', 'PAID_SYSTEM', 'PAID_TRUSTED'].includes(paymentStatus.status)) {
      return `${baseLabel} (${paymentStatusDate})`;
    }
    return baseLabel;
  };

  if (compact) {
    // Compact mode: Just icon with colors and detailed tooltip
    const getIconColor = (status: string) => {
      switch (status) {
        case 'UNPAID':
          return '#f44336'; // Red
        case 'PREPARED':
          return '#2196f3'; // Blue
        case 'PAID_MANUAL':
          return '#4caf50'; // Light Green - Manual work/effort
        case 'PAID_SYSTEM':
          return '#1976d2'; // Blue - Cold/digital system
        case 'PAID_TRUSTED':
          return '#2e7d32'; // Dark Green - Trusted/premium
        default:
          return '#757575'; // Gray
      }
    };

    return (
      <Tooltip title={getTooltip(paymentStatus.status)} arrow>
        <span
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            cursor: 'help',
            color: getIconColor(paymentStatus.status)
          }}
        >
          {getIcon(paymentStatus.icon)}
        </span>
      </Tooltip>
    );
  }

  // Full mode: Chip with icon and label
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