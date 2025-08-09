import React, { useState } from 'react';
import { Routes, Route } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import Dashboard from '../Dashboard/Dashboard';
import BeneficiaryManager from '../BeneficiaryManager/BeneficiaryManager';
import TemplateBuilder from '../TemplateBuilder/TemplateBuilder';
import TransferWorkflow from '../TransferWorkflow/TransferWorkflow';

const Layout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header onMenuClick={() => setSidebarOpen(true)} />
        
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/beneficiaries" element={<BeneficiaryManager />} />
            <Route path="/templates" element={<TemplateBuilder />} />
            <Route path="/transfers" element={<TransferWorkflow />} />
          </Routes>
        </main>
      </div>
    </div>
  );
};

export default Layout;