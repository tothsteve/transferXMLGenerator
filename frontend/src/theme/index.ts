import { createTheme } from '@mui/material/styles';
import { huHU } from '@mui/material/locale';

// Modern Hungarian bank-inspired color palette with gradients
const theme = createTheme(
  {
    palette: {
      mode: 'light',
      primary: {
        main: '#2563eb', // Modern blue
        light: '#60a5fa',
        dark: '#1e40af',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#f59e0b', // Warm accent gold
        light: '#fbbf24',
        dark: '#d97706',
        contrastText: '#ffffff',
      },
      error: {
        main: '#ef4444',
        light: '#f87171',
        dark: '#dc2626',
      },
      warning: {
        main: '#f59e0b',
        light: '#fbbf24',
        dark: '#d97706',
      },
      info: {
        main: '#06b6d4', // Modern cyan
        light: '#22d3ee',
        dark: '#0891b2',
      },
      success: {
        main: '#10b981', // Modern green
        light: '#34d399',
        dark: '#059669',
      },
      grey: {
        50: '#f8fafc',
        100: '#f1f5f9',
        200: '#e2e8f0',
        300: '#cbd5e1',
        400: '#94a3b8',
        500: '#64748b',
        600: '#475569',
        700: '#334155',
        800: '#1e293b',
        900: '#0f172a',
      },
      background: {
        default: '#f8fafc', // Softer, more modern background
        paper: '#ffffff',
      },
      // Custom colors for modern design
      action: {
        hover: 'rgba(59, 130, 246, 0.04)',
        selected: 'rgba(59, 130, 246, 0.08)',
        disabled: 'rgba(0, 0, 0, 0.26)',
        disabledBackground: 'rgba(0, 0, 0, 0.12)',
      },
    },
    typography: {
      // Modern font stack with Inter for better readability
      fontFamily:
        '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica Neue", Arial, sans-serif',
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
        lineHeight: 1.2,
        letterSpacing: '-0.025em', // Tighter letter spacing for headings
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 700,
        lineHeight: 1.25,
        letterSpacing: '-0.020em',
      },
      h3: {
        fontSize: '1.5rem',
        fontWeight: 600,
        lineHeight: 1.3,
        letterSpacing: '-0.015em',
      },
      h4: {
        fontSize: '1.25rem',
        fontWeight: 600,
        lineHeight: 1.35,
        letterSpacing: '-0.010em',
      },
      h5: {
        fontSize: '1.125rem',
        fontWeight: 600,
        lineHeight: 1.4,
        letterSpacing: '-0.005em',
      },
      h6: {
        fontSize: '1rem',
        fontWeight: 600,
        lineHeight: 1.4,
        letterSpacing: 0,
      },
      body1: {
        fontSize: '1rem',
        lineHeight: 1.6, // Better readability
        letterSpacing: 0,
      },
      body2: {
        fontSize: '0.875rem',
        lineHeight: 1.5,
        letterSpacing: 0,
      },
      button: {
        fontWeight: 600,
        letterSpacing: '0.025em', // Slightly spaced button text
        textTransform: 'none' as const,
      },
      caption: {
        fontSize: '0.75rem',
        lineHeight: 1.4,
        letterSpacing: '0.025em',
        fontWeight: 500,
      },
      overline: {
        fontSize: '0.75rem',
        fontWeight: 600,
        letterSpacing: '0.1em',
        textTransform: 'uppercase' as const,
      },
    },
    shape: {
      borderRadius: 12, // More modern rounded corners
    },
    // Enhanced spacing system for better visual hierarchy
    spacing: 8, // Base unit remains 8px but we'll use it more thoughtfully
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 10,
            padding: '10px 20px',
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)', // Smooth transitions
            '&:hover': {
              transform: 'translateY(-1px)', // Subtle lift effect
            },
          },
          contained: {
            boxShadow: '0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
            '&:hover': {
              boxShadow: '0 8px 16px -4px rgba(0, 0, 0, 0.1), 0 4px 6px -1px rgba(0, 0, 0, 0.06)',
              transform: 'translateY(-1px)',
            },
            '&:active': {
              transform: 'translateY(0)',
            },
          },
          outlined: {
            borderWidth: '1.5px',
            '&:hover': {
              borderWidth: '1.5px',
              boxShadow: '0 4px 8px -2px rgba(0, 0, 0, 0.05)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            border: '1px solid rgba(0, 0, 0, 0.05)', // Subtle border
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
          },
          elevation1: {
            boxShadow: '0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
          },
          elevation2: {
            boxShadow: '0 4px 8px -2px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          },
          elevation3: {
            boxShadow: '0 8px 16px -4px rgba(0, 0, 0, 0.12), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 16, // More rounded for modern look
            border: '1px solid rgba(0, 0, 0, 0.05)',
            boxShadow: '0 2px 4px -1px rgba(0, 0, 0, 0.06), 0 1px 2px -1px rgba(0, 0, 0, 0.06)',
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              boxShadow: '0 8px 16px -4px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
              transform: 'translateY(-2px)', // Gentle hover lift
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 10,
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              '&:hover': {
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(37, 99, 235, 0.3)',
                },
              },
              '&.Mui-focused': {
                '& .MuiOutlinedInput-notchedOutline': {
                  borderWidth: '2px',
                  borderColor: '#2563eb',
                },
              },
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 20,
            fontWeight: 500,
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              transform: 'scale(1.02)',
            },
          },
        },
      },
      MuiTableContainer: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            border: '1px solid rgba(0, 0, 0, 0.05)',
          },
        },
      },
      MuiTableHead: {
        styleOverrides: {
          root: {
            '& .MuiTableCell-head': {
              backgroundColor: '#f8fafc',
              fontWeight: 600,
              fontSize: '0.75rem',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              color: '#475569',
              borderBottom: '1px solid #e2e8f0',
            },
          },
        },
      },
      MuiTableRow: {
        styleOverrides: {
          root: {
            transition: 'background-color 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              backgroundColor: '#f8fafc !important',
            },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 16,
            boxShadow: '0 20px 40px -12px rgba(0, 0, 0, 0.25)',
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 10,
            transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              backgroundColor: 'rgba(37, 99, 235, 0.08)',
              transform: 'scale(1.05)',
            },
          },
        },
      },
    },
  },
  huHU
);

export default theme;
