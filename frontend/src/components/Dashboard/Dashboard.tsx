import React from 'react';
import { Link } from 'react-router-dom';
import {
  UserGroupIcon,
  DocumentDuplicateIcon,
  ArrowsRightLeftIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';
import { useBeneficiaries, useTemplates } from '../../hooks/api';

const quickActions = [
  {
    name: 'Új átutalás készítése',
    description: 'Sablon alapján gyors átutalás létrehozása',
    href: '/transfers',
    icon: ArrowsRightLeftIcon,
    color: 'bg-primary-500',
  },
  {
    name: 'Kedvezményezettek kezelése',
    description: 'Kedvezményezettek hozzáadása, szerkesztése',
    href: '/beneficiaries',
    icon: UserGroupIcon,
    color: 'bg-green-500',
  },
  {
    name: 'Sablonok szerkesztése',
    description: 'Átutalási sablonok létrehozása és kezelése',
    href: '/templates',
    icon: DocumentDuplicateIcon,
    color: 'bg-purple-500',
  },
];

const Dashboard: React.FC = () => {
  const { data: beneficiariesData } = useBeneficiaries({ page: 1 });
  const { data: templatesData } = useTemplates();
  
  const totalBeneficiaries = beneficiariesData?.count || 0;
  const totalTemplates = templatesData?.results?.length || 0;
  const activeTemplates = templatesData?.results?.filter(t => t.is_active).length || 0;
  const todayTransfers = 0; // This would come from a today's transfers API

  const stats = [
    { name: 'Összes kedvezményezett', stat: totalBeneficiaries.toString(), icon: UserGroupIcon, href: '/beneficiaries' },
    { name: 'Aktív sablonok', stat: activeTemplates.toString(), icon: DocumentDuplicateIcon, href: '/templates' },
    { name: 'Mai átutalások', stat: todayTransfers.toString(), icon: ArrowsRightLeftIcon, href: '/transfers' },
    { name: 'Összes sablon', stat: totalTemplates.toString(), icon: ChartBarIcon, href: '/templates' },
  ];

  return (
    <div className="lg:pl-72">
      <div className="xl:pr-96">
        <div className="px-4 py-10 sm:px-6 lg:px-8 lg:py-6">
          <div className="border-b border-gray-200 pb-5">
            <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900">
              Főoldal
            </h1>
            <p className="mt-2 max-w-4xl text-sm text-gray-500">
              Bank átutalások XML generálása és kezelése
            </p>
          </div>

          {/* Stats */}
          <div className="mt-8">
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {stats.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className="relative overflow-hidden rounded-lg bg-white px-4 py-5 shadow hover:shadow-md transition-shadow sm:px-6 sm:py-6"
                >
                  <div>
                    <dt className="truncate text-sm font-medium text-gray-500">
                      {item.name}
                    </dt>
                    <dd className="mt-1 text-3xl font-semibold tracking-tight text-gray-900">
                      {item.stat}
                    </dd>
                  </div>
                  <div className="absolute top-4 right-4">
                    <item.icon className="h-8 w-8 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>
          </div>

          {/* Quick Actions */}
          <div className="mt-12">
            <h2 className="text-lg font-medium text-gray-900">Gyors műveletek</h2>
            <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {quickActions.map((action) => (
                <Link
                  key={action.name}
                  to={action.href}
                  className="group relative overflow-hidden rounded-lg bg-white p-6 shadow hover:shadow-md transition-shadow"
                >
                  <div>
                    <span className={`inline-flex rounded-lg p-3 ${action.color}`}>
                      <action.icon className="h-6 w-6 text-white" aria-hidden="true" />
                    </span>
                  </div>
                  <div className="mt-4">
                    <h3 className="text-lg font-medium text-gray-900 group-hover:text-primary-600">
                      {action.name}
                    </h3>
                    <p className="mt-2 text-sm text-gray-500">
                      {action.description}
                    </p>
                  </div>
                  <span
                    className="absolute inset-x-0 bottom-0 h-1 bg-primary-600 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-200"
                    aria-hidden="true"
                  />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;