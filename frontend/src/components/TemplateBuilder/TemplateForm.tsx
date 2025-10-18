import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Checkbox,
  FormControlLabel,
  Box,
  Stack,
  Typography,
  IconButton,
  Paper,
  InputAdornment,
  List,
  ListItem,
  ListItemText,
  Tooltip,
} from '@mui/material';
import {
  Close as CloseIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  DragIndicator as DragIcon,
} from '@mui/icons-material';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { TransferTemplate, Beneficiary } from '../../types/api';
import { useBeneficiaries } from '../../hooks/api';

interface TemplateFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TemplateFormData) => void;
  template?: TransferTemplate | null;
  isLoading?: boolean;
}

interface TemplateFormData {
  name: string;
  description: string;
  is_active: boolean;
  beneficiaries: {
    beneficiary_id: number;
    default_amount: string;
    default_remittance_info: string;
  }[];
}

interface BeneficiarySelection {
  beneficiary_id: number;
  beneficiary_name: string;
  account_number: string | null | undefined;
  vat_number: string | null | undefined;
  default_amount: string;
  default_remittance_info: string;
  order: number;
}

// Sortable Beneficiary Component
const SortableBeneficiary: React.FC<{
  beneficiary: BeneficiarySelection;
  onUpdate: (
    beneficiaryId: number,
    field: 'default_amount' | 'default_remittance_info',
    value: string
  ) => void;
  onRemove: (beneficiaryId: number) => void;
}> = ({ beneficiary, onUpdate, onRemove }) => {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: beneficiary.beneficiary_id,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <Paper
      ref={setNodeRef}
      style={style}
      sx={{
        p: 2,
        cursor: isDragging ? 'grabbing' : 'default',
        '&:hover .drag-handle': { opacity: 1 },
      }}
    >
      <Stack direction="row" spacing={2}>
        <Box sx={{ display: 'flex', alignItems: 'flex-start', pt: 1 }}>
          <Tooltip title="Húzd a sorrendezéshez">
            <IconButton
              {...attributes}
              {...listeners}
              size="small"
              className="drag-handle"
              sx={{
                opacity: 0.3,
                transition: 'opacity 0.2s',
                cursor: 'grab',
                '&:active': { cursor: 'grabbing' },
              }}
            >
              <DragIcon />
            </IconButton>
          </Tooltip>
        </Box>

        <Box sx={{ flex: 1 }}>
          <Typography variant="body1" fontWeight={500}>
            {beneficiary.beneficiary_name}
          </Typography>
          <Stack spacing={0.25}>
            {beneficiary.account_number && (
              <Typography variant="body2" color="text.secondary" fontFamily="monospace">
                {beneficiary.account_number}
              </Typography>
            )}
            {beneficiary.vat_number && (
              <Typography variant="body2" sx={{ color: 'info.main', fontWeight: 500 }}>
                Adóazonosító: {beneficiary.vat_number}
              </Typography>
            )}
            {!beneficiary.account_number && !beneficiary.vat_number && (
              <Typography variant="body2" color="text.secondary">
                -
              </Typography>
            )}
          </Stack>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
              gap: 2,
              mt: 1,
            }}
          >
            <Box>
              <TextField
                label="Alapértelmezett összeg (HUF)"
                type="number"
                size="small"
                fullWidth
                value={beneficiary.default_amount || ''}
                onChange={(e) =>
                  onUpdate(beneficiary.beneficiary_id, 'default_amount', e.target.value)
                }
                placeholder="0"
              />
            </Box>
            <Box>
              <TextField
                label="Alapértelmezett közlemény"
                size="small"
                fullWidth
                value={beneficiary.default_remittance_info || ''}
                onChange={(e) =>
                  onUpdate(beneficiary.beneficiary_id, 'default_remittance_info', e.target.value)
                }
                placeholder="Közlemény..."
              />
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'flex-start', pt: 1 }}>
          <Tooltip title="Eltávolítás">
            <IconButton
              onClick={() => onRemove(beneficiary.beneficiary_id)}
              color="error"
              size="small"
            >
              <DeleteIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Stack>
    </Paper>
  );
};

