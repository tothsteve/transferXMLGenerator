import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Paper,
  Stack,
  Chip,
  Skeleton,
  Avatar,
} from '@mui/material';
import {
  People as PeopleIcon,
  Description as DescriptionIcon,
  SwapHoriz as SwapHorizIcon,
  TrendingUp as TrendingUpIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useBeneficiaries, useTemplates, useBatches } from '../../hooks/api';

// Animated counter hook
const useAnimatedCounter = (end: number, duration: number = 1000, start: number = 0) => {
  const [count, setCount] = useState(start);

  useEffect(() => {
    if (end === 0) return;

    const increment = end / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
      current += increment;
      if (current >= end) {
        setCount(end);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, 16);

    return () => clearInterval(timer);
  }, [end, duration, start]);

  return count;
};

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: 'primary' | 'secondary' | 'success' | 'warning';
  trend?: string;
  isLoading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon: Icon,
  color,
  trend,
  isLoading,
}) => {
  const numericValue = typeof value === 'number' ? value : parseInt(value.toString()) || 0;
  const animatedValue = useAnimatedCounter(numericValue, 800);

  if (isLoading) {
    return (
      <Card elevation={1}>
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Stack spacing={1} sx={{ flex: 1 }}>
              <Skeleton variant="text" width="60%" height={20} />
              <Skeleton variant="text" width="40%" height={40} />
              <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 2 }} />
            </Stack>
            <Skeleton variant="circular" width={56} height={56} />
          </Stack>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      elevation={1}
      sx={{
        background:
          color === 'primary' ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : undefined,
        color: color === 'primary' ? 'white' : undefined,
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 20px -4px rgba(0, 0, 0, 0.15)',
        },
      }}
    >
      <CardContent sx={{ p: 3 }}>
        <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
          <Stack spacing={1}>
            <Typography
              variant="body2"
              sx={{
                color: color === 'primary' ? 'rgba(255,255,255,0.8)' : 'text.secondary',
                fontWeight: 500,
              }}
            >
              {title}
            </Typography>
            <Typography variant="h4" fontWeight="bold">
              {typeof value === 'number' ? animatedValue.toLocaleString('hu-HU') : value}
            </Typography>
            {trend && (
              <Chip
                label={trend}
                size="small"
                color={color === 'primary' ? 'secondary' : 'success'}
                icon={<TrendingUpIcon />}
                sx={{
                  fontWeight: 500,
                  '& .MuiChip-icon': {
                    fontSize: '16px',
                  },
                }}
              />
            )}
          </Stack>
          <Avatar
            sx={{
              bgcolor: color === 'primary' ? 'rgba(255,255,255,0.2)' : `${color}.main`,
              width: 56,
              height: 56,
              transition: 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                transform: 'scale(1.1)',
              },
            }}
          >
            <Icon fontSize="large" />
          </Avatar>
        </Stack>
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: beneficiariesData, isLoading: beneficiariesLoading } = useBeneficiaries();
  const { data: templatesData, isLoading: templatesLoading } = useTemplates();
  const { data: batchesData, isLoading: batchesLoading } = useBatches();

  const totalBeneficiaries = beneficiariesData?.count || 0;
  const totalTemplates = templatesData?.count || 0;
  const activeBeneficiaries = beneficiariesData?.results?.filter((b) => b.is_active)?.length || 0;
  const frequentBeneficiaries =
    beneficiariesData?.results?.filter((b) => b.is_frequent)?.length || 0;
  const totalBatches = batchesData?.count || 0;

  const isLoading = beneficiariesLoading || templatesLoading || batchesLoading;

  const quickActions = [
    {
      title: 'Új kedvezményezett',
      description: 'Kedvezményezett hozzáadása a rendszerhez',
      action: () => navigate('/beneficiaries'),
      color: 'primary' as const,
      icon: PeopleIcon,
    },
    {
      title: 'Új sablon',
      description: 'Átutalási sablon létrehozása',
      action: () => navigate('/templates'),
      color: 'secondary' as const,
      icon: DescriptionIcon,
    },
    {
      title: 'Átutalás indítása',
      description: 'Új átutalási folyamat kezdeményezése',
      action: () => navigate('/transfers'),
      color: 'success' as const,
      icon: SwapHorizIcon,
    },
  ];

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold">
          Főoldal
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Üdvözöljük a Transfer XML Generator rendszerben
        </Typography>
      </Box>

      {/* Statistics Cards */}
      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            md: 'repeat(4, 1fr)',
          },
          gap: 3,
          mb: 4,
        }}
      >
        <StatCard
          title="Összes kedvezményezett"
          value={totalBeneficiaries}
          icon={PeopleIcon}
          color="primary"
          {...(activeBeneficiaries > 0 && { trend: `${activeBeneficiaries} aktív` })}
          isLoading={isLoading}
        />
        <StatCard
          title="Gyakori kedvezményezettek"
          value={frequentBeneficiaries}
          icon={PeopleIcon}
          color="secondary"
          isLoading={isLoading}
        />
        <StatCard
          title="Sablonok száma"
          value={totalTemplates}
          icon={DescriptionIcon}
          color="success"
          isLoading={isLoading}
        />
        <StatCard
          title="Generált XML-ek"
          value={totalBatches}
          icon={SwapHorizIcon}
          color="warning"
          isLoading={isLoading}
        />
      </Box>

      {/* Quick Actions */}
      <Paper elevation={1} sx={{ p: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom fontWeight="600">
          Gyors műveletek
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          A leggyakrabban használt funkciók gyors elérése
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
            },
            gap: 3,
          }}
        >
          {quickActions.map((action, index) => (
            <Card
              key={index}
              elevation={0}
              sx={{
                border: 1,
                borderColor: 'divider',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  borderColor: `${action.color}.main`,
                  transform: 'translateY(-2px)',
                  boxShadow: 2,
                },
              }}
              onClick={action.action}
            >
              <CardContent sx={{ textAlign: 'center', py: 4 }}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    bgcolor: `${action.color}.50`,
                    color: `${action.color}.600`,
                    display: 'inline-flex',
                    mb: 2,
                  }}
                >
                  <action.icon fontSize="large" />
                </Box>
                <Typography variant="h6" component="h3" gutterBottom fontWeight="600">
                  {action.title}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                  {action.description}
                </Typography>
                <Button
                  variant="contained"
                  color={action.color}
                  size="small"
                  sx={{ minWidth: 120 }}
                >
                  Indítás
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Paper>

      {/* Recent Activity Placeholder */}
      <Paper elevation={1} sx={{ p: 3, mt: 4 }}>
        <Typography variant="h5" component="h2" gutterBottom fontWeight="600">
          Legutóbbi tevékenységek
        </Typography>
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body2" color="text.secondary">
            Itt jelennek meg a legutóbbi átutalások és műveletek
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default Dashboard;
