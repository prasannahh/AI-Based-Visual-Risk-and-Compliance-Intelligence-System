import React, { useEffect, useState } from "react";
import {
  Activity,
  TrendingUp,
  TrendingDown,
  BookOpen,
  Wallet,
  CheckCircle2,
  Clock,
  Target,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  Moon,
  PieChart as PieIcon,
  Layers,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { api } from "../services/api";
import type {
  AnalyticsResponse,
  AnalyticsTimeRange,
} from "../types/api";
import { Card } from "../components/ui/Card";
import { MetricCard } from "../components/ui/MetricCard";
import { Button } from "../components/ui/Button";
import { LoadingSkeleton } from "../components/ui/LoadingSkeleton";
import { ErrorState } from "../components/ui/ErrorState";
import { usePreferences } from "../context/PreferencesContext";

const CATEGORY_COLORS: Record<string, string> = {
  Food: "#10b981",
  "Dining Out": "#059669",
  Housing: "#6366f1",
  Bills: "#8b5cf6",
  Transport: "#f59e0b",
  Salary: "#3b82f6",
  Investment: "#84cc16",
  Entertainment: "#ec4899",
  Healthcare: "#ef4444",
  Education: "#06b6d4",
  Other: "#64748b",
};

const CHART_PALETTE = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#06b6d4",
  "#ec4899",
  "#8b5cf6",
  "#ef4444",
  "#84cc16",
  "#3b82f6",
  "#64748b",
];

const TIME_RANGES: Array<{ label: string; value: AnalyticsTimeRange }> = [
  { label: "7 Days", value: "7D" },
  { label: "30 Days", value: "30D" },
  { label: "90 Days", value: "90D" },
  { label: "1 Year", value: "1Y" },
];