const TemplateForm: React.FC<TemplateFormProps> = ({
  isOpen,
  onClose,
  onSubmit,
  template,
  isLoading = false,
}) => {
  const [selectedBeneficiaries, setSelectedBeneficiaries] = useState<BeneficiarySelection[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showBeneficiaryPicker, setShowBeneficiaryPicker] = useState(false);

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<Omit<TemplateFormData, 'beneficiaries'>>({
    defaultValues: {
      name: template?.name || '',
      description: template?.description || '',
      is_active: template?.is_active ?? true,
    },
  });

  const { data: beneficiariesData } = useBeneficiaries({
    search: searchTerm,
    is_active: true,
  });

  const availableBeneficiaries = beneficiariesData?.results || [];
  const selectedBeneficiaryIds = new Set(selectedBeneficiaries.map((b) => b.beneficiary_id));

  useEffect(() => {
    if (template) {
      // Reset form with template values
      reset({
        name: template.name || '',
        description: template.description || '',
        is_active: template.is_active ?? true,
      });

      // Load template beneficiaries if they exist
      if (template.template_beneficiaries) {
        const templateBeneficiaries = template.template_beneficiaries
          .sort((a, b) => a.order - b.order) // Sort by order field
          .map((tb) => ({
            beneficiary_id: tb.beneficiary.id,
            beneficiary_name: tb.beneficiary.name,
            account_number: tb.beneficiary.account_number,
            vat_number: tb.beneficiary.vat_number,
            default_amount: tb.default_amount?.toString() || '',
            default_remittance_info: tb.default_remittance || '',
            order: tb.order,
          }));
        setSelectedBeneficiaries(templateBeneficiaries);
      }
    } else {
      // Reset form for new template
      reset({
        name: '',
        description: '',
        is_active: true,
      });
      setSelectedBeneficiaries([]);
    }
  }, [template, reset]);

  const handleDragEnd = (event: DragEndEvent): void => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = selectedBeneficiaries.findIndex(
        (beneficiary) => beneficiary.beneficiary_id === active.id
      );
      const newIndex = selectedBeneficiaries.findIndex(
        (beneficiary) => beneficiary.beneficiary_id === over.id
      );

      if (oldIndex !== -1 && newIndex !== -1) {
        const reorderedBeneficiaries = arrayMove(selectedBeneficiaries, oldIndex, newIndex).map(
          (b, index) => ({
            ...b,
            order: index, // Update order based on new position
          })
        );
        setSelectedBeneficiaries(reorderedBeneficiaries);
      }
    }
  };

  const handleFormSubmit = (data: Omit<TemplateFormData, 'beneficiaries'>): void => {
    const formData: TemplateFormData = {
      ...data,
      beneficiaries: selectedBeneficiaries.map((b) => ({
        beneficiary_id: b.beneficiary_id,
        default_amount: b.default_amount,
        default_remittance_info: b.default_remittance_info,
      })),
    };
    onSubmit(formData);
  };

  const handleClose = (): void => {
    reset();
    setSelectedBeneficiaries([]);
    setSearchTerm('');
    setShowBeneficiaryPicker(false);
    onClose();
  };

  const addBeneficiary = (beneficiary: Beneficiary): void => {
    if (!selectedBeneficiaryIds.has(beneficiary.id)) {
      setSelectedBeneficiaries((prev) => [
        ...prev,
        {
          beneficiary_id: beneficiary.id,
          beneficiary_name: beneficiary.name,
          account_number: beneficiary.account_number,
          vat_number: beneficiary.vat_number,
          default_amount: '',
          default_remittance_info: beneficiary.remittance_information || '',
          order: prev.length, // Add to the end
        },
      ]);
    }
    setShowBeneficiaryPicker(false);
    setSearchTerm('');
  };

  const removeBeneficiary = (beneficiaryId: number): void => {
    setSelectedBeneficiaries(
      (prev) =>
        prev
          .filter((b) => b.beneficiary_id !== beneficiaryId)
          .map((b, index) => ({ ...b, order: index })) // Reorder after removal
    );
  };

  const updateBeneficiary = (
    beneficiaryId: number,
    field: 'default_amount' | 'default_remittance_info',
    value: string
  ) => {
    setSelectedBeneficiaries((prev) =>
      prev.map((b) => (b.beneficiary_id === beneficiaryId ? { ...b, [field]: value } : b))
    );
  };

  return (
    <Dialog open={isOpen} onClose={handleClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {template ? 'Sablon szerkesztése' : 'Új sablon létrehozása'}
          </Typography>
          <IconButton onClick={handleClose} size="small">
            <CloseIcon />
          </IconButton>
        </Stack>
      </DialogTitle>

      <form onSubmit={handleSubmit(handleFormSubmit)}>
        <DialogContent>
          <Stack spacing={4}>
            {/* Basic Template Info */}
            <Box
              sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '2fr 1fr' }, gap: 3 }}
            >
              <Box>
                <TextField
                  label="Sablon neve *"
                  fullWidth
                  placeholder="pl. Havi bérszámfejtés"
                  {...register('name', { required: 'A sablon neve kötelező' })}
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Controller
                  name="is_active"
                  control={control}
                  render={({ field: { onChange, value, ...field } }) => (
                    <FormControlLabel
                      control={
                        <Checkbox
                          {...field}
                          checked={!!value}
                          onChange={(e) => onChange(e.target.checked)}
                        />
                      }
                      label="Aktív sablon"
                    />
                  )}
                />
              </Box>
            </Box>

            <TextField
              label="Leírás"
              fullWidth
              multiline
              rows={3}
              placeholder="Sablon leírása..."
              {...register('description')}
            />

            {/* Beneficiaries Section */}
            <Box>
              <Stack
                direction="row"
                justifyContent="space-between"
                alignItems="center"
                sx={{ mb: 2 }}
              >
                <Typography variant="body1" fontWeight={500}>
                  Kedvezményezettek ({selectedBeneficiaries.length})
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => setShowBeneficiaryPicker(true)}
                >
                  Hozzáadás
                </Button>
              </Stack>

              {/* Beneficiary Picker Dialog */}
              <Dialog
                open={showBeneficiaryPicker}
                onClose={() => setShowBeneficiaryPicker(false)}
                maxWidth="sm"
                fullWidth
              >
                <DialogTitle>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="h6">Kedvezményezett kiválasztása</Typography>
                    <IconButton onClick={() => setShowBeneficiaryPicker(false)} size="small">
                      <CloseIcon />
                    </IconButton>
                  </Stack>
                </DialogTitle>
                <DialogContent>
                  <TextField
                    fullWidth
                    placeholder="Keresés..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    sx={{ mb: 2 }}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      ),
                    }}
                  />
                  <List sx={{ maxHeight: 300, overflow: 'auto' }}>
                    {availableBeneficiaries
                      .filter((b) => !selectedBeneficiaryIds.has(b.id))
                      .map((beneficiary) => (
                        <ListItem
                          key={beneficiary.id}
                          onClick={() => addBeneficiary(beneficiary)}
                          sx={{
                            border: 1,
                            borderColor: 'divider',
                            borderRadius: 1,
                            mb: 1,
                            cursor: 'pointer',
                            '&:hover': {
                              backgroundColor: 'action.hover',
                            },
                          }}
                        >
                          <ListItemText
                            primary={beneficiary.name}
                            secondary={
                              <Stack spacing={0.25}>
                                {beneficiary.account_number && (
                                  <Typography variant="body2" fontFamily="monospace">
                                    {beneficiary.account_number}
                                  </Typography>
                                )}
                                {beneficiary.vat_number && (
                                  <Typography
                                    variant="body2"
                                    sx={{ color: 'info.main', fontWeight: 500 }}
                                  >
                                    Adóazonosító: {beneficiary.vat_number}
                                  </Typography>
                                )}
                                {!beneficiary.account_number && !beneficiary.vat_number && (
                                  <Typography variant="body2" color="text.secondary">
                                    -
                                  </Typography>
                                )}
                              </Stack>
                            }
                          />
                        </ListItem>
                      ))}
                  </List>
                </DialogContent>
              </Dialog>

              {/* Selected Beneficiaries */}
              {selectedBeneficiaries.length === 0 ? (
                <Paper
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    border: 2,
                    borderStyle: 'dashed',
                    borderColor: 'divider',
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    Nincs kiválasztott kedvezményezett. Kedvezményezetteket később is hozzáadhat a
                    sablonhoz.
                  </Typography>
                </Paper>
              ) : (
                <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <SortableContext
                      items={selectedBeneficiaries.map((b) => b.beneficiary_id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <Stack spacing={2}>
                        {selectedBeneficiaries
                          .sort((a, b) => a.order - b.order) // Sort by order
                          .map((beneficiary) => (
                            <SortableBeneficiary
                              key={beneficiary.beneficiary_id}
                              beneficiary={beneficiary}
                              onUpdate={updateBeneficiary}
                              onRemove={removeBeneficiary}
                            />
                          ))}
                      </Stack>
                    </SortableContext>
                  </DndContext>
                </Box>
              )}
            </Box>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Mégse</Button>
          <Button type="submit" variant="contained" disabled={isLoading}>
            {isLoading ? 'Mentés...' : template ? 'Frissítés' : 'Létrehozás'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default TemplateForm;
