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
  Skeleton
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
          elevation={1}
          sx={{ 
            transition: 'box-shadow 0.2s',
            '&:hover': { boxShadow: 4 }
          }}
        >
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={2}>
              <Box sx={{ minWidth: 0, flex: 1 }}>
                <Typography variant="h6" component="h3" noWrap gutterBottom>
                  {template.name}
                </Typography>
                {template.description && (
                  <Typography 
                    variant="body2" 
                    color="text.secondary" 
                    sx={{ 
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}
                  >
                    {template.description}
                  </Typography>
                )}
              </Box>
              <Chip
                label={template.is_active ? 'Aktív' : 'Inaktív'}
                size="small"
                color={template.is_active ? 'success' : 'default'}
                variant="outlined"
              />
            </Stack>

            <Stack spacing={1} sx={{ mt: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1}>
                <GroupIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  {template.beneficiary_count} kedvezményezett
                </Typography>
              </Stack>
              <Stack direction="row" alignItems="center" spacing={1}>
                <CalendarIcon fontSize="small" color="action" />
                <Typography variant="body2" color="text.secondary">
                  Létrehozva: {new Date(template.created_at).toLocaleDateString('hu-HU')}
                </Typography>
              </Stack>
              {template.updated_at !== template.created_at && (
                <Stack direction="row" alignItems="center" spacing={1}>
                  <CalendarIcon fontSize="small" color="action" />
                  <Typography variant="body2" color="text.secondary">
                    Módosítva: {new Date(template.updated_at).toLocaleDateString('hu-HU')}
                  </Typography>
                </Stack>
              )}
            </Stack>

          </CardContent>
          <CardActions>
            <Button
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={() => onLoadTemplate(template.id)}
              sx={{ flex: 1 }}
            >
              Betöltés
            </Button>
            <Stack direction="row" spacing={0.5}>
              <IconButton
                onClick={() => onView(template)}
                size="small"
                title="Megtekintés"
              >
                <ViewIcon fontSize="small" />
              </IconButton>
              <IconButton
                onClick={() => onEdit(template)}
                size="small"
                title="Szerkesztés"
                color="primary"
              >
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton
                onClick={() => onDelete(template.id)}
                size="small"
                title="Törlés"
                color="error"
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Stack>
          </CardActions>
        </Card>
      ))}
    </Box>
  );
};

export default TemplateList;