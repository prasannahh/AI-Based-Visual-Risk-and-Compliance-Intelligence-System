import React from 'react';
import { Card } from './Card';
import { Button } from './Button';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Failed to load data',
  message,
  onRetry,
  className = '',
}) => {
  return (
    <Card className={`border-rose-200/80 dark:border-rose-900/60 bg-rose-50/30 dark:bg-rose-950/20 text-center py-10 px-6 flex flex-col items-center justify-center ${className}`}>
      <div className="w-10 h-10 rounded-2xl bg-rose-100/70 dark:bg-rose-900/50 text-rose-600 dark:text-rose-400 flex items-center justify-center mb-3">
        <AlertTriangle className="w-5 h-5" />
      </div>
      <h3 className="text-sm font-semibold text-rose-900 dark:text-rose-200 mb-1">{title}</h3>
      <p className="text-xs text-rose-700/80 dark:text-rose-300/80 max-w-sm mb-4 leading-relaxed">{message}</p>
      {onRetry && (
        <Button
          variant="secondary"
          size="sm"
          onClick={onRetry}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Try Again
        </Button>
      )}
    </Card>
  );
};
