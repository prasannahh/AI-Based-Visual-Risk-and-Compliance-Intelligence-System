import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  noPadding?: boolean;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  noPadding = false,
  title,
  subtitle,
  action,
  ...props
}) => {
  const hasHeader = title || subtitle || action;

  return (
    <div
      className={`rounded-2xl border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900 shadow-[0_1px_3px_0_rgba(15,23,42,0.04)] transition-all duration-200 ${
        noPadding ? '' : 'p-6'
      } ${className}`}
      {...props}
    >
      {hasHeader && (
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            {title && <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{subtitle}</p>}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
