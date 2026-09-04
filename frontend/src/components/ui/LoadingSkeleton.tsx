import React from 'react';
import { Card } from './Card';

export const LoadingSkeleton: React.FC<{ rows?: number }> = ({ rows = 3 }) => {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="h-32 bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/60 dark:border-slate-800/60">
            <div className="w-24 h-4 bg-slate-200 dark:bg-slate-800 rounded mb-4" />
            <div className="w-36 h-8 bg-slate-200 dark:bg-slate-800 rounded mb-2" />
            <div className="w-20 h-3 bg-slate-200 dark:bg-slate-800 rounded" />
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 h-80 bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/60 dark:border-slate-800/60">
          <div className="w-32 h-5 bg-slate-200 dark:bg-slate-800 rounded mb-4" />
          <div className="w-full h-56 bg-slate-200/70 dark:bg-slate-800/60 rounded" />
        </Card>
        <Card className="h-80 bg-slate-50/70 dark:bg-slate-800/40 border-slate-200/60 dark:border-slate-800/60">
          <div className="w-28 h-5 bg-slate-200 dark:bg-slate-800 rounded mb-4" />
          <div className="space-y-3">
            {Array.from({ length: rows }).map((_, i) => (
              <div key={i} className="w-full h-12 bg-slate-200/60 dark:bg-slate-800/60 rounded-xl" />
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};
