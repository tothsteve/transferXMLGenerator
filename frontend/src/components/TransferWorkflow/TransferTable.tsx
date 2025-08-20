import React, { useState } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
  IconButton,
  TextField,
  Box,
  Stack,
  Avatar,
  Tooltip,
  Card,
  CardContent,
  alpha
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Add as AddIcon,
  CalendarToday as CalendarIcon,
  AccountBalance as CurrencyIcon,
  DragIndicator as DragIcon,
  Person as PersonIcon,
  Receipt as ReceiptIcon,
  Payments as PaymentsIcon
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
import {
  CSS,
} from '@dnd-kit/utilities';
import { Transfer, Beneficiary } from '../../types/api';

interface TransferData extends Omit<Transfer, 'id' | 'is_processed' | 'created_at'> {
  id?: number;
  beneficiary_data?: Beneficiary;
  tempId?: string;
}

interface TransferTableProps {
  transfers: TransferData[];
  onUpdateTransfer: (index: number, transfer: Partial<TransferData>) => void;
  onDeleteTransfer: (index: number) => void;
  onAddTransfer: () => void;
  onReorderTransfers: (transfers: TransferData[]) => void;
}

// Sortable Row Component
const SortableRow: React.FC<{
  transfer: TransferData;
  index: number;
  editingIndex: number | null;
  editData: Partial<TransferData>;
  onStartEdit: (index: number, transfer: TransferData) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onDelete: (index: number) => void;
  onUpdateEditData: (data: Partial<TransferData>) => void;
}> = ({
  transfer,
  index,
  editingIndex,
  editData,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onDelete,
  onUpdateEditData,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: transfer.id || transfer.tempId || `transfer-${index}`
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <TableRow 
      ref={setNodeRef} 
      style={style} 
      hover={!isDragging}
      sx={{ 
        cursor: isDragging ? 'grabbing' : 'default',
        '&:hover .drag-handle': { opacity: 1 }
      }}
    >
      <TableCell sx={{ width: 48, p: 1 }}>
        <IconButton
          {...attributes}
          {...listeners}
          size="small"
          className="drag-handle"
          sx={{ 
            opacity: 0.3,
            transition: 'opacity 0.2s',
            cursor: 'grab',
            '&:active': { cursor: 'grabbing' }
          }}
        >
          <DragIcon />
        </IconButton>
      </TableCell>
      <TableCell>
        <Stack direction="row" alignItems="center" spacing={2}>
          <Avatar 
            sx={{ 
              width: 40, 
              height: 40, 
              bgcolor: 'primary.main',
              background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)'
            }}
          >
            <PersonIcon />
          </Avatar>
          <Box>
            <Typography variant="body2" fontWeight={600} sx={{ color: 'text.primary' }}>
              {transfer.beneficiary_data?.name || `Kedvezményezett #${transfer.beneficiary}`}
            </Typography>
            <Typography 
              variant="caption" 
              sx={{ 
                color: 'text.secondary', 
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                letterSpacing: '0.02em'
              }}
            >
              {transfer.beneficiary_data?.account_number}
            </Typography>
          </Box>
        </Stack>
      </TableCell>
      <TableCell>
        {editingIndex === index ? (
          <TextField
            type="number"
            size="small"
            value={editData.amount || ''}
            onChange={(e) => onUpdateEditData({ ...editData, amount: e.target.value })}
            placeholder="0"
            sx={{ width: 140 }}
            InputProps={{ 
              inputProps: { step: 1 },
              startAdornment: <PaymentsIcon sx={{ color: 'text.secondary', mr: 1, fontSize: 18 }} />
            }}
          />
        ) : (
          <Stack direction="row" alignItems="center" spacing={1}>
            <PaymentsIcon sx={{ color: 'success.main', fontSize: 18 }} />
            <Box>
              <Typography variant="body2" fontWeight={600} sx={{ color: 'text.primary' }}>
                {parseFloat(transfer.amount).toLocaleString('hu-HU')}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                HUF
              </Typography>
            </Box>
          </Stack>
        )}
      </TableCell>
      <TableCell>
        {editingIndex === index ? (
          <TextField
            type="date"
            size="small"
            value={editData.execution_date || ''}
            onChange={(e) => onUpdateEditData({ ...editData, execution_date: e.target.value })}
            sx={{ width: 150 }}
          />
        ) : (
          <Stack direction="row" alignItems="center" spacing={1}>
            <CalendarIcon sx={{ fontSize: 18, color: 'primary.main' }} />
            <Box>
              <Typography variant="body2" fontWeight={500} sx={{ color: 'text.primary' }}>
                {new Date(transfer.execution_date).toLocaleDateString('hu-HU')}
              </Typography>
              <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
                Teljesítés
              </Typography>
            </Box>
          </Stack>
        )}
      </TableCell>
      <TableCell>
        {editingIndex === index ? (
          <TextField
            size="small"
            value={editData.remittance_info || ''}
            onChange={(e) => onUpdateEditData({ ...editData, remittance_info: e.target.value })}
            placeholder="Közlemény..."
            fullWidth
          />
        ) : (
          <Stack direction="row" alignItems="center" spacing={1}>
            <ReceiptIcon sx={{ fontSize: 16, color: 'secondary.main' }} />
            <Typography 
              variant="body2" 
              sx={{ 
                maxWidth: 200, 
                color: 'text.primary',
                fontWeight: transfer.remittance_info ? 500 : 400,
                fontStyle: transfer.remittance_info ? 'normal' : 'italic'
              }}
              noWrap
            >
              {transfer.remittance_info || 'Nincs közlemény'}
            </Typography>
          </Stack>
        )}
      </TableCell>
      <TableCell align="right">
        {editingIndex === index ? (
          <Stack direction="row" justifyContent="flex-end" spacing={0.5}>
            <Tooltip title="Mentés">
              <IconButton onClick={onSaveEdit} size="small" color="success">
                <CheckIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Mégse">
              <IconButton onClick={onCancelEdit} size="small" color="error">
                <CloseIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        ) : (
          <Stack direction="row" justifyContent="flex-end" spacing={0.5}>
            <Tooltip title="Szerkesztés">
              <IconButton
                onClick={() => onStartEdit(index, transfer)}
                size="small"
                color="primary"
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Tooltip title="Törlés">
              <IconButton
                onClick={() => onDelete(index)}
                size="small"
                color="error"
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Stack>
        )}
      </TableCell>
    </TableRow>
  );
};

