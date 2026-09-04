import React from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import type { BadgeVariant } from './Badge';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  badgeText?: string;
  badgeVariant?: BadgeVariant;
  icon?: React.ReactNode;
  trend?: {
    value: string;
    isPositive?: boolean;
  };
  progressValue?: number; // 0 to 100 for score ring or bar
  progressColor?: string;
  className?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  badgeText,
  badgeVariant = 'default',
  icon,
  trend,
  progressValue,
  progressColor = 'bg-indigo-600',
  className = '',
}) => {
  return (
    <Card className={`relative overflow-hidden flex flex-col justify-between ${className}`}>
      <div>
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {title}
          </span>
          {icon && (
            <div className="w-8 h-8 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700/80 flex items-center justify-center text-slate-600 dark:text-slate-300">
              {icon}
            </div>
          )}
        </div>

        <div className="flex items-baseline justify-between gap-3 mb-1">
          <div className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 font-sans">
            {value}
          </div>
          <div className="flex items-center gap-1.5">
            {trend && (
              <span
                className={`text-xs font-semibold ${
                  trend.isPositive ?? true ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'
                }`}
              >
                {trend.value}
              </span>
            )}
            {badgeText && (
              <Badge variant={badgeVariant} size="sm">
                {badgeText}
              </Badge>
            )}
          </div>
        </div>

        {subtitle && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>

      {typeof progressValue === 'number' && (
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
            <span>Score Completion</span>
            <span className="font-semibold text-slate-700 dark:text-slate-300">{progressValue}%</span>
          </div>
          <div className="w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${progressColor}`}
              style={{ width: `${Math.min(Math.max(progressValue, 0), 100)}%` }}
            />
          </div>
        </div>
      )}
    </Card>
  );
};
