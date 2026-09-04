import React from 'react';
import { useLocation } from 'react-router-dom';
import { Sparkles, Activity, Menu } from 'lucide-react';
import { Button } from '../ui/Button';
import { usePreferences } from '../../context/PreferencesContext';

interface TopNavProps {
  onToggleChat: () => void;
  isChatOpen: boolean;
  onToggleMobileSidebar: () => void;
}

const ROUTE_NAMES: Record<string, string> = {
  '/': 'Overview',
  '/tasks': 'Tasks & Planner',
  '/study': 'Study & Academic',
  '/suggestions': 'Suggestions',
  '/simulation': 'What-If Simulator',
  '/wealth': 'Wealth Planner',
  '/analytics': 'Analytics',
  '/profile': 'Profile & Goals',
  '/settings': 'Settings',
};

export const TopNav: React.FC<TopNavProps> = ({
  onToggleChat,
  isChatOpen,
  onToggleMobileSidebar,
}) => {
  const location = useLocation();
  const { formatDate } = usePreferences();
  const currentTitle = ROUTE_NAMES[location.pathname] || 'Workspace';

  const todayFormatted = formatDate(new Date());

  return (
    <header className="h-16 border-b border-slate-200/80 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md px-4 sm:px-6 lg:px-8 flex items-center justify-between sticky top-0 z-20 transition-colors duration-200">
      <div className="flex items-center gap-3">
        {/* Mobile Hamburger Menu */}
        <button
          onClick={onToggleMobileSidebar}
          className="lg:hidden p-2 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors cursor-pointer"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Route Breadcrumb / Title */}
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-slate-800 dark:text-slate-100 tracking-tight">
            {currentTitle}
          </span>
          <span className="hidden sm:inline text-slate-300 dark:text-slate-700">•</span>
          <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Twin Model Calibrated</span>
            <span className="text-slate-300 dark:text-slate-700">•</span>
            <span>{todayFormatted}</span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-[11px] text-slate-600 dark:text-slate-300 font-medium border border-slate-200/50 dark:border-slate-700">
          <Activity className="w-3.5 h-3.5 text-indigo-600 dark:text-indigo-400" />
          <span>Horizon: 12 Mo</span>
        </div>

        <Button
          variant={isChatOpen ? 'soft' : 'primary'}
          size="sm"
          onClick={onToggleChat}
          leftIcon={<Sparkles className="w-3.5 h-3.5 text-indigo-200" />}
        >
          {isChatOpen ? 'Close Assistant' : 'Ask Twin AI'}
        </Button>
      </div>
    </header>
  );
};
