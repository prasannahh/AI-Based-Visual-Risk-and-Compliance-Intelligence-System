import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CalendarCheck,
  BookOpen,
  Sparkles,
  GitFork,
  TrendingUp,
  BarChart3,
  User,
  Settings,
  LogOut,
  Dna,
  X,
  Bot,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavItem {
  name: string;
  to: string;
  icon: React.ReactNode;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const SECTIONS: NavSection[] = [
  {
    title: 'DIGITAL TWIN',
    items: [
      { name: 'Overview', to: '/', icon: <LayoutDashboard className="w-4 h-4" /> },
      { name: 'Tasks & Planner', to: '/tasks', icon: <CalendarCheck className="w-4 h-4" /> },
      { name: 'Study & Academic', to: '/study', icon: <BookOpen className="w-4 h-4" /> },
      { name: 'Suggestions', to: '/suggestions', icon: <Sparkles className="w-4 h-4" /> },
    ],
  },
  {
    title: 'PLANNING & ANALYSIS',
    items: [
      { name: 'What-If Simulator', to: '/simulation', icon: <GitFork className="w-4 h-4" /> },
      { name: 'Wealth Planner', to: '/wealth', icon: <TrendingUp className="w-4 h-4" /> },
      { name: 'Analytics', to: '/analytics', icon: <BarChart3 className="w-4 h-4" /> },
    ],
  },
  {
    title: 'PERSONAL',
    items: [
      { name: 'Profile & Goals', to: '/profile', icon: <User className="w-4 h-4" /> },
      { name: 'Settings', to: '/settings', icon: <Settings className="w-4 h-4" /> },
    ],
  },
];

interface SidebarProps {
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
  onOpenChat?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isMobileOpen = false,
  onCloseMobile,
  onOpenChat,
}) => {
  const { user, logout } = useAuth();

  const initials = user?.name
    ? user.name
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : 'DT';

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-slate-900/25 backdrop-blur-2xs lg:hidden transition-opacity"
        />
      )}

      {/* Main Sidebar Container */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white dark:bg-slate-900 border-r border-slate-200/80 dark:border-slate-800 flex flex-col justify-between transition-transform duration-200 ease-in-out lg:static lg:translate-x-0 lg:h-screen lg:sticky lg:top-0 lg:shrink-0 select-none ${
          isMobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div>
          <div className="h-16 px-6 flex items-center justify-between border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-xs">
                <Dna className="w-4 h-4" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 tracking-tight flex items-center gap-1.5">
                  Digital Twin AI
                  <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.2 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 rounded-md border border-indigo-100 dark:border-indigo-800">
                    PRO
                  </span>
                </div>
                <div className="text-[11px] text-slate-400 dark:text-slate-500 font-medium">Decision Intelligence</div>
              </div>
            </div>

            {/* Close button visible only on mobile */}
            <button
              onClick={onCloseMobile}
              className="lg:hidden p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Navigation Items */}
          <nav className="p-4 space-y-6 overflow-y-auto max-h-[calc(100vh-8.5rem)]">
            {SECTIONS.map((section) => (
              <div key={section.title}>
                <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-slate-400 dark:text-slate-500 uppercase">
                  {section.title}
                </div>
                <ul className="space-y-1">
                  {section.items.map((item) => (
                    <li key={item.name}>
                      <NavLink
                        to={item.to}
                        end={item.to === '/'}
                        onClick={() => onCloseMobile?.()}
                        className={({ isActive }) =>
                          `flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                            isActive
                              ? 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-400 font-semibold shadow-2xs'
                              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 hover:bg-slate-50 dark:hover:bg-slate-800/60'
                          }`
                        }
                      >
                        {item.icon}
                        <span>{item.name}</span>
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </div>
            ))}

            {/* AI Assistant Drawer Trigger */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
              <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-slate-400 dark:text-slate-500 uppercase">
                AI Assistant
              </div>
              <button
                type="button"
                onClick={() => {
                  onCloseMobile?.();
                  onOpenChat?.();
                }}
                className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium rounded-xl text-indigo-700 dark:text-indigo-400 bg-indigo-50/60 dark:bg-indigo-950/40 hover:bg-indigo-100/60 dark:hover:bg-indigo-905/60 border border-indigo-100/80 dark:border-indigo-800/60 transition-all cursor-pointer group"
              >
                <div className="flex items-center gap-2.5">
                  <Bot className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                  <span>Twin Assistant</span>
                </div>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 text-indigo-700 dark:text-indigo-400 border border-indigo-200/60 dark:border-indigo-800 shadow-2xs">
                  Chat
                </span>
              </button>
            </div>
          </nav>
        </div>

        {/* User Footer */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-950/50">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-9 h-9 rounded-full bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 font-semibold text-xs flex items-center justify-center shrink-0 border border-indigo-200/60 dark:border-indigo-800">
                {initials}
              </div>
              <div className="truncate">
                <div className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                  {user?.name || 'Twin User'}
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate">
                  {user?.occupation || user?.email || 'Active'}
                </div>
              </div>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/50 rounded-lg transition-colors cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
