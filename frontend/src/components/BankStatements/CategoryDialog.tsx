/**
 * @fileoverview Dialog for manually categorizing bank transactions as OtherCost
 * @module components/BankStatements/CategoryDialog
 */

import { ReactElement, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Stack,
  Typography,
  Box,
  Alert,
  Chip,
} from '@mui/material';
import { Category as CategoryIcon, Info as InfoIcon } from '@mui/icons-material';
import { BankTransaction, OtherCostCategory } from '../../schemas/bankStatement.schemas';

/**
 * Props for CategoryDialog component.
 *
 * @interface CategoryDialogProps
 */
interface CategoryDialogProps {
  /** Whether dialog is open */
  open: boolean;

  /** Transaction to categorize */
  transaction: BankTransaction | null;

  /** Callback when dialog is closed */
  onClose: () => void;

  /** Callback when categorization is submitted */
  onSubmit: (data: CategoryFormData) => Promise<void>;

  /** Whether submission is in progress */
  isSubmitting?: boolean;
}

/**
 * Form data for categorization.
 *
 * @interface CategoryFormData
 */
export interface CategoryFormData {
  /** Selected expense category */
  category: OtherCostCategory;

  /** Optional description override */
  description: string;

  /** Optional notes */
  notes: string;

  /** Optional tags (comma-separated) */
  tags: string;
}

/**
 * Category options with Hungarian labels and descriptions.
 */
const CATEGORY_OPTIONS: Array<{
  value: OtherCostCategory;
  label: string;
  description: string;
}> = [
  {
    value: 'SUBSCRIPTION',
    label: 'Előfizetés',
    description: 'Ismétlődő szolgáltatások (Netflix, Claude AI, stb.)',
  },
  {
    value: 'TRAVEL',
    label: 'Utazás',
    description: 'Szállás, repülő, vonat, taxi',
  },
  {
    value: 'FUEL',
    label: 'Üzemanyag',
    description: 'Benzinkút vásárlások',
  },
  {
    value: 'OFFICE',
    label: 'Iroda/irodaszer',
    description: 'Irodai kellékek, bútorok',
  },
  {
    value: 'UTILITY',
    label: 'Közüzemi díj',
    description: 'Víz, áram, gáz, internet',
  },
  {
    value: 'CARD_PURCHASE',
    label: 'Kártyás vásárlás',
    description: 'Általános kártyás fizetések',
  },
  {
    value: 'BANK_FEE',
    label: 'Banki költség',
    description: 'Tranzakciós díjak',
  },
  {
    value: 'INTEREST',
    label: 'Kamat',
    description: 'Betéti kamat vagy hitelkamat',
  },
  {
    value: 'OTHER',
    label: 'Egyéb',
    description: 'Más kategóriába nem sorolható',
  },
];

/**
 * Get merchant/partner name from transaction.
 *
 * @param transaction - Bank transaction
 * @returns Merchant or partner name
 */
const getMerchantName = (transaction: BankTransaction): string => {
  const amount = parseFloat(transaction.amount);
  if (transaction.transaction_type === 'POS_PURCHASE') {
    return transaction.merchant_name || '-';
  }
  return amount > 0 ? transaction.payer_name : transaction.beneficiary_name;
};

/**
 * Category dialog component.
 *
 * Allows manual categorization of bank transactions to establish learned patterns.
 * After categorization, future transactions with the same merchant name will
 * automatically be categorized.
 *
 * Features:
 * - Category selection with descriptions
 * - Optional description and notes
 * - Tag input (comma-separated)
 * - Learned pattern explanation
 *
 * @component
 * @example
 * ```tsx
 * <CategoryDialog
 *   open={dialogOpen}
 *   transaction={selectedTransaction}
 *   onClose={() => setDialogOpen(false)}
 *   onSubmit={handleCategorize}
 *   isSubmitting={isSubmitting}
 * />
 * ```
 */
const CategoryDialog: React.FC<CategoryDialogProps> = ({
  open,
  transaction,
  onClose,
  onSubmit,
  isSubmitting = false,
}): ReactElement => {
  const [category, setCategory] = useState<OtherCostCategory>('OTHER');
  const [description, setDescription] = useState('');
  const [notes, setNotes] = useState('');
  const [tags, setTags] = useState('');
  const [isLocalSubmitting, setIsLocalSubmitting] = useState(false);

  // Reset form when dialog opens
  const handleOpen = () => {
    if (transaction) {
      setCategory('OTHER');
      setDescription(transaction.description || '');
      setNotes('');
      setTags('');
      setIsLocalSubmitting(false);
    }
  };

  // Handle form submission
  const handleSubmit = async () => {
    if (!transaction) return;

    // Prevent duplicate submissions - local guard
    if (isLocalSubmitting || isSubmitting) {
      return;
    }

    setIsLocalSubmitting(true);

    try {
      await onSubmit({
        category,
        description,
        notes,
        tags,
      });

      // Reset form after successful submission
      setCategory('OTHER');
      setDescription('');
      setNotes('');
      setTags('');
    } finally {
      setIsLocalSubmitting(false);
    }
  };

  const merchantName = transaction ? getMerchantName(transaction) : '';

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
      TransitionProps={{
        onEntered: handleOpen,
      }}
    >
      <DialogTitle>
        <Stack direction="row" spacing={1} alignItems="center">
          <CategoryIcon color="primary" />
          <Typography variant="h6">Tranzakció kategorizálása</Typography>
        </Stack>
      </DialogTitle>

      <DialogContent>
        <Stack spacing={3} sx={{ mt: 1 }}>
          {/* Learned Pattern Info */}
          <Alert severity="info" icon={<InfoIcon />}>
            <Typography variant="body2" gutterBottom>
              <strong>Ismétlődő minta tanulás</strong>
            </Typography>
            <Typography variant="caption">
              A kategorizálás után a rendszer automatikusan kategorizálja a jövőbeli
              tranzakciókat ugyanazzal a partnerrel.
            </Typography>
          </Alert>

          {/* Merchant Name */}
          {merchantName && (
            <Box>
              <Typography variant="caption" color="text.secondary">
                Partner/Kereskedő:
              </Typography>
              <Chip label={merchantName} size="small" sx={{ mt: 0.5 }} />
            </Box>
          )}

          {/* Category Selection */}
          <TextField
            select
            label="Kategória *"
            value={category}
            onChange={(e) => setCategory(e.target.value as OtherCostCategory)}
            fullWidth
            helperText="Válassza ki a tranzakció kategóriáját"
          >
            {CATEGORY_OPTIONS.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                <Box>
                  <Typography variant="body2">{option.label}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {option.description}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </TextField>

          {/* Description */}
          <TextField
            label="Leírás"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            fullWidth
            multiline
            rows={2}
            helperText="Opcionális - ha üres, a tranzakció eredeti leírása kerül mentésre"
          />

          {/* Notes */}
          <TextField
            label="Megjegyzések"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            fullWidth
            multiline
            rows={2}
            helperText="Opcionális - további információk a kategorizálásról"
          />

          {/* Tags */}
          <TextField
            label="Címkék"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            fullWidth
            helperText="Opcionális - vesszővel elválasztott címkék (pl: subscription, monthly, claude)"
            placeholder="subscription, monthly"
          />
        </Stack>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={isLocalSubmitting || isSubmitting}>
          Mégse
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={isLocalSubmitting || isSubmitting || !category}
          startIcon={<CategoryIcon />}
        >
          {(isLocalSubmitting || isSubmitting) ? 'Mentés...' : 'Kategorizálás'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CategoryDialog;
