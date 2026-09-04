import React, { useEffect, useMemo, useState } from "react";
import {
  TrendingUp,
  TrendingDown,
  Wallet,
  CreditCard,
  PiggyBank,
  RefreshCw,
  Plus,
  Trash2,
  Edit3,
  Sparkles,
  Search,
  PieChart as PieIcon,
  BarChart3,
  Target,
  AlertCircle,
  CheckCircle2,
  X,
  ShieldCheck,
} from "lucide-react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
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
  TransactionItem,
  TransactionType,
  WealthOverviewResponse,
  ExpenseClassifyResponse,
  ForecastSimulateResponse,
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
  "#ec4899",
  "#06b6d4",
  "#8b5cf6",
  "#ef4444",
  "#84cc16",
  "#3b82f6",
  "#64748b",
];

export const WealthPlannerPage: React.FC = () => {
  const { formatCurrency, formatCompactCurrency, formatDate, currencySymbol } = usePreferences();
  const [data, setData] = useState<WealthOverviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active View Tab
  const [activeTab, setActiveTab] = useState<
    "overview" | "analytics" | "budget" | "classifier" | "transactions"
  >("overview");

  // Transactions Filter & Search State
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("All");
  const [filterCategory, setFilterCategory] = useState<string>("All");

  // Interactive Forecast Simulation State
  const [forecastMonths, setForecastMonths] = useState<number>(12);
  const [extraSavings, setExtraSavings] = useState<number>(0);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simResponse, setSimResponse] = useState<ForecastSimulateResponse | null>(null);

  // AI Expense Classifier State
  const [classifierInput, setClassifierInput] = useState<string>("");
  const [isClassifying, setIsClassifying] = useState<boolean>(false);
  const [classifierResult, setClassifierResult] = useState<ExpenseClassifyResponse | null>(null);
  const [classifierError, setClassifierError] = useState<string | null>(null);

  // Add / Edit Transaction Modal State
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingTx, setEditingTx] = useState<TransactionItem | null>(null);
  const [formCategory, setFormCategory] = useState<string>("Food");
  const [formAmount, setFormAmount] = useState<string>("");
  const [formType, setFormType] = useState<TransactionType>("Expense");
  const [formDate, setFormDate] = useState<string>(() => new Date().toISOString().split("T")[0]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // In-modal AI Assistant detector
  const [modalAiPrompt, setModalAiPrompt] = useState<string>("");
  const [isModalDetecting, setIsModalDetecting] = useState<boolean>(false);

  // Delete Modal State
  const [deleteConfirmTx, setDeleteConfirmTx] = useState<TransactionItem | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Fetch Wealth Overview
  const fetchWealthData = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const resp = await api.getWealthOverview();
      setData(resp);

      // Run initial simulation if baseline exists
      if (resp.has_data) {
        runSimulation(12, 0);
      }
    } catch (err: any) {
      setError(err?.message || "Failed to load financial intelligence from server.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchWealthData();
  }, []);

  // Run Savings Forecast Simulation
  const runSimulation = async (months: number, extra: number) => {
    setIsSimulating(true);
    try {
      const sim = await api.simulateSavingsForecast({
        horizon_months: months,
        extra_monthly_savings: extra,
      });
      setSimResponse(sim);
    } catch (err: any) {
      console.error("Failed to simulate savings forecast:", err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    setForecastMonths(val);
    runSimulation(val, extraSavings);
  };

  const handleExtraSavingsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = Math.max(0, parseFloat(e.target.value) || 0);
    setExtraSavings(val);
    runSimulation(forecastMonths, val);
  };

  // Run AI Expense Classifier
  const handleClassify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!classifierInput.trim()) {
      setClassifierError("Please enter an expense description to classify.");
      return;
    }
    setIsClassifying(true);
    setClassifierError(null);
    try {
      const res = await api.classifyExpense({ description: classifierInput.trim() });
      setClassifierResult(res);
    } catch (err: any) {
      setClassifierError(err?.message || "AI Classification request failed.");
    } finally {
      setIsClassifying(false);
    }
  };

  // In-modal AI Category Auto-Detect
  const handleModalAutoDetect = async () => {
    if (!modalAiPrompt.trim()) return;
    setIsModalDetecting(true);
    try {
      const res = await api.classifyExpense({ description: modalAiPrompt.trim() });
      if (res.category && data?.supported_categories?.includes(res.category)) {
        setFormCategory(res.category);
      } else if (res.category) {
        setFormCategory("Other");
      }
      setFormType("Expense");
    } catch (e) {
      console.error("Auto detect failed", e);
    } finally {
      setIsModalDetecting(false);
    }
  };

  // Format currency with user preference
  const formatINR = (val: number | null | undefined): string => {
    return formatCurrency(val);
  };

  // Open Add Modal
  const handleOpenAddModal = (initialCategory?: string) => {
    setEditingTx(null);
    setFormCategory(initialCategory || "Food");
    setFormAmount("");
    setFormType("Expense");
    setFormDate(new Date().toISOString().split("T")[0]);
    setModalAiPrompt("");
    setFormError(null);
    setIsModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (tx: TransactionItem) => {
    setEditingTx(tx);
    setFormCategory(tx.category);
    setFormAmount(String(tx.amount));
    setFormType(tx.transaction_type);
    setFormDate(tx.date);
    setModalAiPrompt("");
    setFormError(null);
    setIsModalOpen(true);
  };

  // Submit Add / Edit
  const handleSubmitTx = async (e: React.FormEvent) => {
    e.preventDefault();
    const amt = parseFloat(formAmount);
    if (isNaN(amt) || amt <= 0) {
      setFormError("Please enter a valid amount greater than zero.");
      return;
    }
    if (!formCategory.trim()) {
      setFormError("Please select a transaction category.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      if (editingTx) {
        await api.updateTransaction(editingTx.record_id, {
          category: formCategory.trim(),
          amount: amt,
          transaction_type: formType,
          date: formDate,
        });
      } else {
        await api.createTransaction({
          category: formCategory.trim(),
          amount: amt,
          transaction_type: formType,
          date: formDate,
        });
      }
      setIsModalOpen(false);
      await fetchWealthData(true);
    } catch (err: any) {
      setFormError(err?.message || "Failed to save transaction.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Confirm Delete
  const handleConfirmDelete = async () => {
    if (!deleteConfirmTx) return;
    setIsDeleting(true);
    try {
      await api.deleteTransaction(deleteConfirmTx.record_id);
      setDeleteConfirmTx(null);
      await fetchWealthData(true);
    } catch (err: any) {
      alert(err?.message || "Failed to delete transaction.");
    } finally {
      setIsDeleting(false);
    }
  };

  // Filtered transactions
  const filteredTransactions = useMemo(() => {
    if (!data?.transactions) return [];
    return data.transactions.filter((t) => {
      const matchesSearch =
        searchQuery === "" ||
        t.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.date.includes(searchQuery) ||
        String(t.amount).includes(searchQuery);

      const matchesType = filterType === "All" || t.transaction_type === filterType;
      const matchesCategory = filterCategory === "All" || t.category === filterCategory;

      return matchesSearch && matchesType && matchesCategory;
    });
  }, [data?.transactions, searchQuery, filterType, filterCategory]);

  // Merge history and simulation timeline for projection chart
  const combinedForecastChartData = useMemo(() => {
    const points: Array<{
      label: string;
      actual?: number;
      projected?: number;
    }> = [];

    // Actual history
    if (data?.savings_trend?.history && data.savings_trend.history.length > 0) {
      data.savings_trend.history.forEach((h) => {
        points.push({
          label: h.date,
          actual: h.cumulative_savings,
        });
      });
    }

    // Connect last actual to projected timeline
    if (simResponse?.projected_timeline && simResponse.projected_timeline.length > 0) {
      if (points.length > 0) {
        const lastActual = points[points.length - 1];
        lastActual.projected = lastActual.actual;
      }
      simResponse.projected_timeline.forEach((pt) => {
        points.push({
          label: pt.date,
          projected: pt.projected_savings,
        });
      });
    }

    return points;
  }, [data?.savings_trend?.history, simResponse]);

  if (isLoading) {
    return <LoadingSkeleton rows={4} />;
  }

  if (error && !data) {
    return (
      <ErrorState
        title="Failed to load Wealth Intelligence"
        message={error}
        onRetry={() => fetchWealthData()}
      />
    );
  }

  const hasData = Boolean(data?.has_data && data.transactions.length > 0);
  const summary = data?.summary;
  const categoriesList = data?.supported_categories || [
    "Housing",
    "Food",
    "Dining Out",
    "Transport",
    "Salary",
    "Investment",
    "Entertainment",
    "Healthcare",
    "Education",
    "Bills",
    "Other",
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Wealth Planner & Finance
            </h1>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5" />
              PostgreSQL Ground Truth
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Cash flows, ML spending analysis, 50/30/20 budget guidelines, and interactive savings
            projections.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchWealthData(true)}
            disabled={isRefreshing}
            leftIcon={<RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />}
          >
            {isRefreshing ? "Syncing..." : "Refresh"}
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => handleOpenAddModal()}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            Add Transaction
          </Button>
        </div>
      </div>

      {/* Honest Uncalibrated State Banner if no records exist */}
      {!hasData && (
        <Card className="border-amber-200 bg-amber-50/50 p-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2.5 bg-amber-100 rounded-xl text-amber-700 shrink-0 mt-0.5">
                <PiggyBank className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-semibold text-slate-900">
                  Financial Model Uncalibrated
                </h3>
                <p className="text-sm text-slate-600 mt-1 max-w-2xl">
                  No financial records are logged in your account yet. Log your income, expenses, or
                  savings to unlock AI spending distributions, 50/30/20 category recommendations, and
                  predictive savings growth curves.
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => handleOpenAddModal("Salary")}
              leftIcon={<Plus className="w-4 h-4" />}
              className="shrink-0"
            >
              Record First Transaction
            </Button>
          </div>
        </Card>
      )}

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Income"
          value={hasData && summary?.total_income != null ? formatINR(summary.total_income) : "--"}
          subtitle={hasData ? "All logged earnings" : "Awaiting records"}
          icon={<Wallet className="w-5 h-5 text-emerald-600" />}
        />

        <MetricCard
          title="Total Expenses"
          value={hasData && summary?.total_expenses != null ? formatINR(summary.total_expenses) : "--"}
          subtitle={hasData ? "All logged expenditures" : "Awaiting records"}
          icon={<CreditCard className="w-5 h-5 text-rose-600" />}
        />

        <MetricCard
          title="Net Cash Flow"
          value={hasData && summary?.net_cash_flow != null ? formatINR(summary.net_cash_flow) : "--"}
          subtitle={
            hasData && summary?.net_cash_flow != null
              ? summary.net_cash_flow >= 0
                ? "Surplus balance"
                : "Net deficit"
              : "Income minus expenses"
          }
          icon={
            hasData && (summary?.net_cash_flow ?? 0) >= 0 ? (
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-rose-600" />
            )
          }
        />

        <MetricCard
          title="Total Savings"
          value={hasData && summary?.total_savings != null ? formatINR(summary.total_savings) : "--"}
          subtitle={
            hasData && summary?.savings_rate_pct != null
              ? `${summary.savings_rate_pct}% of income`
              : "Awaiting records"
          }
          icon={<PiggyBank className="w-5 h-5 text-indigo-600" />}
        />

        <MetricCard
          title="Monthly Savings Rate"
          value={
            hasData && summary?.monthly_rate != null
              ? `${formatINR(summary.monthly_rate)} / mo`
              : "--"
          }
          subtitle={
            hasData && summary?.months_active
              ? `Across ${summary.months_active} active month(s)`
              : "Baseline growth rate"
          }
          icon={<Target className="w-5 h-5 text-cyan-600" />}
        />
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 overflow-x-auto gap-2 text-sm font-medium">
        <button
          onClick={() => setActiveTab("overview")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "overview"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          Savings Projection Simulator
        </button>

        <button
          onClick={() => setActiveTab("analytics")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "analytics"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <PieIcon className="w-4 h-4" />
          Spending Analytics
        </button>

        <button
          onClick={() => setActiveTab("budget")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "budget"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Target className="w-4 h-4" />
          50/30/20 Budget Guidelines
        </button>

        <button
          onClick={() => setActiveTab("classifier")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "classifier"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <Sparkles className="w-4 h-4 text-purple-600" />
          AI Expense Classifier
        </button>

        <button
          onClick={() => setActiveTab("transactions")}
          className={`pb-3 px-3 border-b-2 transition-colors whitespace-nowrap flex items-center gap-2 ${
            activeTab === "transactions"
              ? "border-indigo-600 text-indigo-600 font-semibold"
              : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
          }`}
        >
          <CreditCard className="w-4 h-4" />
          Transactions Ledger ({data?.transactions?.length ?? 0})
        </button>
      </div>

      {/* TAB 1: SAVINGS PROJECTION SIMULATOR */}
      {activeTab === "overview" && (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-6 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-indigo-600" />
                  Interactive Savings Growth Simulator
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Simulate your cumulative savings trajectory based on historical performance and
                  custom monthly contributions.
                </p>
              </div>

              {/* Simulation Controls */}
              <div className="flex flex-wrap items-center gap-4 bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div className="flex flex-col gap-1">
                  <div className="flex justify-between text-xs font-semibold text-slate-700">
                    <span>Horizon:</span>
                    <span className="text-indigo-600">{forecastMonths} Months</span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="36"
                    value={forecastMonths}
                    onChange={handleSliderChange}
                    className="w-36 accent-indigo-600 cursor-pointer h-1.5 bg-slate-200 rounded-lg"
                  />
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs font-semibold text-slate-700">
                    Extra Monthly Contribution:
                  </label>
                  <div className="relative">
                    <span className="absolute left-2.5 top-1.5 text-xs text-slate-400">{currencySymbol}</span>
                    <input
                      type="number"
                      min="0"
                      step="500"
                      value={extraSavings}
                      onChange={handleExtraSavingsChange}
                      placeholder="0"
                      className="w-32 pl-6 pr-2 py-1 text-xs font-medium bg-white border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {isSimulating && (
                  <span className="text-xs text-indigo-600 font-medium flex items-center gap-1 animate-pulse">
                    <RefreshCw className="w-3 h-3 animate-spin" /> Computing...
                  </span>
                )}
              </div>
            </div>

            {/* Projection Metric Highlights */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 my-6">
              <div className="bg-slate-50/70 border border-slate-200 p-4 rounded-xl">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Current Savings
                </span>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {formatINR(simResponse?.current_savings ?? summary?.total_savings ?? 0)}
                </p>
                <span className="text-xs text-slate-500">Historical base balance</span>
              </div>

              <div className="bg-indigo-50/50 border border-indigo-100 p-4 rounded-xl">
                <span className="text-xs font-semibold text-indigo-700 uppercase tracking-wider">
                  Effective Monthly Rate
                </span>
                <p className="text-xl font-bold text-indigo-900 mt-1">
                  {formatINR(simResponse?.effective_monthly_rate ?? summary?.monthly_rate ?? 0)} / mo
                </p>
                <span className="text-xs text-indigo-600">
                  Baseline {formatINR(simResponse?.baseline_monthly_rate ?? 0)} + Extra {formatINR(extraSavings)}
                </span>
              </div>

              <div className="bg-emerald-50/50 border border-emerald-100 p-4 rounded-xl">
                <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                  Projected in {forecastMonths} Months
                </span>
                <p className="text-xl font-bold text-emerald-900 mt-1">
                  {formatINR(simResponse?.projected_final_savings ?? 0)}
                </p>
                <span className="text-xs text-emerald-600">Estimated future balance</span>
              </div>
            </div>

            {/* Chart */}
            <div className="h-80 w-full mt-4">
              {combinedForecastChartData.length === 0 ? (
                <div className="h-full flex items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm">
                  Log income and expenses below to generate a real forecast projection.
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={combinedForecastChartData} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                    <defs>
                      <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                      </linearGradient>
                      <linearGradient id="projectedGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
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
                    <Area
                      type="monotone"
                      dataKey="actual"
                      name={`Actual Cumulative (${currencySymbol})`}
                      stroke="#06b6d4"
                      strokeWidth={2.5}
                      fillOpacity={1}
                      fill="url(#actualGrad)"
                      connectNulls
                    />
                    <Area
                      type="monotone"
                      dataKey="projected"
                      name={`Projected Forecast (${currencySymbol})`}
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      strokeDasharray="4 4"
                      fillOpacity={1}
                      fill="url(#projectedGrad)"
                      connectNulls
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 2: SPENDING ANALYTICS */}
      {activeTab === "analytics" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Category Distribution */}
          <Card className="p-6">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <PieIcon className="w-4 h-4 text-emerald-600" />
                  Category Spending Breakdown
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Total logged expenses: {formatINR(data?.spending_analysis?.total_spent ?? 0)}
                </p>
              </div>

              {data?.spending_analysis?.top_category && (
                <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
                  Top: {data.spending_analysis.top_category} (
                  {formatINR(data.spending_analysis.top_category_amount ?? 0)})
                </span>
              )}
            </div>

            {(!data?.spending_analysis?.category_wise ||
              data.spending_analysis.category_wise.length === 0) ? (
              <div className="h-64 flex items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm">
                Log expense transactions to view category distribution.
              </div>
            ) : (
              <div className="space-y-4">
                <div className="h-60 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={data.spending_analysis.category_wise}
                        dataKey="spent"
                        nameKey="category"
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={3}
                      >
                        {data.spending_analysis.category_wise.map((entry, idx) => (
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
                  {data.spending_analysis.category_wise.map((c, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full shrink-0"
                          style={{
                            backgroundColor:
                              CATEGORY_COLORS[c.category] ||
                              CHART_PALETTE[i % CHART_PALETTE.length],
                          }}
                        />
                        <span className="font-medium text-slate-700 truncate">{c.category}</span>
                      </div>
                      <span className="font-bold text-slate-900">
                        {formatINR(c.spent)} ({c.percentage}%)
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Monthly Spending Trend */}
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                Monthly Spending Trend
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Monthly aggregate expenditures across active cycles.
              </p>
            </div>

            {(!data?.spending_analysis?.monthly ||
              data.spending_analysis.monthly.length === 0) ? (
              <div className="h-64 flex items-center justify-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm">
                Log expense transactions across multiple months to view trend.
              </div>
            ) : (
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.spending_analysis.monthly} margin={{ top: 10, right: 10, left: 10, bottom: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} />
                    <YAxis
                      tick={{ fontSize: 11, fill: "#64748b" }}
                      tickLine={false}
                      tickFormatter={(val) => formatCompactCurrency(val)}
                    />
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
                    <Bar dataKey="spent" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 3: BUDGET RECOMMENDATIONS */}
      {activeTab === "budget" && (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Target className="w-5 h-5 text-indigo-600" />
                  50 / 30 / 20 Rule Budget Intelligence
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {data?.budget_recommendation?.basis ||
                    "Log regular transactions to unlock calibrated budget caps."}
                </p>
              </div>

              <span
                className={`text-xs font-semibold px-3 py-1 rounded-full border ${
                  data?.budget_recommendation?.has_budget
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {data?.budget_recommendation?.has_budget ? "Calibrated" : "Uncalibrated Model"}
              </span>
            </div>

            {/* Target Allocations Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 my-6">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Monthly Expense Budget
                </span>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {formatINR(data?.budget_recommendation?.monthly_budget)}
                </p>
                <span className="text-xs text-slate-500">Recommended monthly cap</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  Weekly Spending Limit
                </span>
                <p className="text-xl font-bold text-slate-900 mt-1">
                  {formatINR(data?.budget_recommendation?.weekly_budget)}
                </p>
                <span className="text-xs text-slate-500">Paced per 7-day cycle</span>
              </div>

              <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200">
                <span className="text-xs font-semibold text-amber-700 uppercase tracking-wider">
                  Emergency Cushion Target
                </span>
                <p className="text-xl font-bold text-amber-900 mt-1">
                  {formatINR(data?.budget_recommendation?.emergency_fund)}
                </p>
                <span className="text-xs text-amber-600">6-month living reserve</span>
              </div>

              <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200">
                <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">
                  Monthly Savings Goal
                </span>
                <p className="text-xl font-bold text-emerald-900 mt-1">
                  {formatINR(data?.budget_recommendation?.savings_goal)}
                </p>
                <span className="text-xs text-emerald-600">20% rule allocation</span>
              </div>
            </div>

            {/* Category Limits Table */}
            <div className="mt-6">
              <h4 className="text-sm font-bold text-slate-900 mb-3">
                Category-Wise Monthly Budget Allocations
              </h4>
              {(!data?.budget_recommendation?.category_limits ||
                data.budget_recommendation.category_limits.length === 0) ? (
                <p className="text-xs text-slate-500 italic">
                  No category limits available yet. Record income and expenses to unlock guidelines.
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                  {data.budget_recommendation.category_limits.map((lim, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg border border-slate-200 bg-white shadow-xs flex justify-between items-center"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2 h-2 rounded-full"
                          style={{
                            backgroundColor:
                              CATEGORY_COLORS[lim.category] || CHART_PALETTE[idx % CHART_PALETTE.length],
                          }}
                        />
                        <span className="text-xs font-medium text-slate-700">{lim.category}</span>
                      </div>
                      <span className="text-xs font-bold text-slate-900">
                        {formatINR(lim.limit)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* TAB 4: AI EXPENSE CLASSIFIER */}
      {activeTab === "classifier" && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="p-6">
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-purple-600" />
              <h3 className="text-base font-bold text-slate-900">
                AI NLP Expense Classification
              </h3>
            </div>
            <p className="text-xs text-slate-500 mb-6">
              Type any raw, free-text payment note (e.g. &ldquo;swiggy dinner with friends&rdquo;,
              &ldquo;uber ride to airport&rdquo;, &ldquo;monthly airtel broadband bill&rdquo;) and the
              trained model will classify it into a standard spending category.
            </p>

            <form onSubmit={handleClassify} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Transaction Description
                </label>
                <input
                  type="text"
                  value={classifierInput}
                  onChange={(e) => setClassifierInput(e.target.value)}
                  placeholder="e.g. Starbucks cappuccino & pastry"
                  className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>

              {classifierError && (
                <div className="p-3 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {classifierError}
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isClassifying}
                leftIcon={<Sparkles className="w-4 h-4 text-purple-200" />}
                className="w-full justify-center bg-purple-600 hover:bg-purple-700"
              >
                {isClassifying ? "Classifying..." : "Classify Description"}
              </Button>
            </form>

            {/* Quick Samples */}
            <div className="mt-6 pt-4 border-t border-slate-100">
              <span className="text-xs text-slate-400 font-medium">Try sample:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {[
                  "Grocery shopping at DMart",
                  "Netflix 4K subscription",
                  "Metro card monthly recharge",
                  "Doctor consultation fee",
                ].map((sample, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => {
                      setClassifierInput(sample);
                    }}
                    className="text-xs px-2.5 py-1 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors"
                  >
                    {sample}
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Classification Output Card */}
          <Card className="p-6 flex flex-col justify-center">
            {classifierResult ? (
              <div className="space-y-4 animate-in fade-in duration-200">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    AI Prediction Result
                  </span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-purple-50 text-purple-700 border border-purple-200">
                    {(classifierResult.confidence * 100).toFixed(0)}% Confidence
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-purple-50/50 border border-purple-100">
                  <span className="text-xs text-purple-700 font-medium">Input Note:</span>
                  <p className="text-sm font-semibold text-slate-900 mt-0.5">
                    &ldquo;{classifierResult.description}&rdquo;
                  </p>

                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      <span className="text-xs text-slate-500 font-medium">Predicted Category:</span>
                      <p className="text-xl font-bold text-purple-900 mt-0.5">
                        {classifierResult.category}
                      </p>
                    </div>

                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => {
                        handleOpenAddModal(classifierResult.category);
                      }}
                      leftIcon={<Plus className="w-3.5 h-3.5" />}
                    >
                      Use in Transaction
                    </Button>
                  </div>
                </div>

                <div className="text-xs text-slate-500 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  Logged safely to model prediction audit logs in PostgreSQL.
                </div>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-center p-6 border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400">
                <Sparkles className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-sm font-medium text-slate-600">No Description Tested Yet</p>
                <p className="text-xs text-slate-400 mt-1 max-w-xs">
                  Enter a transaction description on the left to test the natural language expense
                  classifier.
                </p>
              </div>
            )}
          </Card>
        </div>
      )}

      {/* TAB 5: TRANSACTIONS LEDGER */}
      {activeTab === "transactions" && (
        <Card className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h3 className="text-base font-bold text-slate-900">Financial Transactions Ledger</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Real-time records synced directly with PostgreSQL.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative">
                <Search className="w-4 h-4 absolute left-2.5 top-2.5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search category or date..."
                  className="pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 w-44"
                />
              </div>

              {/* Filter Type */}
              <select
                value={filterType}
                onChange={(e) => setFilterType(e.target.value)}
                className="px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="All">All Types</option>
                <option value="Income">Income</option>
                <option value="Expense">Expense</option>
                <option value="Savings">Savings</option>
              </select>

              {/* Filter Category */}
              <select
                value={filterCategory}
                onChange={(e) => setFilterCategory(e.target.value)}
                className="px-2.5 py-1.5 text-xs border border-slate-300 rounded-lg bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="All">All Categories</option>
                {categoriesList.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>

              <Button
                variant="primary"
                size="sm"
                onClick={() => handleOpenAddModal()}
                leftIcon={<Plus className="w-3.5 h-3.5" />}
              >
                New Entry
              </Button>
            </div>
          </div>

          {filteredTransactions.length === 0 ? (
            <div className="py-12 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50 text-slate-400 text-sm">
              {data?.transactions.length === 0
                ? "No financial transactions recorded yet. Click \"New Entry\" to add one."
                : "No transactions match your current search/filter criteria."}
            </div>
          ) : (
            <div className="overflow-x-auto border border-slate-200 rounded-xl">
              <table className="w-full text-left text-xs text-slate-600">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Category</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4 text-right">Amount</th>
                    <th className="py-3 px-4 text-center">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredTransactions.map((tx) => {
                    const isIncome = tx.transaction_type === "Income";
                    const isExpense = tx.transaction_type === "Expense";

                    return (
                      <tr key={tx.record_id} className="hover:bg-slate-50/80 dark:hover:bg-slate-800/60 transition-colors">
                        <td className="py-3 px-4 font-medium text-slate-900 dark:text-slate-100 whitespace-nowrap">
                          {formatDate(tx.date)}
                        </td>
                        <td className="py-3 px-4">
                          <span className="inline-flex items-center gap-1.5 font-semibold text-slate-800">
                            <span
                              className="w-2 h-2 rounded-full"
                              style={{ backgroundColor: CATEGORY_COLORS[tx.category] || "#64748b" }}
                            />
                            {tx.category}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                              isIncome
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : isExpense
                                ? "bg-rose-50 text-rose-700 border-rose-200"
                                : "bg-indigo-50 text-indigo-700 border-indigo-200"
                            }`}
                          >
                            {tx.transaction_type}
                          </span>
                        </td>
                        <td
                          className={`py-3 px-4 text-right font-bold whitespace-nowrap ${
                            isIncome
                              ? "text-emerald-600"
                              : isExpense
                              ? "text-rose-600"
                              : "text-indigo-600"
                          }`}
                        >
                          {isIncome ? "+" : isExpense ? "-" : ""}
                          {formatINR(tx.amount)}
                        </td>
                        <td className="py-3 px-4 text-center whitespace-nowrap">
                          <div className="flex items-center justify-center gap-1">
                            <button
                              onClick={() => handleOpenEditModal(tx)}
                              className="p-1 text-slate-400 hover:text-indigo-600 rounded transition-colors"
                              title="Edit Transaction"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => setDeleteConfirmTx(tx)}
                              className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                              title="Delete Transaction"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* ADD / EDIT TRANSACTION MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-md w-full p-6 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex justify-between items-center pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                {editingTx ? <Edit3 className="w-4 h-4 text-indigo-600" /> : <Plus className="w-4 h-4 text-indigo-600" />}
                {editingTx ? "Edit Financial Record" : "Add Financial Record"}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* In-Modal AI Auto-detect Box (Only in Add Mode) */}
            {!editingTx && (
              <div className="mt-4 p-3 bg-purple-50/50 border border-purple-100 rounded-xl space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-800">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Auto-Classify with AI</span>
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={modalAiPrompt}
                    onChange={(e) => setModalAiPrompt(e.target.value)}
                    placeholder="e.g. Swiggy food delivery or Uber"
                    className="flex-1 px-2.5 py-1 text-xs border border-purple-200 rounded-lg bg-white focus:outline-none focus:ring-1 focus:ring-purple-500"
                  />
                  <button
                    type="button"
                    disabled={isModalDetecting || !modalAiPrompt.trim()}
                    onClick={handleModalAutoDetect}
                    className="px-2.5 py-1 text-xs font-semibold rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-50"
                  >
                    {isModalDetecting ? "..." : "Detect"}
                  </button>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmitTx} className="space-y-4 mt-4">
              {formError && (
                <div className="p-2.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  {formError}
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Transaction Type
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {(compact_types => compact_types.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setFormType(t as TransactionType)}
                      className={`py-1.5 text-xs font-semibold rounded-lg border transition-colors ${
                        formType === t
                          ? t === "Income"
                            ? "bg-emerald-600 text-white border-emerald-600"
                            : t === "Expense"
                            ? "bg-rose-600 text-white border-rose-600"
                            : "bg-indigo-600 text-white border-indigo-600"
                          : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                      }`}
                    >
                      {t}
                    </button>
                  )))(["Expense", "Income", "Savings"])}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category
                </label>
                <select
                  value={formCategory}
                  onChange={(e) => setFormCategory(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {categoriesList.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Amount ({currencySymbol})
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0.01"
                  value={formAmount}
                  onChange={(e) => setFormAmount(e.target.value)}
                  placeholder="e.g. 1500"
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Date
                </label>
                <input
                  type="date"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={isSubmitting}
                >
                  {editingTx ? "Save Changes" : "Record Transaction"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DELETE CONFIRMATION MODAL */}
      {deleteConfirmTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl shadow-xl border border-slate-200 max-w-sm w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-rose-100 rounded-xl text-rose-600 shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">Confirm Deletion</h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  Are you sure you want to delete this {deleteConfirmTx.category} ({formatINR(deleteConfirmTx.amount)}) entry?
                </p>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setDeleteConfirmTx(null)}
                disabled={isDeleting}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                size="sm"
                onClick={handleConfirmDelete}
                isLoading={isDeleting}
              >
                Delete Record
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