export const AnalyticsPage: React.FC = () => {
  const { formatCurrency, formatCompactCurrency, formatDate } = usePreferences();
  const [selectedRange, setSelectedRange] = useState<AnalyticsTimeRange>("30D");
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active sub-domain tab
  const [activeTab, setActiveTab] = useState<
    "all" | "productivity" | "study" | "finance" | "habits" | "goals"
  >("all");

  const fetchAnalytics = async (range: AnalyticsTimeRange, isManual = false) => {
    if (isManual) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const resp = await api.getAnalytics(range);
      setData(resp);
    } catch (err: any) {
      setError(err?.message || "Failed to load analytics from server.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics(selectedRange);
  }, [selectedRange]);

  const handleRangeChange = (range: AnalyticsTimeRange) => {
    setSelectedRange(range);
  };

  const formatINR = (val: number | null | undefined): string => {
    return formatCurrency(val);
  };

  if (isLoading) {
    return <LoadingSkeleton rows={4} />;
  }

  if (error && !data) {
    return (
      <ErrorState
        title="Failed to load Analytics"
        message={error}
        onRetry={() => fetchAnalytics(selectedRange)}
      />
    );
  }

  const overview = data?.overview_metrics;
  const hasData = Boolean(data?.has_data);

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Analytics</h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5" />
              Grounded Intelligence
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Understand your patterns, progress, and performance over time across all domains.
          </p>
        </div>

        {/* Time Range Selector & Actions */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="inline-flex items-center p-1 bg-slate-100 rounded-xl border border-slate-200">
            {TIME_RANGES.map((r) => (
              <button
                key={r.value}
                onClick={() => handleRangeChange(r.value)}
                className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
                  selectedRange === r.value
                    ? "bg-white text-indigo-600 shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchAnalytics(selectedRange, true)}
            disabled={isRefreshing}
            leftIcon={<RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />}
          >
            {isRefreshing ? "Syncing..." : "Refresh"}
          </Button>
        </div>
      </div>

      {/* Date Window Indicator */}
      {data && (
        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <span>
            Window: <strong className="text-slate-700">{data.start_date}</strong> to{" "}
            <strong className="text-slate-700">{data.end_date}</strong> ({data.range})
          </span>
          <span>{hasData ? "Real user data synchronized" : "Awaiting activity records"}</span>
        </div>
      )}

      {/* Uncalibrated / No Activity State Banner */}
      {!hasData && (
        <Card className="border-amber-200 bg-amber-50/50 p-6">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-100 rounded-xl text-amber-700 shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-900">No Activity in this Window</h3>
              <p className="text-sm text-slate-600 mt-1 max-w-2xl">
                No records were found for the selected {selectedRange} window. As you log tasks in
                Planner, record study sessions, or track transactions in Wealth Planner, your Digital
                Twin will surface detailed historical analytics and patterns here.
              </p>
            </div>
          </div>
        </Card>
      )}

      {/* Overview Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Productivity"
          value={
            overview?.productivity_score != null
              ? `${overview.productivity_score}%`
              : "Not Enough Data"
          }
          subtitle={
            overview?.tasks_total
              ? `${overview.tasks_completed} of ${overview.tasks_total} completed`
              : "Task completion rate"
          }
          icon={<CheckCircle2 className="w-5 h-5 text-indigo-600" />}
        />

        <MetricCard
          title="Study Time"
          value={overview?.study_hours != null ? `${overview.study_hours} hrs` : "Not Enough Data"}
          subtitle={
            overview?.avg_study_score != null
              ? `Avg score: ${overview.avg_study_score}/100`
              : "Logged academic hours"
          }
          icon={<BookOpen className="w-5 h-5 text-cyan-600" />}
        />

        <MetricCard
          title="Net Cash Flow"
          value={overview?.net_cash_flow != null ? formatINR(overview.net_cash_flow) : "Not Enough Data"}
          subtitle={
            overview?.net_cash_flow != null
              ? overview.net_cash_flow >= 0
                ? "Surplus inflow"
                : "Net deficit"
              : "Income minus expenses"
          }
          icon={
            (overview?.net_cash_flow ?? 0) >= 0 ? (
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-rose-600" />
            )
          }
        />

        <MetricCard
          title="Habits & Sleep"
          value={
            overview?.habit_consistency != null
              ? `${overview.habit_consistency}%`
              : "Not Enough Data"
          }
          subtitle={
            overview?.avg_sleep_hours != null
              ? `Avg sleep: ${overview.avg_sleep_hours}h`
              : "Habit consistency"
          }
          icon={<Moon className="w-5 h-5 text-purple-600" />}
        />

        <MetricCard
          title="Goal Pacing"
          value={
            overview?.avg_goal_progress != null
              ? `${overview.avg_goal_progress}%`
              : "Not Enough Data"
          }
          subtitle={
            overview?.active_goals_count
              ? `${overview.active_goals_count} active target(s)`
              : "Average progress"
          }
          icon={<Target className="w-5 h-5 text-amber-600" />}
        />
      </div>

      {/* Grounded Twin Insights Section */}
      {data?.twin_insights && data.twin_insights.length > 0 && (
        <Card className="p-5 border-slate-200 bg-linear-to-r from-slate-50 to-white">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-bold text-slate-900">Digital Twin Analytical Insights</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.twin_insights.map((ins, i) => {
              const isPositive = ins.type === "positive";
              const isAttention = ins.type === "attention";
              return (
                <div
                  key={i}
                  className={`p-3 rounded-xl border text-xs flex flex-col justify-between ${
                    isPositive
                      ? "bg-emerald-50/50 border-emerald-100 text-emerald-950"
                      : isAttention
                      ? "bg-rose-50/50 border-rose-100 text-rose-950"
                      : "bg-slate-50 border-slate-200 text-slate-800"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="font-bold uppercase tracking-wider text-[10px] text-slate-500">
                      {ins.domain}
                    </span>
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                        isPositive
                          ? "bg-emerald-100 text-emerald-800"
                          : isAttention
                          ? "bg-rose-100 text-rose-800"
                          : "bg-slate-200 text-slate-700"
                      }`}
                    >
                      {ins.title}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed text-slate-700 mt-1">{ins.message}</p>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Domain Navigation Tabs */}
      <div className="flex border-b border-slate-200 overflow-x-auto gap-2 text-sm font-medium">
        <button
          onClick={() => setActiveTab("all")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "all"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Layers className="w-4 h-4" />
          All Domains
        </button>

        <button
          onClick={() => setActiveTab("productivity")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "productivity"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          Productivity & Tasks
        </button>

        <button
          onClick={() => setActiveTab("study")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "study"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <BookOpen className="w-4 h-4" />
          Study & Academics
        </button>

        <button
          onClick={() => setActiveTab("finance")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "finance"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Wallet className="w-4 h-4" />
          Financial Trends
        </button>

        <button
          onClick={() => setActiveTab("habits")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "habits"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Activity className="w-4 h-4" />
          Habits & Lifestyle
        </button>

        <button
          onClick={() => setActiveTab("goals")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "goals"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Target className="w-4 h-4" />
          Goals ({data?.goals_progress?.goals?.length ?? 0})
        </button>
      </div>

      {/* SECTION 1: PRODUCTIVITY & TASKS */}
      {(activeTab === "all" || activeTab === "productivity") && (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-indigo-600" />
                Task Completion & Productivity Trend
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Scheduled task execution and completion rates over the {selectedRange} window.
              </p>
            </div>
            {data?.productivity_trend?.has_data && overview?.productivity_score != null && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                {overview.productivity_score}% Completion Rate
              </span>
            )}
          </div>

          {!data?.productivity_trend?.has_data ||
          data.productivity_trend.series.length === 0 ? (
            <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mb-2" />
              <p className="font-medium text-slate-600">No Task Records in this Range</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Schedule and complete items in Tasks & Planner to populate productivity time-series
                analytics.
              </p>
            </div>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.productivity_trend.series} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#0f172a",
                      borderColor: "#334155",
                      borderRadius: "0.5rem",
                      color: "#f8fafc",
                      fontSize: "0.75rem",
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                  <Bar dataKey="completed" name="Completed Tasks" fill="#10b981" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="total" name="Total Scheduled" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>
      )}

      {/* SECTION 2: STUDY & ACADEMICS */}
      {(activeTab === "all" || activeTab === "study") && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Study Hours Over Time */}
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-cyan-600" />
                  Daily Study Hours & Scores
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Total: {data?.study_analytics?.total_hours ?? 0} hrs logged ({data?.study_analytics?.sessions_count ?? 0} sessions)
                </p>
              </div>
              {data?.study_analytics?.peak_focus_time && (
                <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-cyan-50 text-cyan-700 border border-cyan-200 flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Peak: {data.study_analytics.peak_focus_time}
                </span>
              )}
            </div>

            {!data?.study_analytics?.has_data ||
            data.study_analytics.daily_trend.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
                <BookOpen className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No Study Activity in this Window</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Log study hours in Study & Academic to analyze consistency and test performance trends.
                </p>
              </div>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.study_analytics.daily_trend} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} unit="h" />
                    <Tooltip
                      formatter={(val: any, name: any) => [
                        name === "Hours" ? `${val} hrs` : `${val}/100`,
                        name,
                      ]}
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.5rem",
                        color: "#f8fafc",
                        fontSize: "0.75rem",
                      }}
                    />
                    <Bar dataKey="hours" name="Hours" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Subject Breakdown */}
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-indigo-600" />
                Subject Distribution
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Time investment across academic subjects.
              </p>
            </div>

            {!data?.study_analytics?.has_data ||
            data.study_analytics.subject_breakdown.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
                <PieIcon className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No Subject Breakdown Available</p>
              </div>
            ) : (
              <div className="space-y-3">
                {data.study_analytics.subject_breakdown.map((subj, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex justify-between text-xs font-semibold text-slate-700">
                      <span>{subj.subject}</span>
                      <span>
                        {subj.hours} hrs ({subj.percentage}%)
                        {subj.avg_score != null ? ` · ${subj.avg_score}/100` : ""}
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(subj.percentage, 100)}%`,
                          backgroundColor: CHART_PALETTE[idx % CHART_PALETTE.length],
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      )}

      {/* SECTION 3: FINANCIAL TRENDS */}
      {(activeTab === "all" || activeTab === "finance") && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Income vs Expenses Cashflow */}
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Wallet className="w-4 h-4 text-emerald-600" />
                  Income vs Expenses Cashflow
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Net cashflow: {formatINR(data?.financial_analytics?.net_savings ?? 0)}
                </p>
              </div>
            </div>

            {!data?.financial_analytics?.has_data ||
            data.financial_analytics.cashflow_trend.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
                <Wallet className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No Financial Records in this Window</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Log income and expenses in Wealth Planner to see periodic cash flow comparisons.
                </p>
              </div>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.financial_analytics.cashflow_trend} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="period" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickLine={false}
                      tickFormatter={(val) => formatCompactCurrency(val)}
                    />
                    <Tooltip
                      formatter={(val: any) => [formatINR(Number(val)), ""]}
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.5rem",
                        color: "#f8fafc",
                        fontSize: "0.75rem",
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                    <Bar dataKey="income" name="Income" fill="#10b981" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="expenses" name="Expenses" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>

          {/* Spending by Category Donut */}
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <PieIcon className="w-4 h-4 text-purple-600" />
                Spending by Category
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Total spent: {formatINR(data?.financial_analytics?.total_expenses ?? 0)}
              </p>
            </div>

            {!data?.financial_analytics?.has_data ||
            data.financial_analytics.spending_by_category.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
                <PieIcon className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No Expense Categories Logged</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="h-52 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={data.financial_analytics.spending_by_category}
                        dataKey="spent"
                        nameKey="category"
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={3}
                      >
                        {data.financial_analytics.spending_by_category.map((entry, idx) => (
                          <Cell
                            key={`cell-${idx}`}
                            fill={CATEGORY_COLORS[entry.category] || CHART_PALETTE[idx % CHART_PALETTE.length]}
                          />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(val: any) => [formatINR(Number(val)), "Spent"]}
                        contentStyle={{
                          backgroundColor: "#0f172a",
                          borderColor: "#334155",
                          borderRadius: "0.5rem",
                          color: "#f8fafc",
                          fontSize: "0.75rem",
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs">
                  {data.financial_analytics.spending_by_category.slice(0, 6).map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-1.5 rounded-lg bg-slate-50 border border-slate-100"
                    >
                      <div className="flex items-center gap-1.5 truncate">
                        <span
                          className="w-2 h-2 rounded-full shrink-0"
                          style={{
                            backgroundColor:
                              CATEGORY_COLORS[c.category] || CHART_PALETTE[i % CHART_PALETTE.length],
                          }}
                        />
                        <span className="font-medium text-slate-700 truncate">{c.category}</span>
                      </div>
                      <span className="font-bold text-slate-900 shrink-0">
                        {formatINR(c.spent)} ({c.percentage}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* SECTION 4: HABITS & LIFESTYLE */}
      {(activeTab === "all" || activeTab === "habits") && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Habit Consistency */}
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Activity className="w-4 h-4 text-purple-600" />
                Habit Consistency & Predictions
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Calculated completion rates and ML trend trajectories.
              </p>
            </div>

            {!data?.habit_lifestyle_analytics?.has_data ||
            data.habit_lifestyle_analytics.habits.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
                <Activity className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No Habit Predictions Available</p>
                <p className="text-xs text-slate-400 mt-1 max-w-sm">
                  Log habit entries in the Habit Tracker to analyze consistency and directional trends.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {data.habit_lifestyle_analytics.habits.map((h, i) => (
                  <div key={i} className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-800">{h.habit_name}</span>
                      <span className="font-semibold text-slate-600">
                        {h.rate}% consistency ({h.trend_pct > 0 ? `+${h.trend_pct}%` : `${h.trend_pct}%`})
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${Math.min(h.rate, 100)}%`,
                          backgroundColor: h.rate >= 70 ? "#10b981" : h.rate >= 40 ? "#f59e0b" : "#ef4444",
                        }}
                      />
                    </div>
                    <p className="text-[11px] text-slate-500 italic">{h.insight}</p>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Sleep & Duration Trend */}
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Moon className="w-4 h-4 text-indigo-600" />
                Sleep & Physical Activity
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Sleep duration and exercise minutes over the active window.
              </p>
            </div>

            {!data?.habit_lifestyle_analytics?.has_data ||
            data.habit_lifestyle_analytics.sleep_activity_trend.length === 0 ? (
              <div className="h-64 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
                <Moon className="w-8 h-8 text-slate-300 mb-2" />
                <p className="font-medium text-slate-600">No Sleep or Fitness Data Logged</p>
              </div>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data.habit_lifestyle_analytics.sleep_activity_trend} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#0f172a",
                        borderColor: "#334155",
                        borderRadius: "0.5rem",
                        color: "#f8fafc",
                        fontSize: "0.75rem",
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: "12px", paddingTop: "10px" }} />
                    <Line type="monotone" dataKey="sleep_hours" name="Sleep (hrs)" stroke="#8b5cf6" strokeWidth={2} />
                    <Line type="monotone" dataKey="exercise_minutes" name="Exercise (min)" stroke="#f59e0b" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* SECTION 5: GOALS PROGRESS */}
      {(activeTab === "all" || activeTab === "goals") && (
        <Card className="p-6">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Target className="w-4 h-4 text-amber-600" />
                Goals Pacing & Execution
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Progress tracking towards designated target amounts.
              </p>
            </div>
            {data?.goals_progress?.has_data && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                {data.goals_progress.goals.length} Active Targets
              </span>
            )}
          </div>

          {!data?.goals_progress?.has_data ||
          data.goals_progress.goals.length === 0 ? (
            <div className="h-48 flex flex-col items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm p-4 text-center">
              <Target className="w-8 h-8 text-slate-300 mb-2" />
              <p className="font-medium text-slate-600">No Goals Configured</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm">
                Add goal milestones in Profile & Goals to track pacing analytics.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.goals_progress.goals.map((g) => (
                <div key={g.goal_id} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <div className="flex justify-between items-start">
                    <h4 className="font-bold text-sm text-slate-900 truncate">{g.goal_name}</h4>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 shrink-0">
                      {g.progress_pct}%
                    </span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="h-full bg-amber-500 rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(g.progress_pct, 100)}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-500 pt-1">
                    <span>
                      {formatCurrency(g.current_progress)} / {formatCurrency(g.target_amount)}
                    </span>
                    <span>{g.target_date ? `Due ${formatDate(g.target_date)}` : "No deadline"}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
