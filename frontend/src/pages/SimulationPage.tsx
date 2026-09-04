import React, { useEffect, useMemo, useState } from 'react';
import {
  Sparkles,
  TrendingUp,
  Wallet,
  GraduationCap,
  Activity,
  Calendar,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sliders,
  History,
  BookmarkPlus,
  ArrowRight,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Info,
  Check,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { api } from '../services/api';
import type {
  SimulationDomain,
  SimulationBaselineResponse,
  RunSimulationResponse,
  SimulationHistoryItem,
} from '../types/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { MetricCard } from '../components/ui/MetricCard';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { usePreferences } from '../context/PreferencesContext';

const SCENARIO_COLORS = [
  '#0d9488', // Teal (Baseline)
  '#6366f1', // Indigo
  '#ec4899', // Pink
  '#f59e0b', // Amber
  '#8b5cf6', // Violet
  '#10b981', // Emerald
];

export const SimulationPage: React.FC = () => {
  const { formatCurrency, formatCompactCurrency, formatDate, currencySymbol } = usePreferences();
  // Domain selection
  const [domain, setDomain] = useState<SimulationDomain>('finance');
  const [horizonMonths, setHorizonMonths] = useState<number>(12);

  // Baseline state
  const [baseline, setBaseline] = useState<SimulationBaselineResponse | null>(null);
  const [loadingBaseline, setLoadingBaseline] = useState<boolean>(true);
  const [baselineError, setBaselineError] = useState<string | null>(null);

  // Custom scenario input state
  const [useCustomScenario, setUseCustomScenario] = useState<boolean>(false);
  const [customName, setCustomName] = useState<string>('Custom Plan');
  const [customSaving, setCustomSaving] = useState<number>(15000);
  const [customExpenses, setCustomExpenses] = useState<number>(35000);
  const [customHours, setCustomHours] = useState<number>(4.0);
  const [studyConsistency, setStudyConsistency] = useState<number>(0.7);
  const [customCompletionRate, setCustomCompletionRate] = useState<number>(80);
  const [customExerciseFreq, setCustomExerciseFreq] = useState<number>(4);

  // Simulation execution state
  const [simResult, setSimResult] = useState<RunSimulationResponse | null>(null);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [simError, setSimError] = useState<string | null>(null);

  // Save simulation state
  const [savingSim, setSavingSim] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // History state
  const [historyOpen, setHistoryOpen] = useState<boolean>(false);
  const [historyList, setHistoryList] = useState<SimulationHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState<boolean>(false);

  // Expandable details
  const [showTable, setShowTable] = useState<boolean>(true);

  // Load baseline on mount
  const fetchBaseline = async () => {
    try {
      setLoadingBaseline(true);
      setBaselineError(null);
      const res = await api.getSimulationBaseline();
      setBaseline(res);

      // Pre-fill custom fields based on real baseline
      if (res.financial) {
        setCustomSaving(res.financial.monthly_savings || 15000);
        setCustomExpenses(res.financial.monthly_expenses || 35000);
      }
      if (res.study) {
        setCustomHours(res.study.avg_hours_per_day || 4.0);
      }
      if (res.habits) {
        setCustomCompletionRate(Math.round(res.habits.avg_completion_rate || 75));
        setCustomExerciseFreq(res.habits.exercise_frequency || 3);
      }
    } catch (err: any) {
      setBaselineError(err.message || 'Failed to retrieve Digital Twin baseline.');
    } finally {
      setLoadingBaseline(false);
    }
  };

  useEffect(() => {
    fetchBaseline();
  }, []);

  // Fetch history when history panel opens
  const fetchHistory = async () => {
    try {
      setLoadingHistory(true);
      const items = await api.getSimulationHistory(domain);
      setHistoryList(items);
    } catch (err) {
      console.error('Failed to load simulation history', err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleOpenHistory = () => {
    setHistoryOpen(!historyOpen);
    if (!historyOpen) {
      fetchHistory();
    }
  };

  // Run simulation handler
  const handleRunSimulation = async () => {
    try {
      setSimulating(true);
      setSimError(null);
      setSaveSuccessMsg(null);

      const customScenarios = useCustomScenario
        ? [
            {
              name: customName.trim() || 'Custom Scenario',
              description: `User-defined ${domain} plan`,
              ...(domain === 'finance'
                ? { monthly_saving: customSaving, monthly_expenses: customExpenses }
                : {}),
              ...(domain === 'study' ? { hours_per_day: customHours } : {}),
              ...(domain === 'habits'
                ? {
                    completion_rate: customCompletionRate,
                    exercise_frequency: customExerciseFreq,
                  }
                : {}),
            },
          ]
        : undefined;

      const result = await api.runSimulation({
        domain,
        horizon_months: horizonMonths,
        consistency: domain === 'study' ? studyConsistency : undefined,
        custom_scenarios: customScenarios,
      });

      setSimResult(result);
    } catch (err: any) {
      setSimError(err.message || 'Error running simulation. Please verify input parameters.');
    } finally {
      setSimulating(false);
    }
  };

  // Run simulation automatically when baseline loads or domain changes
  useEffect(() => {
    if (baseline) {
      handleRunSimulation();
    }
  }, [domain, baseline]);

  // Save simulation handler
  const handleSaveSimulation = async () => {
    if (!simResult) return;
    try {
      setSavingSim(true);
      setSaveSuccessMsg(null);
      const title = `${domain.toUpperCase()} Scenario — ${horizonMonths}M Horizon`;
      const res = await api.saveSimulation({
        domain,
        title,
        horizon_months: horizonMonths,
        scenarios: simResult.scenarios,
        recommendation: simResult.recommendation,
        parameters: {
          horizon_months: horizonMonths,
          use_custom: useCustomScenario,
          consistency: domain === 'study' ? studyConsistency : undefined,
        },
      });
      setSaveSuccessMsg(res.message);
      if (historyOpen) {
        fetchHistory();
      }
    } catch (err: any) {
      alert(`Could not save simulation: ${err.message || 'Unknown error'}`);
    } finally {
      setSavingSim(false);
    }
  };

  // Calibration check for current domain
  const currentDomainBaseline = useMemo(() => {
    if (!baseline) return null;
    if (domain === 'finance') return baseline.financial;
    if (domain === 'study') return baseline.study;
    return baseline.habits;
  }, [baseline, domain]);

  const hasCalibrationData = currentDomainBaseline?.has_data ?? true;

  // Transform time series data for Recharts
  const chartData = useMemo(() => {
    if (!simResult || !simResult.scenarios || simResult.scenarios.length === 0) {
      return [];
    }
    const points: Array<Record<string, any>> = [];
    const maxMonths = simResult.horizon_months;

    for (let m = 1; m <= maxMonths; m++) {
      const entry: Record<string, any> = { month: `M${m}`, monthNum: m };
      simResult.scenarios.forEach((s) => {
        const seriesPoint = s.time_series.find((p) => p.month === m);
        if (seriesPoint) {
          if (domain === 'finance') {
            entry[s.name] = seriesPoint.balance;
          } else if (domain === 'study') {
            entry[s.name] = seriesPoint.projected_score;
          } else if (domain === 'habits') {
            entry[s.name] = seriesPoint.projected_fitness_score;
          }
        }
      });
      points.push(entry);
    }
    return points;
  }, [simResult, domain]);

  if (loadingBaseline && !baseline) {
    return <LoadingSkeleton rows={4} />;
  }

  if (baselineError && !baseline) {
    return (
      <ErrorState
        title="Failed to Load Digital Twin Baseline"
        message={baselineError}
        onRetry={fetchBaseline}
      />
    );
  }

  return (
    <div className="space-y-8 pb-16">
      {/* ----------------- Header ----------------- */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200/80 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-sans">
              What-If Simulator
            </h1>
            <Badge variant="indigo" size="sm" showDot>
              Decision Modeling
            </Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Explore how adjusting your savings, study intensity, or habits could impact your Digital
            Twin future projections.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={handleOpenHistory}
            className="flex items-center gap-1.5"
          >
            <History className="w-4 h-4 text-slate-500" />
            <span>{historyOpen ? 'Hide History' : 'Saved Scenarios'}</span>
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={fetchBaseline}
            disabled={loadingBaseline}
            className="flex items-center gap-1.5"
          >
            <RotateCcw
              className={`w-3.5 h-3.5 text-slate-500 ${loadingBaseline ? 'animate-spin' : ''}`}
            />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {/* ----------------- Saved History Drawer (Toggleable) ----------------- */}
      {historyOpen && (
        <Card className="p-4 bg-slate-50 border border-indigo-100 shadow-sm transition-all duration-300">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-600" />
              <h3 className="text-sm font-semibold text-slate-900">
                Saved Digital Twin Simulations ({historyList.length})
              </h3>
            </div>
            <span className="text-xs text-slate-500">Filtered by {domain}</span>
          </div>

          {loadingHistory ? (
            <LoadingSkeleton rows={1} />
          ) : historyList.length === 0 ? (
            <div className="text-xs text-slate-500 py-3 text-center">
              No saved simulations found for this domain. Run a scenario and click &quot;Save
              Simulation&quot; below to track decisions.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {historyList.map((item) => (
                <div
                  key={item.simulation_id}
                  className="bg-white p-3 rounded-lg border border-slate-200/80 shadow-xs flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <span className="text-xs font-semibold text-slate-800 line-clamp-1">
                        {item.title}
                      </span>
                      <Badge variant="default" size="sm">
                        {item.horizon_months}M
                      </Badge>
                    </div>
                    <p className="text-[11px] text-slate-500">
                      Saved on {formatDate(item.created_at)}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {/* ----------------- Domain Selector Tabs ----------------- */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          type="button"
          onClick={() => {
            setDomain('finance');
            setHorizonMonths(12);
          }}
          className={`flex items-center gap-3 p-4 rounded-xl border text-left transition-all ${
            domain === 'finance'
              ? 'bg-emerald-50/60 border-emerald-500 ring-2 ring-emerald-500/20 shadow-xs'
              : 'bg-white border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/50'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              domain === 'finance'
                ? 'bg-emerald-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            <Wallet className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900">Financial Planning</div>
            <p className="text-xs text-slate-500 mt-0.5">
              Savings, expense cuts, surpluses &amp; goals
            </p>
          </div>
        </button>

        <button
          type="button"
          onClick={() => {
            setDomain('study');
            setHorizonMonths(6);
          }}
          className={`flex items-center gap-3 p-4 rounded-xl border text-left transition-all ${
            domain === 'study'
              ? 'bg-indigo-50/60 border-indigo-500 ring-2 ring-indigo-500/20 shadow-xs'
              : 'bg-white border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/50'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              domain === 'study'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            <GraduationCap className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900">Study &amp; Academics</div>
            <p className="text-xs text-slate-500 mt-0.5">
              Daily hours, exam projections &amp; consistency
            </p>
          </div>
        </button>

        <button
          type="button"
          onClick={() => {
            setDomain('habits');
            setHorizonMonths(6);
          }}
          className={`flex items-center gap-3 p-4 rounded-xl border text-left transition-all ${
            domain === 'habits'
              ? 'bg-rose-50/60 border-rose-500 ring-2 ring-rose-500/20 shadow-xs'
              : 'bg-white border-slate-200/80 hover:border-slate-300 hover:bg-slate-50/50'
          }`}
        >
          <div
            className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
              domain === 'habits'
                ? 'bg-rose-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600'
            }`}
          >
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-semibold text-slate-900">Habit &amp; Fitness</div>
            <p className="text-xs text-slate-500 mt-0.5">
              Workout frequency, completion &amp; health score
            </p>
          </div>
        </button>
      </div>

      {/* ----------------- Uncalibrated Honest State Notice ----------------- */}
      {!hasCalibrationData && (
        <div className="p-4 rounded-xl border border-amber-200 bg-amber-50/70 text-amber-900 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed">
            <span className="font-semibold block text-sm mb-0.5">
              Limited Baseline Data Calibrated
            </span>
            Your Digital Twin has not yet recorded sufficient activity in this domain. Projections
            are currently utilizing fallback baselines. Log your activities in the workspace to
            unlock high-fidelity, personalized predictions.
          </div>
        </div>
      )}

      {/* ----------------- Current Baseline State ----------------- */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Current Recorded Baseline
            </span>
            <Badge variant="default" size="sm">
              Source of Truth
            </Badge>
          </div>
          <span className="text-xs text-slate-500">PostgreSQL Verified</span>
        </div>

        {domain === 'finance' && baseline?.financial && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard
              title="Monthly Income"
              value={formatCurrency(baseline.financial.monthly_income)}
              subtitle="Average monthly intake"
              icon={<Wallet className="w-4 h-4 text-emerald-600" />}
            />
            <MetricCard
              title="Monthly Expenses"
              value={formatCurrency(baseline.financial.monthly_expenses)}
              subtitle="Current baseline outflow"
              icon={<TrendingUp className="w-4 h-4 text-rose-600" />}
            />
            <MetricCard
              title="Monthly Savings"
              value={formatCurrency(baseline.financial.monthly_savings)}
              subtitle="Net monthly accumulation"
              icon={<Sparkles className="w-4 h-4 text-indigo-600" />}
            />
            <MetricCard
              title="Total Savings Pool"
              value={formatCurrency(baseline.financial.total_savings)}
              subtitle="Current recorded reserve"
              icon={<Activity className="w-4 h-4 text-teal-600" />}
            />
          </div>
        )}

        {domain === 'study' && baseline?.study && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard
              title="Daily Study Hours"
              value={`${baseline.study.avg_hours_per_day.toFixed(1)}h`}
              subtitle="Average recorded study rate"
              icon={<GraduationCap className="w-4 h-4 text-indigo-600" />}
            />
            <MetricCard
              title="Avg Performance"
              value={`${baseline.study.avg_performance_score.toFixed(0)}/100`}
              subtitle="Benchmark test scores"
              icon={<Sparkles className="w-4 h-4 text-amber-600" />}
            />
            <MetricCard
              title="Enrolled Subjects"
              value={baseline.study.subjects.length}
              subtitle={
                baseline.study.subjects.slice(0, 2).join(', ') || 'No active subjects logged'
              }
              icon={<Calendar className="w-4 h-4 text-teal-600" />}
            />
            <MetricCard
              title="Days Active"
              value={baseline.study.days_active}
              subtitle="Recorded study sessions"
              icon={<Activity className="w-4 h-4 text-slate-600" />}
            />
          </div>
        )}

        {domain === 'habits' && baseline?.habits && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <MetricCard
              title="Habit Completion"
              value={`${baseline.habits.avg_completion_rate.toFixed(0)}%`}
              subtitle="Consistency score"
              icon={<CheckCircle2 className="w-4 h-4 text-emerald-600" />}
            />
            <MetricCard
              title="Workout Frequency"
              value={`${baseline.habits.exercise_frequency} d/wk`}
              subtitle="Weekly active sessions"
              icon={<Activity className="w-4 h-4 text-rose-600" />}
            />
            <MetricCard
              title="Daily Step Count"
              value={baseline.habits.avg_steps.toLocaleString()}
              subtitle="Average recorded steps"
              icon={<TrendingUp className="w-4 h-4 text-indigo-600" />}
            />
            <MetricCard
              title="Sleep Duration"
              value={`${baseline.habits.avg_sleep_hours.toFixed(1)}h`}
              subtitle="Rest & recovery average"
              icon={<Calendar className="w-4 h-4 text-purple-600" />}
            />
          </div>
        )}
      </div>

      {/* ----------------- Scenario Controls Card ----------------- */}
      <Card className="p-6 border-slate-200/80 shadow-xs bg-white">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4 mb-6">
          <div>
            <h2 className="text-base font-semibold text-slate-900 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-indigo-600" />
              Configure Scenario Parameters
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select your forecast horizon and benchmark against automatic or custom target
              assumptions.
            </p>
          </div>

          {/* Mode switch */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => setUseCustomScenario(false)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                !useCustomScenario
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Benchmark Scenarios
            </button>
            <button
              type="button"
              onClick={() => setUseCustomScenario(true)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                useCustomScenario
                  ? 'bg-white text-slate-900 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Custom Target
            </button>
          </div>
        </div>

        {/* Forecast Horizon Selector */}
        <div className="space-y-3 mb-6">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
              Forecast Horizon: <span className="text-indigo-600 font-bold">{horizonMonths} Months</span>
            </label>
            <div className="flex gap-1.5">
              {[3, 6, 12, 24, 36].map((h) => (
                <button
                  key={h}
                  type="button"
                  onClick={() => setHorizonMonths(h)}
                  className={`px-2.5 py-0.5 text-xs font-medium rounded-full transition-all ${
                    horizonMonths === h
                      ? 'bg-indigo-600 text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {h}M
                </button>
              ))}
            </div>
          </div>
          <input
            type="range"
            min={1}
            max={60}
            step={1}
            value={horizonMonths}
            onChange={(e) => setHorizonMonths(Number(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
        </div>

        {/* Custom scenario parameters */}
        {useCustomScenario ? (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 mb-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Custom Scenario Variables
              </span>
              <input
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="Scenario Name"
                className="text-xs px-2.5 py-1 bg-white border border-slate-200 rounded-md text-slate-800 font-medium focus:outline-hidden focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            {domain === 'finance' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">Simulated Monthly Savings</span>
                    <span className="font-semibold text-emerald-700">
                      {formatCurrency(customSaving)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100000}
                    step={1000}
                    value={customSaving}
                    onChange={(e) => setCustomSaving(Number(e.target.value))}
                    className="w-full accent-emerald-600 cursor-pointer"
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">Simulated Monthly Expenses</span>
                    <span className="font-semibold text-rose-700">
                      {formatCurrency(customExpenses)}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100000}
                    step={1000}
                    value={customExpenses}
                    onChange={(e) => setCustomExpenses(Number(e.target.value))}
                    className="w-full accent-rose-600 cursor-pointer"
                  />
                </div>
              </div>
            )}

            {domain === 'study' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">Daily Study Hours</span>
                    <span className="font-semibold text-indigo-700">
                      {customHours.toFixed(1)} hrs/day
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0.5}
                    max={14.0}
                    step={0.5}
                    value={customHours}
                    onChange={(e) => setCustomHours(Number(e.target.value))}
                    className="w-full accent-indigo-600 cursor-pointer"
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">Study Consistency Modeling</span>
                    <span className="font-semibold text-amber-700">
                      {Math.round(studyConsistency * 100)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min={0.1}
                    max={1.0}
                    step={0.05}
                    value={studyConsistency}
                    onChange={(e) => setStudyConsistency(Number(e.target.value))}
                    className="w-full accent-amber-600 cursor-pointer"
                  />
                </div>
              </div>
            )}

            {domain === 'habits' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">Target Habit Completion</span>
                    <span className="font-semibold text-emerald-700">{customCompletionRate}%</span>
                  </div>
                  <input
                    type="range"
                    min={10}
                    max={100}
                    step={5}
                    value={customCompletionRate}
                    onChange={(e) => setCustomCompletionRate(Number(e.target.value))}
                    className="w-full accent-emerald-600 cursor-pointer"
                  />
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-600">Exercise Frequency</span>
                    <span className="font-semibold text-rose-700">{customExerciseFreq} days/wk</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={7}
                    step={1}
                    value={customExerciseFreq}
                    onChange={(e) => setCustomExerciseFreq(Number(e.target.value))}
                    className="w-full accent-rose-600 cursor-pointer"
                  />
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200/60 mb-6 text-xs text-slate-600 flex items-center gap-2">
            <Info className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>
              The Digital Twin will generate 4 comparative scenarios: your{' '}
              <strong>Recorded Baseline</strong> plus 3 automated optimization trajectories.
            </span>
          </div>
        )}

        {/* Primary Action Button */}
        <div className="flex items-center justify-between">
          <div className="text-xs text-slate-500">
            Calculations run deterministically via Python backend engine.
          </div>
          <Button
            variant="primary"
            onClick={handleRunSimulation}
            disabled={simulating}
            className="flex items-center gap-2 px-6"
          >
            <Sparkles className="w-4 h-4 text-white" />
            <span>{simulating ? 'Simulating...' : 'Run Simulation'}</span>
          </Button>
        </div>

        {simError && (
          <div className="mt-4 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{simError}</span>
          </div>
        )}
      </Card>

      {/* ----------------- Simulation Results ----------------- */}
      {simResult && (
        <div className="space-y-8 animate-fadeIn">
          {/* Top Result Banner */}
          <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-indigo-950 text-white shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase font-bold tracking-wider text-indigo-300">
                  Projected Scenario Outcome
                </span>
                <Badge variant="indigo" size="sm">
                  {simResult.horizon_months}M Horizon
                </Badge>
              </div>
              <div className="text-lg font-bold text-white flex items-center gap-2">
                <span>Recommended: {simResult.recommendation?.recommended_scenario}</span>
                {simResult.recommendation?.baseline_comparison?.improvement ? (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30">
                    +{simResult.recommendation.baseline_comparison.improvement.toFixed(1)} score
                    pts
                  </span>
                ) : null}
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSaveSimulation}
                disabled={savingSim}
                className="bg-white/10 hover:bg-white/20 text-white border-white/20 flex items-center gap-1.5"
              >
                <BookmarkPlus className="w-3.5 h-3.5 text-indigo-300" />
                <span>{savingSim ? 'Saving...' : 'Save Simulation'}</span>
              </Button>
            </div>
          </div>

          {saveSuccessMsg && (
            <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{saveSuccessMsg}</span>
            </div>
          )}

          {/* Projection Line Chart */}
          <Card className="p-6 border-slate-200/80 shadow-xs bg-white">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-900">
                  Scenario Trajectory Comparison Over Time
                </h3>
                <p className="text-xs text-slate-500">
                  {domain === 'finance'
                    ? `Projected Savings Balance (${currencySymbol}) progression`
                    : domain === 'study'
                    ? 'Projected Academic Performance Score (0-100)'
                    : 'Projected Health & Fitness Score (0-100)'}
                </p>
              </div>
              <Badge variant="default" size="sm">
                Deterministic Model
              </Badge>
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis
                    dataKey="month"
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: '#cbd5e1' }}
                    tickFormatter={(val) =>
                      domain === 'finance'
                        ? formatCompactCurrency(val)
                        : `${val}`
                    }
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      borderRadius: '8px',
                      color: '#f8fafc',
                      fontSize: '12px',
                      border: 'none',
                    }}
                    formatter={(val: any) =>
                      domain === 'finance'
                        ? [formatCurrency(Number(val)), 'Balance']
                        : [Number(val).toFixed(1), 'Score']
                    }
                  />
                  <Legend
                    wrapperStyle={{ paddingTop: '16px', fontSize: '12px' }}
                    iconType="circle"
                  />
                  {simResult.scenarios.map((s, idx) => (
                    <Line
                      key={s.name}
                      type="monotone"
                      dataKey={s.name}
                      stroke={SCENARIO_COLORS[idx % SCENARIO_COLORS.length]}
                      strokeWidth={s.is_baseline ? 3.5 : 2}
                      strokeDasharray={s.is_baseline ? undefined : '4 4'}
                      dot={{ r: s.is_baseline ? 3 : 2 }}
                      activeDot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </Card>

          {/* Scenario Comparison Cards Grid */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                Scenario Breakdown &amp; Decision Scores
              </span>
              <span className="text-xs text-slate-500">Ranked by Digital Twin Score</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {simResult.scenarios.map((s) => (
                <Card
                  key={s.name}
                  className={`p-5 flex flex-col justify-between transition-all ${
                    s.is_baseline
                      ? 'border-teal-400/80 bg-teal-50/20'
                      : s.name === simResult.recommendation?.recommended_scenario
                      ? 'border-indigo-400/80 bg-indigo-50/20'
                      : 'border-slate-200/80 bg-white'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-sm font-bold text-slate-900 line-clamp-1">{s.name}</span>
                      {s.is_baseline ? (
                        <Badge variant="success" size="sm">
                          Baseline
                        </Badge>
                      ) : s.name === simResult.recommendation?.recommended_scenario ? (
                        <Badge variant="indigo" size="sm">
                          Recommended
                        </Badge>
                      ) : null}
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-2 mb-4">{s.description}</p>

                    <div className="space-y-2 pt-2 border-t border-slate-100">
                      {domain === 'finance' && (
                        <>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Final Balance:</span>
                            <span className="font-semibold text-slate-800">
                              {formatCurrency(s.output_metrics.final_balance)}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Net Growth:</span>
                            <span className="font-semibold text-emerald-600">
                              +{formatCurrency(s.output_metrics.net_worth_change)}
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Monthly Surplus:</span>
                            <span
                              className={`font-semibold ${
                                s.output_metrics.monthly_surplus >= 0
                                  ? 'text-slate-800'
                                  : 'text-rose-600'
                              }`}
                            >
                              {formatCurrency(s.output_metrics.monthly_surplus)}
                            </span>
                          </div>
                        </>
                      )}

                      {domain === 'study' && (
                        <>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Projected Score:</span>
                            <span className="font-semibold text-indigo-700">
                              {s.output_metrics.final_score?.toFixed(1)}/100
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Improvement:</span>
                            <span className="font-semibold text-emerald-600">
                              +{s.output_metrics.score_improvement?.toFixed(1)} pts
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Total Hours:</span>
                            <span className="font-semibold text-slate-800">
                              {s.output_metrics.total_study_hours?.toFixed(0)} hrs
                            </span>
                          </div>
                        </>
                      )}

                      {domain === 'habits' && (
                        <>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Fitness Score:</span>
                            <span className="font-semibold text-rose-700">
                              {s.output_metrics.projected_fitness_score?.toFixed(1)}/100
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Score Change:</span>
                            <span className="font-semibold text-emerald-600">
                              +{s.output_metrics.fitness_score_change?.toFixed(1)} pts
                            </span>
                          </div>
                          <div className="flex justify-between text-xs">
                            <span className="text-slate-500">Consistency:</span>
                            <span className="font-semibold text-slate-800">
                              {s.output_metrics.habit_consistency?.toFixed(0)}%
                            </span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs text-slate-500">Score</span>
                    <span className="text-sm font-bold text-slate-900">{s.score.toFixed(1)}/100</span>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Digital Twin AI Recommendation Card */}
          {simResult.recommendation && (
            <Card className="p-6 border-indigo-200/80 bg-gradient-to-br from-indigo-50/40 via-white to-slate-50 shadow-xs">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Digital Twin Recommendation Engine
                </h3>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 space-y-4">
                  <div>
                    <h4 className="text-base font-bold text-slate-900 mb-1">
                      {simResult.recommendation.recommended_scenario}
                    </h4>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      {simResult.recommendation.reason}
                    </p>
                  </div>

                  {simResult.recommendation.benefits?.length > 0 && (
                    <div>
                      <span className="text-xs font-semibold text-emerald-700 block mb-1">
                        Key Benefits:
                      </span>
                      <ul className="space-y-1">
                        {simResult.recommendation.benefits.map((b, i) => (
                          <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0 mt-0.5" />
                            <span>{b}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {simResult.recommendation.risks?.length > 0 && (
                    <div>
                      <span className="text-xs font-semibold text-amber-700 block mb-1">
                        Trade-offs &amp; Risks to Monitor:
                      </span>
                      <ul className="space-y-1">
                        {simResult.recommendation.risks.map((r, i) => (
                          <li key={i} className="text-xs text-slate-600 flex items-start gap-1.5">
                            <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="p-4 rounded-xl bg-white border border-indigo-100 shadow-xs flex flex-col justify-between">
                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2 block">
                      Actionable Next Steps
                    </span>
                    {simResult.recommendation.next_actions?.length > 0 ? (
                      <ul className="space-y-2">
                        {simResult.recommendation.next_actions.map((na, i) => (
                          <li key={i} className="text-xs text-slate-700 flex items-start gap-1.5">
                            <ArrowRight className="w-3.5 h-3.5 text-indigo-600 shrink-0 mt-0.5" />
                            <span>{na}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-500">
                        Continue monitoring this trajectory against your monthly targets.
                      </p>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs text-slate-500">Overall Score</span>
                    <Badge variant="indigo" size="md">
                      {simResult.recommendation.score.toFixed(1)} / 100
                    </Badge>
                  </div>
                </div>
              </div>
            </Card>
          )}

          {/* Expandable Comparison Table */}
          <div className="border border-slate-200/80 rounded-xl overflow-hidden bg-white shadow-xs">
            <button
              type="button"
              onClick={() => setShowTable(!showTable)}
              className="w-full px-5 py-3 bg-slate-50 border-b border-slate-200/80 flex items-center justify-between text-left hover:bg-slate-100/60 transition-all"
            >
              <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                Detailed Comparison Table ({simResult.comparison_table.length} Scenarios)
              </span>
              {showTable ? (
                <ChevronUp className="w-4 h-4 text-slate-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-slate-500" />
              )}
            </button>

            {showTable && (
              <div className="overflow-x-auto p-2">
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-500 font-semibold uppercase tracking-wider">
                      {Object.keys(simResult.comparison_table[0] || {}).map((col) => (
                        <th key={col} className="px-4 py-2.5">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {simResult.comparison_table.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/60">
                        {Object.entries(row).map(([k, v], cellIdx) => (
                          <td key={cellIdx} className="px-4 py-2.5 text-slate-800">
                            {typeof v === 'number'
                              ? domain === 'finance' && (k.includes('Balance') || k.includes('Net') || k.includes('Surplus'))
                                ? formatCurrency(v)
                                : v.toFixed(1)
                              : String(v)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Explicit Assumptions & Disclaimer */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="p-4 border-slate-200/80 bg-white">
              <div className="flex items-center gap-2 mb-2">
                <Info className="w-4 h-4 text-indigo-600" />
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Simulation Assumptions
                </h4>
              </div>
              <ul className="space-y-1.5 text-xs text-slate-600">
                {simResult.assumptions.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-1.5">
                    <span className="text-slate-400">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </Card>

            <Card className="p-4 border-amber-200 bg-amber-50/50">
              <div className="flex items-center gap-2 mb-2">
                <ShieldAlert className="w-4 h-4 text-amber-700" />
                <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                  Important Disclaimer
                </h4>
              </div>
              <p className="text-xs text-amber-900 leading-relaxed">
                {simResult.disclaimer}
              </p>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};