const TransferTable: React.FC<TransferTableProps> = ({
  transfers,
  onUpdateTransfer,
  onDeleteTransfer,
  onAddTransfer,
  onReorderTransfers,
}) => {
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editData, setEditData] = useState<Partial<TransferData>>({});

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = transfers.findIndex(
        (transfer) => 
          (transfer.id || transfer.tempId || `transfer-${transfers.indexOf(transfer)}`) === active.id
      );
      const newIndex = transfers.findIndex(
        (transfer) => 
          (transfer.id || transfer.tempId || `transfer-${transfers.indexOf(transfer)}`) === over.id
      );

      if (oldIndex !== -1 && newIndex !== -1) {
        const reorderedTransfers = arrayMove(transfers, oldIndex, newIndex);
        onReorderTransfers(reorderedTransfers);
      }
    }
  };

  const handleStartEdit = (index: number, transfer: TransferData) => {
    setEditingIndex(index);
    setEditData({
      amount: transfer.amount,
      execution_date: transfer.execution_date,
      remittance_info: transfer.remittance_info,
    });
  };

  const handleSaveEdit = () => {
    if (editingIndex !== null) {
      onUpdateTransfer(editingIndex, editData);
      setEditingIndex(null);
      setEditData({});
    }
  };

  const handleCancelEdit = () => {
    setEditingIndex(null);
    setEditData({});
  };

  const totalAmount = transfers.reduce((sum, transfer) => 
    sum + (parseFloat(transfer.amount) || 0), 0
  );

  if (transfers.length === 0) {
    return (
      <Card 
        elevation={2}
        sx={{
          background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(255, 255, 255, 0.3)',
          borderRadius: 3,
        }}
      >
        <CardContent>
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <Avatar 
              sx={{ 
                width: 80, 
                height: 80, 
                mx: 'auto', 
                mb: 3,
                background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.1) 0%, rgba(59, 130, 246, 0.05) 100%)',
                border: '2px solid rgba(37, 99, 235, 0.1)'
              }}
            >
              <CurrencyIcon sx={{ fontSize: 36, color: 'primary.main' }} />
            </Avatar>
            <Typography variant="h5" fontWeight={700} sx={{ mb: 2, color: 'text.primary' }}>
              Nincsenek átutalások
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 4, maxWidth: 400, mx: 'auto' }}>
              Válasszon ki egy sablont vagy adjon hozzá manuálisan átutalásokat a kezdéshez.
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<AddIcon />}
              onClick={onAddTransfer}
              sx={{
                borderRadius: 3,
                px: 4,
                py: 1.5,
                background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
                boxShadow: '0 4px 16px rgba(37, 99, 235, 0.3)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 6px 20px rgba(37, 99, 235, 0.4)',
                }
              }}
            >
              Átutalás hozzáadása
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      elevation={2}
      sx={{
        background: 'linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(255, 255, 255, 0.85) 100%)',
        backdropFilter: 'blur(20px)',
        border: '1px solid rgba(255, 255, 255, 0.3)',
        borderRadius: 3,
        overflow: 'hidden'
      }}
    >
      {/* Header */}
      <Box 
        sx={{ 
          px: 3, 
          py: 3, 
          background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.05) 0%, rgba(59, 130, 246, 0.02) 100%)',
          borderBottom: `1px solid ${alpha('#2563eb', 0.1)}`,
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}
      >
        <Stack direction="row" alignItems="center" spacing={2}>
          <Avatar sx={{ 
            bgcolor: 'primary.main',
            background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
            width: 32,
            height: 32
          }}>
            <CurrencyIcon sx={{ fontSize: 18 }} />
          </Avatar>
          <Typography variant="h6" fontWeight={700} sx={{ color: 'text.primary' }}>
            Átutalások ({transfers.length})
          </Typography>
        </Stack>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={onAddTransfer}
          size="small"
          sx={{
            borderRadius: 2,
            background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)',
            '&:hover': {
              background: 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)',
              transform: 'translateY(-1px)',
              boxShadow: '0 6px 16px rgba(37, 99, 235, 0.4)',
            }
          }}
        >
          Hozzáadás
        </Button>
      </Box>

      {/* Table */}
      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ width: 48 }}></TableCell>
                <TableCell>Kedvezményezett</TableCell>
                <TableCell>Összeg (HUF)</TableCell>
                <TableCell>Teljesítés dátuma</TableCell>
                <TableCell>Közlemény</TableCell>
                <TableCell align="right">Műveletek</TableCell>
              </TableRow>
            </TableHead>
            <SortableContext 
              items={transfers.map((transfer, index) => 
                transfer.id || transfer.tempId || `transfer-${index}`
              )}
              strategy={verticalListSortingStrategy}
            >
              <TableBody>
                {transfers.map((transfer, index) => (
                  <SortableRow
                    key={transfer.id || transfer.tempId || `transfer-${index}`}
                    transfer={transfer}
                    index={index}
                    editingIndex={editingIndex}
                    editData={editData}
                    onStartEdit={handleStartEdit}
                    onSaveEdit={handleSaveEdit}
                    onCancelEdit={handleCancelEdit}
                    onDelete={onDeleteTransfer}
                    onUpdateEditData={setEditData}
                  />
                ))}
              </TableBody>
            </SortableContext>
          </Table>
        </TableContainer>
      </DndContext>

      {/* Footer with totals */}
      <Box 
        sx={{ 
          px: 3, 
          py: 3, 
          background: 'linear-gradient(135deg, rgba(5, 150, 105, 0.03) 0%, rgba(16, 185, 129, 0.02) 100%)',
          borderTop: `1px solid ${alpha('#059669', 0.1)}`,
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}
      >
        <Stack direction="row" alignItems="center" spacing={2}>
          <Avatar sx={{ 
            bgcolor: 'success.main',
            background: 'linear-gradient(135deg, #059669 0%, #10b981 100%)',
            width: 28,
            height: 28
          }}>
            <Typography variant="caption" fontWeight={700} sx={{ color: 'white' }}>
              {transfers.length}
            </Typography>
          </Avatar>
          <Typography variant="body2" color="text.secondary" fontWeight={500}>
            átutalás összesen
          </Typography>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1}>
          <PaymentsIcon sx={{ color: 'success.main', fontSize: 20 }} />
          <Box textAlign="right">
            <Typography variant="h6" fontWeight={700} sx={{ color: 'success.dark' }}>
              {totalAmount.toLocaleString('hu-HU')}
            </Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              HUF összesen
            </Typography>
          </Box>
        </Stack>
      </Box>
    </Card>
  );
};

export default TransferTable;