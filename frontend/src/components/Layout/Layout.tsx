import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, useTheme, useMediaQuery } from '@mui/material';
import Sidebar from './Sidebar';
import Header from './Header';
import Dashboard from '../Dashboard/Dashboard';
import BeneficiaryManager from '../BeneficiaryManager/BeneficiaryManager';
import TemplateBuilder from '../TemplateBuilder/TemplateBuilder';
import TransferWorkflow from '../TransferWorkflow/TransferWorkflow';
import BatchManager from '../BatchManager/BatchManager';

const SIDEBAR_WIDTH = 280;

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));

  return (
    <Box 
      sx={{ 
        display: 'flex', 
        height: '100vh',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 25%, #f1f5f9 50%, #f8fafc 100%)',
      }}
    >
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        width={SIDEBAR_WIDTH}
        isMobile={isMobile}
      />
      
      <Box 
        sx={{ 
          flexGrow: 1, 
          display: 'flex', 
          flexDirection: 'column',
          ml: { lg: `${SIDEBAR_WIDTH}px` },
          transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
          }),
        }}
      >
        <Header onMenuClick={() => setSidebarOpen(true)} />
        
        <Box 
          component="main" 
          sx={{ 
            flexGrow: 1, 
            p: 3,
            bgcolor: 'background.default',
            overflow: 'auto'
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/beneficiaries" element={<BeneficiaryManager />} />
            <Route path="/templates" element={<TemplateBuilder />} />
            <Route path="/transfers" element={<TransferWorkflow />} />
            <Route path="/batches" element={<BatchManager />} />
          </Routes>
        </Box>
      </Box>
    </Box>
  );
};

export default Layout;