import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  IconButton,
  Chip,
  Stack,
  Skeleton,
  Avatar,
  Divider,
  alpha
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Visibility as ViewIcon,
  CalendarToday as CalendarIcon,
  Group as GroupIcon,
  Description as TemplateIcon
} from '@mui/icons-material';
import { TransferTemplate } from '../../types/api';
import { usePermissions } from '../../hooks/usePermissions';

interface TemplateListProps {
  templates: TransferTemplate[];
  isLoading: boolean;
  onEdit: (template: TransferTemplate) => void;
  onDelete: (id: number) => void;
  onView: (template: TransferTemplate) => void;
  onLoadTemplate: (id: number) => void;
}

const TemplateList: React.FC<TemplateListProps> = ({
  templates,
  isLoading,
  onEdit,
  onDelete,
  onView,
  onLoadTemplate,
}) => {
  const permissions = usePermissions();
  
  if (isLoading) {
    return (
      <Box 
        sx={{ 
          display: 'grid',
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, 1fr)',
            lg: 'repeat(3, 1fr)'
          },
          gap: 3
        }}
      >
        {[...Array(6)].map((_, i) => (
          <Card key={i} elevation={1}>
            <CardContent>
              <Skeleton variant="text" width="75%" height={24} />
              <Skeleton variant="text" width="50%" height={20} sx={{ mb: 2 }} />
              <Stack spacing={1}>
                <Skeleton variant="text" width="100%" height={16} />
                <Skeleton variant="text" width="67%" height={16} />
              </Stack>
            </CardContent>
            <CardActions>
              <Skeleton variant="rectangular" width={80} height={32} />
              <Skeleton variant="rectangular" width={64} height={32} />
            </CardActions>
          </Card>
        ))}
      </Box>
    );
  }

  if (templates.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <TemplateIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
        <Typography variant="h6" color="text.primary" gutterBottom>
          Nincsenek sablonok
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Kezdjen el egy új sablon létrehozásával.
        </Typography>
      </Box>
    );
  }

  return (
    <Box 
      sx={{ 
        display: 'grid',
        gridTemplateColumns: {
          xs: '1fr',
          sm: 'repeat(2, 1fr)',
          lg: 'repeat(3, 1fr)'
        },
        gap: 3
      }}
    >
      {templates.map((template) => (
        <Card 
          key={template.id} 
          elevation={2}
          sx={{ 
            background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
            backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255, 255, 255, 0.3)',
            borderRadius: 3,
            transition: 'all 0.3s ease-in-out',
            '&:hover': { 
              boxShadow: '0 12px 32px rgba(0, 0, 0, 0.15)',
              transform: 'translateY(-4px)',
              border: '1px solid rgba(37, 99, 235, 0.2)'
            }
          }}
        >
          <CardContent>
            {/* Header with Avatar and Status */}
            <Stack direction="row" alignItems="flex-start" spacing={2} sx={{ mb: 2 }}>
              <Avatar 
                sx={{ 
                  width: 48, 
                  height: 48,
                  background: template.is_active 
                    ? 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)'
                    : 'linear-gradient(135deg, #64748b 0%, #94a3b8 100%)',
                  mt: 0.5
                }}
              >
                <TemplateIcon />
              </Avatar>
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                  <Typography variant="h6" component="h3" noWrap fontWeight={700} sx={{ color: 'text.primary' }}>
                    {template.name}
                  </Typography>
                  <Chip
                    label={template.is_active ? 'Aktív' : 'Inaktív'}
                    size="small"
                    color={template.is_active ? 'success' : 'default'}
                    variant="outlined"
                    sx={{ 
                      minWidth: 'fit-content',
                      borderWidth: 2,
                      fontWeight: 600
                    }}
                  />
                </Stack>
                {template.description && (
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                      lineHeight: 1.4
                    }}
                  >
                    {template.description}
                  </Typography>
                )}
              </Box>
            </Stack>

            {/* Divider */}
            <Divider sx={{ my: 2, borderColor: alpha('#000', 0.05) }} />
            
            {/* Metadata */}
            <Stack direction="row" spacing={3} sx={{ mb: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Avatar sx={{ width: 24, height: 24, bgcolor: 'secondary.main', background: 'linear-gradient(135deg, #0891b2 0%, #06b6d4 100%)' }}>
                  <GroupIcon sx={{ fontSize: 14 }} />
                </Avatar>
                <Typography variant="body2" color="text.primary" fontWeight={500}>
                  {template.beneficiary_count}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  kedvezményezett
                </Typography>
              </Stack>
              <Stack direction="row" alignItems="center" spacing={1}>
                <Avatar sx={{ width: 24, height: 24, bgcolor: 'primary.main', background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)' }}>
                  <CalendarIcon sx={{ fontSize: 14 }} />
                </Avatar>
                <Typography variant="caption" color="text.secondary" fontWeight={500}>
                  {new Date(template.created_at).toLocaleDateString('hu-HU')}
                </Typography>
              </Stack>
            </Stack>
            
            {template.updated_at !== template.created_at && (
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Utoljára módosítva: {new Date(template.updated_at).toLocaleDateString('hu-HU')}
                </Typography>
              </Stack>
            )}

          </CardContent>
          <CardActions sx={{ p: 3, pt: 0 }}>
            {permissions.canManageTransfers ? (
              <Button
                variant="contained"
                startIcon={<PlayIcon />}
                onClick={() => onLoadTemplate(template.id)}
                disabled={!template.is_active}
                sx={{ 
                  flex: 1,
                  borderRadius: 2,
                  background: template.is_active 
                    ? 'linear-gradient(135deg, #059669 0%, #10b981 100%)'
                    : 'linear-gradient(135deg, #9ca3af 0%, #d1d5db 100%)',
                  boxShadow: template.is_active 
                    ? '0 4px 12px rgba(5, 150, 105, 0.3)'
                    : 'none',
                  color: template.is_active ? 'white' : '#6b7280',
                  '&:hover': template.is_active ? {
                    background: 'linear-gradient(135deg, #047857 0%, #059669 100%)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 6px 16px rgba(5, 150, 105, 0.4)',
                  } : {},
                  '&:disabled': {
                    background: 'linear-gradient(135deg, #9ca3af 0%, #d1d5db 100%)',
                    color: '#9ca3af',
                    cursor: 'not-allowed'
                  }
                }}
              >
                {template.is_active ? 'Betöltés' : 'Inaktív'}
              </Button>
            ) : (
              <Button
                variant="outlined"
                disabled
                sx={{ 
                  flex: 1,
                  borderRadius: 2,
                  color: '#9ca3af',
                  borderColor: '#d1d5db',
                  cursor: 'not-allowed'
                }}
              >
                Csak megtekintés
              </Button>
            )}
            <Stack direction="row" spacing={0.5}>
              <IconButton
                onClick={() => onView(template)}
                size="small"
                title="Megtekintés"
                sx={{
                  bgcolor: alpha('#2563eb', 0.1),
                  color: 'primary.main',
                  '&:hover': {
                    bgcolor: alpha('#2563eb', 0.2),
                    transform: 'scale(1.05)',
                  }
                }}
              >
                <ViewIcon fontSize="small" />
              </IconButton>
              {permissions.canManageTemplates && (
                <>
                  <IconButton
                    onClick={() => onEdit(template)}
                    size="small"
                    title="Szerkesztés"
                    sx={{
                      bgcolor: alpha('#d97706', 0.1),
                      color: 'warning.main',
                      '&:hover': {
                        bgcolor: alpha('#d97706', 0.2),
                        transform: 'scale(1.05)',
                      }
                    }}
                  >
                    <EditIcon fontSize="small" />
                  </IconButton>
                  <IconButton
                    onClick={() => onDelete(template.id)}
                    size="small"
                    title="Törlés"
                    sx={{
                      bgcolor: alpha('#dc2626', 0.1),
                      color: 'error.main',
                      '&:hover': {
                        bgcolor: alpha('#dc2626', 0.2),
                        transform: 'scale(1.05)',
                      }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </>
              )}
            </Stack>
          </CardActions>
        </Card>
      ))}
    </Box>
  );
};

export default TemplateList;