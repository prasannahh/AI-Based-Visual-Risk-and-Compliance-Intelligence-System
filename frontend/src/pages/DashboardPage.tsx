import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  HeartPulse,
  Brain,
  Wallet,
  Moon,
  GraduationCap,
  Target,
  Sparkles,
  TrendingUp,
  BarChart3,
  CheckCircle2,
  RefreshCw,
  BookOpen,
  GitFork,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import { api } from '../services/api';
import type { DashboardSummaryResponse } from '../types/api';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { usePreferences } from '../context/PreferencesContext';

export const DashboardPage: React.FC = () => {
  const { formatCurrency, formatCompactCurrency, formatDate } = usePreferences();
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [chartMode, setChartMode] = useState<'savings' | 'study'>('savings');

  const fetchData = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const summary = await api.getDashboardSummary();
      setData(summary);
    } catch (err: any) {
      setError(err?.message || 'Unable to retrieve dashboard intelligence from backend.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-10 w-64 bg-slate-200/60 rounded-xl animate-pulse" />
        <LoadingSkeleton />
      </div>
    );
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Dashboard Sync Failed"
        message={error || 'Unable to connect to the Digital Twin backend service.'}
        onRetry={() => fetchData(false)}
      />
    );
  }

  const { user, kpis, goals, savings_trend, study_distribution, twin_insights } = data;

  // Time-aware greeting
  const hour = new Date().getHours();
  const greeting =
    hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  const hasStudyBarData =
    kpis.weekly_study.has_real_data &&
    study_distribution &&
    study_distribution.some((d) => d.hours > 0);

  const hasMultipleDomains =
    (kpis.saved_money.has_real_data ? 1 : 0) +
    (kpis.weekly_study.has_real_data ? 1 : 0) +
    (kpis.health_vitality.has_real_data ? 1 : 0) +
    (goals.length > 0 ? 1 : 0);

  const twinStatusTitle =
    user.days_active >= 3 && hasMultipleDomains >= 2
      ? 'Active Digital Twin'
      : hasMultipleDomains >= 1
      ? 'Learning from Activity'
      : 'Calibrating Twin Models';

  const twinStatusHeadline =
    user.days_active >= 3 && hasMultipleDomains >= 2
      ? 'Your Digital Twin is actively calibrated and forecasting outcomes.'
      : hasMultipleDomains >= 1
      ? 'Your Digital Twin is assimilating logged sessions into behavioral models.'
      : 'Initial calibration state: log activities to sharpen predictive precision.';

  const twinStatusDescription =
    user.days_active >= 3 && hasMultipleDomains >= 2
      ? 'Behavioral models in PostgreSQL are synthesizing financial cash flows, focus rhythms, and active goals into actionable recommendations.'
      : 'Record daily expenses, study hours, or routines to unlock full predictive modeling and simulation fidelity.';

  return (
    <div className="space-y-8">
      {/* 1. Header / Greeting Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Personal Digital Twin
            </span>
            <span className="text-slate-300">•</span>
            <Badge variant="success" size="sm" showDot>
              Online
            </Badge>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900">
            {greeting}, {user.name}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            {user.occupation} · Active for {user.days_active} {user.days_active === 1 ? 'day' : 'days'}. Real-time synchronization with PostgreSQL.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchData(true)}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />}
          >
            {isRefreshing ? 'Syncing...' : 'Sync Twin'}
          </Button>

          <div className="bg-white border border-slate-200/80 rounded-2xl px-4 py-2 shadow-2xs text-right">
            <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              Goal Completion
            </div>
            <div className="text-lg font-bold text-indigo-600 font-sans">
              {kpis.goal_progress.has_real_data ? `${kpis.goal_progress.average_pct}%` : '0%'}
            </div>
          </div>
        </div>
      </div>

      {/* Digital Twin Status Hero Card */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-5 sm:p-6 shadow-sm border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div className="space-y-1.5 max-w-2xl">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                {twinStatusTitle}
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-xs text-slate-300 font-medium">
                Active for {user.days_active} {user.days_active === 1 ? 'day' : 'days'}
              </span>
            </div>
            <h2 className="text-lg sm:text-xl font-bold tracking-tight text-white">
              {twinStatusHeadline}
            </h2>
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {twinStatusDescription}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 lg:flex-col lg:items-end">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 w-full lg:w-auto">
              <div className="px-3 py-2 rounded-xl bg-white/10 backdrop-blur-xs border border-white/10 text-center">
                <div className="text-[10px] text-slate-300 uppercase tracking-wider font-semibold">Finance</div>
                <div className="text-xs font-bold text-white mt-0.5">
                  {kpis.saved_money.has_real_data ? 'Active' : 'Calibrating'}
                </div>
              </div>
              <div className="px-3 py-2 rounded-xl bg-white/10 backdrop-blur-xs border border-white/10 text-center">
                <div className="text-[10px] text-slate-300 uppercase tracking-wider font-semibold">Study</div>
                <div className="text-xs font-bold text-white mt-0.5">
                  {kpis.weekly_study.has_real_data ? 'Modeled' : 'Awaiting'}
                </div>
              </div>
              <div className="px-3 py-2 rounded-xl bg-white/10 backdrop-blur-xs border border-white/10 text-center">
                <div className="text-[10px] text-slate-300 uppercase tracking-wider font-semibold">Vitality</div>
                <div className="text-xs font-bold text-white mt-0.5">
                  {kpis.health_vitality.has_real_data ? 'Monitored' : 'Calibrating'}
                </div>
              </div>
              <div className="px-3 py-2 rounded-xl bg-white/10 backdrop-blur-xs border border-white/10 text-center">
                <div className="text-[10px] text-slate-300 uppercase tracking-wider font-semibold">Simulation</div>
                <div className="text-xs font-bold text-emerald-400 mt-0.5">Ready</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Top-Level Metric Cards Grid (Real Data) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Saved Money KPI */}
        <MetricCard
          title="Total Net Savings"
          value={formatCurrency(kpis.saved_money.total_savings)}
          subtitle={
            kpis.saved_money.has_real_data
              ? kpis.saved_money.monthly_savings >= 0
                ? `+${formatCurrency(kpis.saved_money.monthly_savings)}/mo current rate`
                : `-${formatCurrency(Math.abs(kpis.saved_money.monthly_savings))}/mo deficit`
              : 'Add financial records to model trajectory'
          }
          icon={<Wallet className="w-4 h-4 text-emerald-600" />}
          badgeText={
            kpis.saved_money.has_real_data
              ? kpis.saved_money.monthly_savings >= 0
                ? 'Accumulating'
                : 'Deficit'
              : 'No Records'
          }
          badgeVariant={
            kpis.saved_money.has_real_data
              ? kpis.saved_money.monthly_savings >= 0
                ? 'success'
                : 'danger'
              : 'default'
          }
        />

        {/* Health & Vitality Score */}
        <MetricCard
          title="Health & Vitality"
          value={
            kpis.health_vitality.has_real_data && kpis.health_vitality.score !== null
              ? `${kpis.health_vitality.score} / 100`
              : '— / 100'
          }
          subtitle={
            kpis.health_vitality.has_real_data
              ? `Status: ${kpis.health_vitality.level} vitality rating`
              : 'Awaiting fitness and habit logs'
          }
          icon={<HeartPulse className="w-4 h-4 text-rose-500" />}
          progressValue={
            kpis.health_vitality.has_real_data && kpis.health_vitality.score !== null
              ? kpis.health_vitality.score
              : undefined
          }
          progressColor="bg-rose-500"
          badgeText={
            kpis.health_vitality.has_real_data ? kpis.health_vitality.level : 'Calibration'
          }
          badgeVariant={kpis.health_vitality.has_real_data ? 'purple' : 'default'}
        />

        {/* Cognitive Focus Score */}
        <MetricCard
          title="Cognitive Focus"
          value={
            kpis.cognitive_focus.has_real_data && kpis.cognitive_focus.score !== null
              ? `${kpis.cognitive_focus.score} / 100`
              : '— / 100'
          }
          subtitle={
            kpis.cognitive_focus.has_real_data
              ? `Peak focus window: ${kpis.weekly_study.peak_focus}`
              : 'Log study hours to compute focus rating'
          }
          icon={<Brain className="w-4 h-4 text-indigo-600" />}
          progressValue={
            kpis.cognitive_focus.has_real_data && kpis.cognitive_focus.score !== null
              ? kpis.cognitive_focus.score
              : undefined
          }
          progressColor="bg-indigo-600"
          badgeText={
            kpis.cognitive_focus.has_real_data ? kpis.cognitive_focus.level : 'Awaiting Data'
          }
          badgeVariant={kpis.cognitive_focus.has_real_data ? 'indigo' : 'default'}
        />

        {/* Sleep KPI */}
        <MetricCard
          title="Rest & Sleep"
          value={
            kpis.sleep.has_real_data && kpis.sleep.avg_hours !== null
              ? `${kpis.sleep.avg_hours} hrs`
              : '— hrs'
          }
          subtitle={
            kpis.sleep.has_real_data
              ? kpis.sleep.status
              : 'No sleep records logged yet'
          }
          icon={<Moon className="w-4 h-4 text-indigo-500" />}
          badgeText={kpis.sleep.has_real_data ? kpis.sleep.status : 'No Sleep Logs'}
          badgeVariant={
            kpis.sleep.has_real_data
              ? kpis.sleep.status === 'Healthy Range'
                ? 'success'
                : 'warning'
              : 'default'
          }
        />
      </div>

      {/* 3. Main Analytics & Projections Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trend Chart (Col 1 & 2) */}
        <Card className="lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight">
                  {chartMode === 'savings' ? 'Cumulative Savings Projection' : 'Weekly Study Hours'}
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  {chartMode === 'savings'
                    ? kpis.saved_money.has_real_data
                      ? `12-Month Projected Growth: ${formatCurrency(kpis.saved_money.projected_1yr)}`
                      : 'Deterministic forecast based on monthly savings rate'
                    : `Total Logged This Week: ${kpis.weekly_study.total_hours} hours`}
                </p>
              </div>

              {/* Chart Mode Toggle */}
              <div className="flex bg-slate-100 dark:bg-slate-800 p-1 rounded-xl shrink-0 self-start sm:self-auto">
                <button
                  onClick={() => setChartMode('savings')}
                  className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                    chartMode === 'savings'
                      ? 'bg-white dark:bg-slate-750 text-indigo-700 dark:text-indigo-300 shadow-2xs'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                >
                  <TrendingUp className="w-3.5 h-3.5" />
                  Savings
                </button>
                <button
                  onClick={() => setChartMode('study')}
                  className={`flex items-center gap-1.5 px-3 py-1 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
                    chartMode === 'study'
                      ? 'bg-white dark:bg-slate-750 text-indigo-700 dark:text-indigo-300 shadow-2xs'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5" />
                  Study Hours
                </button>
              </div>
            </div>

            {/* Recharts Component / Real Data Empty State */}
            <div className="h-64 w-full">
              {chartMode === 'savings' ? (
                savings_trend && savings_trend.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={savings_trend} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                      <defs>
                        <linearGradient id="savingsGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" strokeOpacity={0.4} />
                      <XAxis
                        dataKey="date"
                        tickLine={false}
                        axisLine={{ stroke: '#cbd5e1' }}
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                      />
                      <YAxis
                        tickLine={false}
                        axisLine={{ stroke: '#cbd5e1' }}
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                        tickFormatter={(v) => formatCompactCurrency(v)}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          borderRadius: '12px',
                          border: '1px solid #334155',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.2)',
                          fontSize: '12px',
                          color: '#f8fafc',
                        }}
                        itemStyle={{ color: '#818cf8' }}
                        labelStyle={{ color: '#cbd5e1', fontWeight: 600 }}
                        formatter={(val: any) => [formatCurrency(Number(val)), 'Cumulative Savings']}
                      />
                      <Area
                        type="monotone"
                        dataKey="cumulative_savings"
                        stroke="#6366f1"
                        strokeWidth={2.5}
                        fillOpacity={1}
                        fill="url(#savingsGrad)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    icon={<TrendingUp className="w-6 h-6 text-slate-400" />}
                    title="No Savings History Recorded"
                    description="Your financial transactions have not been recorded in PostgreSQL yet. Add your income and expenses to visualize your cumulative savings trajectory."
                    className="h-full justify-center border-dashed"
                  />
                )
              ) : hasStudyBarData ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={study_distribution} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis
                      dataKey="day"
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                    />
                    <YAxis
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                      tick={{ fill: '#94a3b8', fontSize: 11 }}
                      tickFormatter={(v) => `${v}h`}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#ffffff',
                        borderRadius: '12px',
                        border: '1px solid #e2e8f0',
                        fontSize: '12px',
                      }}
                      formatter={(val: any) => [`${val} hrs`, 'Study Hours']}
                    />
                    <Bar dataKey="hours" fill="#6366f1" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState
                  icon={<BookOpen className="w-6 h-6 text-slate-400" />}
                  title="No Study Hours This Week"
                  description="No study sessions have been logged for the current calendar week. Study distribution by day will automatically populate as sessions are recorded."
                  className="h-full justify-center border-dashed"
                />
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Verified with deterministic Python regression model
            </span>
            <span>Forecast Horizon: 12 Months</span>
          </div>
        </Card>

        {/* AI Insights & Twin Intelligence (Col 3) */}
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5" />
                </div>
                <h2 className="text-base font-semibold text-slate-900 tracking-tight">
                  Twin Intelligence
                </h2>
              </div>
              <Badge variant="indigo" size="sm">
                Real-time
              </Badge>
            </div>

            <div className="space-y-3">
              {twin_insights && twin_insights.length > 0 ? (
                twin_insights.map((insight, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-50/80 border border-slate-200/60 transition-all hover:bg-slate-50"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <span className="text-xs font-semibold text-indigo-700">
                        {insight.category}
                      </span>
                      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400">
                        {insight.priority}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed">{insight.text}</p>
                    {insight.action && (
                      <div className="mt-2 text-[11px] font-medium text-slate-500 flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
                        {insight.action}
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="p-4 text-xs text-slate-500 bg-slate-50 rounded-xl text-center">
                  Twin model calibrated. Insights will generate as records are added.
                </div>
              )}
            </div>

            <div className="mt-3 text-right">
              <Link
                to="/suggestions"
                className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors inline-flex items-center gap-1"
              >
                Explore all recommendations →
              </Link>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400 text-center">
            Insights generated from active simulations and behavioral tracking.
          </div>
        </Card>
      </div>

      {/* 4. What-If Decision Simulation Gateway */}
      <Card className="p-6 bg-gradient-to-br from-indigo-50/70 via-white to-purple-50/50 border-indigo-100/90 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div className="space-y-2 max-w-2xl">
            <div className="flex items-center gap-2">
              <Badge variant="indigo" size="sm">
                Future Outcome Simulation
              </Badge>
              <Badge variant="purple" size="sm">
                Decision Assistant
              </Badge>
            </div>
            <h3 className="text-lg font-bold text-slate-900 tracking-tight">
              Test Decisions Before You Make Them in Real Life
            </h3>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
              Your Digital Twin models how adjusted monthly savings, altered study schedules, and fitness routines influence your 12–36 month outcomes. Compare scenarios side-by-side with trade-off rankings.
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link to="/simulation">
              <Button variant="primary" size="md" className="flex items-center gap-2 shadow-xs">
                <GitFork className="w-4 h-4" />
                Explore Future Scenarios →
              </Button>
            </Link>
          </div>
        </div>
      </Card>

      {/* 5. Goals & Weekly Academic Summary Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Goal Progress Section (2 cols) */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-indigo-600" />
              <h2 className="text-base font-semibold text-slate-900 tracking-tight">
                Active Financial & Life Goals
              </h2>
            </div>
            <span className="text-xs text-slate-400 font-medium">
              {goals.length} {goals.length === 1 ? 'goal tracked' : 'goals tracked'}
            </span>
          </div>

          {goals && goals.length > 0 ? (
            <div className="space-y-4">
              {goals.map((g) => (
                <div key={g.goal_id} className="p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-800/40">
                  <div className="flex items-center justify-between text-sm mb-1.5">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{g.goal_name}</span>
                    <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400">
                      {formatCurrency(g.current_progress)} / {formatCurrency(g.target_amount)} ({g.progress_pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-slate-200/80 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                      style={{ width: `${g.progress_pct}%` }}
                    />
                  </div>
                  {g.target_date && (
                    <div className="mt-1.5 text-[11px] text-slate-400 dark:text-slate-500">
                      Target Date: {formatDate(g.target_date)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              icon={<Target className="w-6 h-6 text-slate-400" />}
              title="No Goals Currently Set"
              description="You have not created any goals yet. Add target savings or academic milestones in Profile & Goals to monitor your progress here."
              className="py-8 bg-slate-50/50 border-dashed"
            />
          )}
        </Card>

        {/* Academic Quick Stat Card (1 col) */}
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <GraduationCap className="w-4 h-4 text-indigo-600" />
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 tracking-tight">
                Academic Rhythm
              </h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Logged Study Hours</span>
                <span className="text-sm font-bold text-slate-900 dark:text-slate-100">{kpis.weekly_study.total_hours} hrs</span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Peak Concentration</span>
                <span className="text-xs font-semibold text-indigo-700 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/60 px-2 py-0.5 rounded">
                  {kpis.weekly_study.peak_focus}
                </span>
              </div>

              <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
                <span className="text-xs text-slate-600 dark:text-slate-400 font-medium">Performance Rating</span>
                <span className="text-sm font-bold text-emerald-700 dark:text-emerald-400">
                  {kpis.cognitive_focus.has_real_data && kpis.cognitive_focus.score !== null
                    ? `${kpis.cognitive_focus.score} / 100`
                    : 'Awaiting Data'}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400 text-center">
            Derived from historical performance scores & study logs.
          </div>
        </Card>
      </div>
    </div>
  );
};
