import React from 'react';
import {
  Paper,
  Typography,
  Box,
  Stack,
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
  Chip,
} from '@mui/material';
import { Description as TemplateIcon } from '@mui/icons-material';
import { TransferTemplate } from '../../types/api';

interface TemplateSelectorProps {
  templates: TransferTemplate[];
  selectedTemplate: TransferTemplate | null;
  onSelectTemplate: (template: TransferTemplate) => void;
  onLoadTemplate: (templateId: number) => void;
  isLoading?: boolean;
}

const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  selectedTemplate,
  onSelectTemplate,
  onLoadTemplate,
  isLoading = false,
}) => {
  const activeTemplates = templates.filter((t) => t.is_active);

  const handleSelectChange = (event: SelectChangeEvent<number>): void => {
    const templateId = event.target.value as number;
    const template = activeTemplates.find((t) => t.id === templateId);
    if (template) {
      onSelectTemplate(template);
      // Automatically load the template when selected
      onLoadTemplate(templateId);
    }
  };

  return (
    <Paper elevation={1} sx={{ p: 3 }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 3 }}>
        <TemplateIcon color="primary" />
        <Typography variant="h6">Sablon kiválasztása</Typography>
        {isLoading && (
          <Typography variant="body2" color="primary" sx={{ ml: 2 }}>
            Betöltés...
          </Typography>
        )}
      </Stack>

      {activeTemplates.length === 0 ? (
        <Box
          sx={{
            textAlign: 'center',
            py: 4,
            border: 2,
            borderStyle: 'dashed',
            borderColor: 'divider',
            borderRadius: 1,
          }}
        >
          <TemplateIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
          <Typography variant="h6" gutterBottom>
            Nincsenek aktív sablonok
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Hozzon létre egy új sablont a Sablonok menüpontban.
          </Typography>
        </Box>
      ) : (
        <FormControl fullWidth>
          <Select
            value={selectedTemplate?.id || ''}
            onChange={handleSelectChange}
            displayEmpty
            renderValue={(selected) => {
              if (!selected) {
                return <Typography color="text.secondary">Válasszon sablont...</Typography>;
              }
              const template = activeTemplates.find((t) => t.id === selected);
              return (
                <Box>
                  <Typography variant="body1" fontWeight={500}>
                    {template?.name}
                  </Typography>
                  {template?.description && (
                    <Typography variant="caption" color="text.secondary" noWrap>
                      {template.description}
                    </Typography>
                  )}
                </Box>
              );
            }}
          >
            {activeTemplates.map((template) => (
              <MenuItem key={template.id} value={template.id}>
                <Box sx={{ width: '100%' }}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body2" fontWeight={500}>
                        {template.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {template.beneficiary_count} kedvezményezett
                      </Typography>
                      {template.description && (
                        <Typography variant="caption" color="text.secondary" display="block" noWrap>
                          {template.description}
                        </Typography>
                      )}
                    </Box>
                    {selectedTemplate?.id === template.id && (
                      <Chip size="small" color="primary" label="Kiválasztva" />
                    )}
                  </Stack>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}

      {selectedTemplate && (
        <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                <Typography component="span" fontWeight={500}>
                  Kedvezményezettek:
                </Typography>{' '}
                {selectedTemplate.beneficiary_count}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                <Typography component="span" fontWeight={500}>
                  Létrehozva:
                </Typography>{' '}
                {new Date(selectedTemplate.created_at).toLocaleDateString('hu-HU')}
              </Typography>
            </Box>
          </Box>
          {selectedTemplate.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {selectedTemplate.description}
            </Typography>
          )}
        </Box>
      )}
    </Paper>
  );
};

export default TemplateSelector;
