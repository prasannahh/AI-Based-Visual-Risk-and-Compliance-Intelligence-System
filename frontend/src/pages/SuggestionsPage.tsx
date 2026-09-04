import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  BookOpen,
  LineChart,
  CalendarCheck,
  Target,
  HeartPulse,
  Dumbbell,
  ShieldAlert,
  GitFork,
  Check,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  SuggestionItem,
  SuggestionsResponse,
} from '../types/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import type { BadgeVariant } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorState } from '../components/ui/ErrorState';

export const SuggestionsPage: React.FC = () => {
  const [data, setData] = useState<SuggestionsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedPriority, setSelectedPriority] = useState<string>('All');

  const fetchSuggestions = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const resp = await api.getSuggestions();
      setData(resp);
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve recommendations from the decision engine.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const getPriorityBadgeVariant = (priority: string): BadgeVariant => {
    switch (priority.toLowerCase()) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'warning';
      case 'medium':
        return 'purple';
      case 'low':
      default:
        return 'default';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case 'study':
        return <BookOpen className="w-4 h-4 text-indigo-600" />;
      case 'finance':
        return <LineChart className="w-4 h-4 text-emerald-600" />;
      case 'health':
        return <HeartPulse className="w-4 h-4 text-rose-600" />;
      case 'fitness':
        return <Dumbbell className="w-4 h-4 text-amber-600" />;
      case 'habits':
        return <CalendarCheck className="w-4 h-4 text-purple-600" />;
      case 'goals':
        return <Target className="w-4 h-4 text-cyan-600" />;
      case 'simulation':
        return <GitFork className="w-4 h-4 text-indigo-600" />;
      default:
        return <Sparkles className="w-4 h-4 text-indigo-600" />;
    }
  };

  const filteredSuggestions = useMemo(() => {
    if (!data?.suggestions) return [];
    return data.suggestions.filter((item: SuggestionItem) => {
      const matchCat =
        selectedCategory === 'All' ||
        item.category.toLowerCase() === selectedCategory.toLowerCase();
      const matchPrio =
        selectedPriority === 'All' ||
        item.priority.toLowerCase() === selectedPriority.toLowerCase();
      return matchCat && matchPrio;
    });
  }, [data?.suggestions, selectedCategory, selectedPriority]);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="p-6">
        <ErrorState
          title="Suggestions Engine Error"
          message={error}
          onRetry={() => fetchSuggestions()}
        />
      </div>
    );
  }

  const hasData = data?.has_data ?? false;
  const suggestions = data?.suggestions ?? [];
  const priorityCounts = data?.priority_counts ?? {
    Critical: 0,
    High: 0,
    Medium: 0,
    Low: 0,
  };
  const categories = data?.categories ?? [];
  const calibrationState = data?.calibration_state;

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Suggestions & Recommendations
            </h1>
            <Badge variant="indigo" size="sm">
              Twin Engine
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Personalized, actionable guidance synthesized deterministically from your active Digital Twin data
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchSuggestions(true)}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />}
          >
            Refresh Suggestions
          </Button>
        </div>
      </div>

      {/* 2. Priority & Category Summary Bar */}
      {hasData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Card className="p-4 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-rose-600 block">
                Critical Priority
              </span>
              <span className="text-xl font-bold text-slate-900 font-sans">
                {priorityCounts.Critical}
              </span>
            </div>
            <div className="w-8 h-8 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-600">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </Card>

          <Card className="p-4 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-amber-600 block">
                High Priority
              </span>
              <span className="text-xl font-bold text-slate-900 font-sans">
                {priorityCounts.High}
              </span>
            </div>
            <div className="w-8 h-8 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </Card>

          <Card className="p-4 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-purple-600 block">
                Medium Priority
              </span>
              <span className="text-xl font-bold text-slate-900 font-sans">
                {priorityCounts.Medium}
              </span>
            </div>
            <div className="w-8 h-8 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
              <Sparkles className="w-4 h-4" />
            </div>
          </Card>

          <Card className="p-4 flex items-center justify-between">
            <div>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Total Active
              </span>
              <span className="text-xl font-bold text-slate-900 font-sans">
                {data?.total_count ?? 0}
              </span>
            </div>
            <div className="w-8 h-8 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center text-slate-600">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </Card>
        </div>
      )}

      {/* 3. Filters Row (Rendered when suggestions exist) */}
      {hasData && (
        <Card className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-slate-50/50">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-500 mr-1">Category:</span>
            <button
              onClick={() => setSelectedCategory('All')}
              className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors ${
                selectedCategory === 'All'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
              }`}
            >
              All ({suggestions.length})
            </button>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 text-xs font-medium rounded-lg transition-colors ${
                  selectedCategory.toLowerCase() === cat.toLowerCase()
                    ? 'bg-indigo-600 text-white shadow-xs'
                    : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <span className="text-xs font-semibold text-slate-500">Priority:</span>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none"
            >
              <option value="All">All Priorities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </Card>
      )}

      {/* 4. Suggestions List or Calibration State */}
      {hasData && filteredSuggestions.length > 0 ? (
        <div className="space-y-4">
          {filteredSuggestions.map((item: SuggestionItem) => (
            <Card
              key={item.id}
              className="p-5 border-slate-200 hover:border-indigo-200 transition-all shadow-xs"
            >
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                {/* Main Content */}
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="p-1 rounded-md bg-slate-100 border border-slate-200">
                      {getCategoryIcon(item.category)}
                    </span>
                    <Badge variant="default" size="sm">
                      {item.category}
                    </Badge>
                    <Badge variant={getPriorityBadgeVariant(item.priority)} size="sm" showDot>
                      {item.priority} Priority
                    </Badge>
                  </div>

                  <h3 className="text-base font-semibold text-slate-900 tracking-tight">
                    {item.title}
                  </h3>

                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                    {item.description}
                  </p>

                  {/* Supporting Evidence Chips */}
                  {item.evidence && Object.keys(item.evidence).length > 0 && (
                    <div className="pt-2 flex flex-wrap items-center gap-2">
                      <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                        Evidence:
                      </span>
                      {Object.entries(item.evidence).map(([key, val]) => (
                        <span
                          key={key}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[11px] font-mono border border-slate-200/80"
                        >
                          <span className="text-slate-400">{key}:</span>
                          <span className="font-semibold text-slate-700">{String(val)}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Benefits and Risks */}
                  {(item.benefits.length > 0 || item.risks.length > 0) && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-slate-100 text-xs">
                      {item.benefits.length > 0 && (
                        <div className="space-y-1">
                          <span className="font-semibold text-emerald-700 flex items-center gap-1 text-[11px] uppercase tracking-wider">
                            <Check className="w-3 h-3" /> Projected Benefit
                          </span>
                          {item.benefits.map((b, idx) => (
                            <p key={idx} className="text-slate-600 leading-normal pl-4">
                              • {b}
                            </p>
                          ))}
                        </div>
                      )}

                      {item.risks.length > 0 && (
                        <div className="space-y-1">
                          <span className="font-semibold text-amber-700 flex items-center gap-1 text-[11px] uppercase tracking-wider">
                            <AlertTriangle className="w-3 h-3" /> Trade-off / Risk
                          </span>
                          {item.risks.map((r, idx) => (
                            <p key={idx} className="text-slate-600 leading-normal pl-4">
                              • {r}
                            </p>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Recommended Action / Button */}
                {item.action && (
                  <div className="md:w-64 shrink-0 flex flex-col justify-between pt-3 md:pt-0 md:pl-4 border-t md:border-t-0 md:border-l border-slate-100 space-y-3">
                    <div>
                      <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-600 block mb-1">
                        Recommended Action
                      </span>
                      <p className="text-xs text-slate-700 font-medium leading-normal">
                        {item.action}
                      </p>
                    </div>

                    {item.action_route && (
                      <Link to={item.action_route} className="inline-block">
                        <Button
                          variant="soft"
                          size="sm"
                          className="w-full justify-between"
                          rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                        >
                          {item.action_label || 'Take Action'}
                        </Button>
                      </Link>
                    )}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      ) : hasData && filteredSuggestions.length === 0 ? (
        <Card className="p-8 text-center bg-slate-50/50 border-dashed border-slate-200">
          <p className="text-sm font-semibold text-slate-700">
            No suggestions match the selected filter.
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Try adjusting your category or priority selection above.
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setSelectedCategory('All');
              setSelectedPriority('All');
            }}
            className="mt-4"
          >
            Reset Filters
          </Button>
        </Card>
      ) : (
        /* Honest Calibration / Empty State */
        <div className="space-y-6">
          <Card className="p-8 text-center border-indigo-100 bg-gradient-to-br from-white via-indigo-50/20 to-purple-50/20">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-4 border border-indigo-100">
              <Sparkles className="w-6 h-6" />
            </div>

            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Your Digital Twin is Calibrating
            </h2>

            <p className="text-xs sm:text-sm text-slate-600 max-w-lg mx-auto mt-2 leading-relaxed">
              {calibrationState?.message ||
                'Keep logging activities across your workspace to unlock personalized recommendations.'}
            </p>

            {calibrationState?.missing_data && calibrationState.missing_data.length > 0 && (
              <div className="mt-4 inline-flex flex-wrap items-center justify-center gap-1.5 max-w-md">
                <span className="text-xs text-slate-400 font-medium mr-1">Awaiting data in:</span>
                {calibrationState.missing_data.map((domain: string) => (
                  <span
                    key={domain}
                    className="px-2.5 py-0.5 rounded-full bg-white border border-slate-200 text-slate-600 text-xs font-medium"
                  >
                    {domain}
                  </span>
                ))}
              </div>
            )}
          </Card>

          {/* Actionable Unlocking Capabilities */}
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-3 tracking-tight">
              Available Actions to Unlock Twin Recommendations
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {calibrationState?.unlock_actions.map((act) => (
                <Card
                  key={act.route}
                  className="p-5 hover:border-indigo-200 transition-all flex flex-col justify-between"
                >
                  <div className="space-y-2 mb-4">
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                      {act.route === '/study' && <BookOpen className="w-4 h-4" />}
                      {act.route === '/tasks' && <CalendarCheck className="w-4 h-4" />}
                      {act.route === '/profile' && <Target className="w-4 h-4" />}
                    </div>
                    <h4 className="text-sm font-semibold text-slate-900">{act.title}</h4>
                    <p className="text-xs text-slate-500 leading-relaxed">{act.description}</p>
                  </div>

                  <Link to={act.route} className="block">
                    <Button
                      variant="secondary"
                      size="sm"
                      className="w-full justify-between"
                      rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                    >
                      {act.label}
                    </Button>
                  </Link>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
