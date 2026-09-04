export interface User {
  user_id: number;
  name: string;
  email: string;
  gender?: string;
  age?: number;
  occupation?: string;
  created_at?: string;
}

export interface Goal {
  goal_id: number;
  user_id?: number;
  goal_name: string;
  target_amount: number;
  current_progress: number;
  target_date?: string | null;
  progress_pct: number;
  is_completed?: boolean;
  status?: 'completed' | 'overdue' | 'active';
  days_remaining?: number | null;
}

export interface HealthVitalityKPI {
  score: number | null;
  max: number;
  level: string;
  has_real_data: boolean;
}

export interface CognitiveFocusKPI {
  score: number | null;
  max: number;
  level: string;
  has_real_data: boolean;
}

export interface SavedMoneyKPI {
  total_savings: number;
  monthly_income: number;
  monthly_expenses: number;
  monthly_savings: number;
  projected_1yr: number;
  monthly_rate: number;
  has_real_data: boolean;
}

export interface SleepKPI {
  avg_hours: number | null;
  status: string;
  has_real_data: boolean;
}

export interface WeeklyStudyKPI {
  total_hours: number;
  peak_focus: string;
  has_real_data: boolean;
}

export interface GoalProgressKPI {
  average_pct: number;
  count: number;
  has_real_data: boolean;
}

export interface DashboardKPIs {
  health_vitality: HealthVitalityKPI;
  cognitive_focus: CognitiveFocusKPI;
  saved_money: SavedMoneyKPI;
  sleep: SleepKPI;
  weekly_study: WeeklyStudyKPI;
  goal_progress: GoalProgressKPI;
}

export interface SavingsTrendPoint {
  date: string;
  cumulative_savings: number;
}

export interface StudyDistributionPoint {
  day: string;
  hours: number;
}

export interface TwinInsight {
  category: string;
  priority: string;
  text: string;
  action?: string;
}

export interface DashboardSummaryResponse {
  user: {
    name: string;
    occupation: string;
    age: number;
    days_active: number;
  };
  kpis: DashboardKPIs;
  goals: Goal[];
  savings_trend: SavingsTrendPoint[];
  study_distribution: StudyDistributionPoint[];
  twin_insights: TwinInsight[];
}

export interface ChatStatusResponse {
  provider: string;
  model: string;
  has_api_key: boolean;
  suggested_questions: string[];
  greeting: string;
}

export interface ChatTurnResponse {
  question: string;
  answer: string;
  provider: string;
  model?: string;
  grounded: boolean;
}

export type TaskStatus = 'Upcoming' | 'In Progress' | 'Completed' | 'Missed';

export interface TaskItem {
  schedule_id: number;
  user_id: number;
  activity_name: string;
  planned_time: string | null;
  actual_time: string | null;
  status: TaskStatus;
  date: string;
}

export interface TaskSummary {
  total_tasks: number;
  completed_tasks: number;
  upcoming_tasks: number;
  in_progress_tasks: number;
  missed_tasks: number;
  completion_rate: number;
  peak_focus_time: string;
}

export interface TasksResponse {
  date: string;
  tasks: TaskItem[];
  summary: TaskSummary;
}

export interface CreateTaskRequest {
  activity_name: string;
  date?: string;
  planned_time?: string | null;
  actual_time?: string | null;
  status?: TaskStatus;
}

export interface UpdateTaskRequest {
  activity_name?: string;
  date?: string;
  planned_time?: string | null;
  actual_time?: string | null;
  status?: TaskStatus;
}

export interface StudyActivity {
  activity_id: number;
  user_id: number;
  subject: string;
  hours_logged: number;
  performance_score: number | null;
  date: string;
}

export interface StudySummary {
  total_hours: number | null;
  total_sessions: number;
  avg_performance_score: number | null;
  avg_hours_per_day: number | null;
  days_active: number;
  peak_focus_time: string;
  completion_rate: number | null;
}

export interface WeeklyStudyPoint {
  day: string;
  hours: number;
}

export interface SubjectSummary {
  subject: string;
  total_hours: number;
  session_count: number;
  avg_score: number | null;
}

export interface WeakSubject {
  subject: string;
  avg_score: number;
  risk_score: number;
  level: string;
  trend: number;
  rank: number;
}

export interface StudyGoal {
  goal_id: number;
  goal_name: string;
  target_amount: number;
  current_progress: number;
  target_date: string;
  progress_pct: number;
}

export interface StudyOverviewResponse {
  has_data: boolean;
  activities: StudyActivity[];
  summary: StudySummary;
  weekly_hours: WeeklyStudyPoint[];
  subjects_summary: SubjectSummary[];
  weak_subjects: WeakSubject[];
  study_goals: StudyGoal[];
  supported_subjects: string[];
}

export interface CreateStudyActivityRequest {
  subject: string;
  hours_logged: number;
  performance_score?: number | null;
  date?: string;
}

export interface UpdateStudyActivityRequest {
  subject?: string;
  hours_logged?: number;
  performance_score?: number | null;
  date?: string;
}

export interface StudyPredictRequest {
  subject: string;
  hours_logged?: number;
  days_to_exam?: number;
  study_consistency?: number;
  prior_score?: number | null;
}

export interface StudyPredictResponse {
  subject: string;
  predicted_score: number;
  predicted_gpa: number;
  band: string;
  prior_score: number;
  is_prediction: boolean;
}

export interface SuggestionItem {
  id: string;
  category: string;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  title: string;
  description: string;
  reason?: string | null;
  benefits: string[];
  risks: string[];
  action?: string | null;
  action_route?: string | null;
  action_label?: string | null;
  evidence?: Record<string, any> | null;
  created_at?: string | null;
}

export interface UnlockAction {
  title: string;
  description: string;
  route: string;
  label: string;
}

export interface CalibrationState {
  is_calibrated: boolean;
  message: string;
  missing_data: string[];
  unlock_actions: UnlockAction[];
}

export interface SuggestionsResponse {
  has_data: boolean;
  total_count: number;
  categories: string[];
  priority_counts: {
    Critical: number;
    High: number;
    Medium: number;
    Low: number;
  };
  suggestions: SuggestionItem[];
  calibration_state: CalibrationState;
}

// ---------------------------------------------------------------------------
// Wealth & Finance
// ---------------------------------------------------------------------------

export type TransactionType = 'Income' | 'Expense' | 'Savings';

export interface TransactionItem {
  record_id: number;
  user_id: number;
  category: string;
  amount: number;
  transaction_type: TransactionType;
  date: string;
}

export interface FinancialSummary {
  total_income: number | null;
  total_expenses: number | null;
  net_cash_flow: number | null;
  total_savings: number | null;
  monthly_rate: number | null;
  savings_rate_pct: number | null;
  transaction_count: number;
  months_active: number;
}

export interface SpendingCategoryPoint {
  category: string;
  spent: number;
  percentage: number;
}

export interface SpendingMonthlyPoint {
  month: string;
  spent: number;
}

export interface SpendingAnalysisData {
  total_spent: number | null;
  top_category: string | null;
  top_category_amount: number | null;
  category_wise: SpendingCategoryPoint[];
  monthly: SpendingMonthlyPoint[];
}

export interface SavingsTrendPoint {
  date: string;
  cumulative_savings: number;
}

export interface SavingsTrendData {
  history: SavingsTrendPoint[];
  forecast_1yr: number | null;
  monthly_rate: number | null;
}

export interface BudgetCategoryLimit {
  category: string;
  limit: number;
}

export interface BudgetRecommendationData {
  has_budget: boolean;
  monthly_budget: number | null;
  weekly_budget: number | null;
  emergency_fund: number | null;
  savings_goal: number | null;
  basis: string;
  category_limits: BudgetCategoryLimit[];
}

export interface WealthOverviewResponse {
  has_data: boolean;
  summary: FinancialSummary;
  transactions: TransactionItem[];
  spending_analysis: SpendingAnalysisData;
  savings_trend: SavingsTrendData;
  budget_recommendation: BudgetRecommendationData;
  supported_categories: string[];
  supported_types: string[];
}

export interface CreateTransactionRequest {
  category: string;
  amount: number;
  transaction_type: TransactionType;
  date?: string;
}

export interface UpdateTransactionRequest {
  category?: string;
  amount?: number;
  transaction_type?: TransactionType;
  date?: string;
}

export interface ExpenseClassifyRequest {
  description: string;
}

export interface ExpenseClassifyResponse {
  description: string;
  category: string;
  confidence: number;
  is_prediction: boolean;
}

export interface ForecastTimelinePoint {
  month: number;
  date: string;
  projected_savings: number;
}

export interface ForecastSimulateRequest {
  horizon_months: number;
  extra_monthly_savings: number;
}

export interface ForecastSimulateResponse {
  current_savings: number;
  baseline_monthly_rate: number;
  effective_monthly_rate: number;
  horizon_months: number;
  projected_final_savings: number;
  projected_timeline: ForecastTimelinePoint[];
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export type AnalyticsTimeRange = '7D' | '30D' | '90D' | '1Y';

export interface AnalyticsOverviewMetrics {
  productivity_score: number | null;
  tasks_completed: number;
  tasks_total: number;
  study_hours: number | null;
  avg_study_score: number | null;
  net_cash_flow: number | null;
  total_savings: number | null;
  habit_consistency: number | null;
  avg_sleep_hours: number | null;
  active_goals_count: number;
  avg_goal_progress: number | null;
}

export interface ProductivityPoint {
  date: string;
  completed: number;
  total: number;
  completion_rate: number;
}

export interface ProductivityTrendData {
  has_data: boolean;
  series: ProductivityPoint[];
}

export interface StudyDailyPoint {
  date: string;
  hours: number;
  avg_score: number | null;
}

export interface StudySubjectPoint {
  subject: string;
  hours: number;
  percentage: number;
  avg_score: number | null;
}

export interface StudyAnalyticsData {
  has_data: boolean;
  total_hours: number;
  sessions_count: number;
  avg_performance_score: number | null;
  peak_focus_time: string;
  daily_trend: StudyDailyPoint[];
  subject_breakdown: StudySubjectPoint[];
}

export interface FinancialCashflowPoint {
  period: string;
  income: number;
  expenses: number;
  net: number;
}

export interface FinancialAnalyticsData {
  has_data: boolean;
  total_income: number;
  total_expenses: number;
  net_savings: number;
  spending_by_category: SpendingCategoryPoint[];
  cashflow_trend: FinancialCashflowPoint[];
}

export interface HabitMetricPoint {
  habit_name: string;
  rate: number;
  trend_pct: number;
  insight: string;
}

export interface SleepActivityPoint {
  date: string;
  sleep_hours: number | null;
  steps: number | null;
  exercise_minutes: number | null;
}

export interface HabitLifestyleAnalyticsData {
  has_data: boolean;
  overall_consistency: number | null;
  habits: HabitMetricPoint[];
  sleep_activity_trend: SleepActivityPoint[];
}

export interface GoalAnalyticsPoint {
  goal_id: number;
  goal_name: string;
  target_amount: number;
  current_progress: number;
  progress_pct: number;
  target_date: string | null;
}

export interface GoalsAnalyticsData {
  has_data: boolean;
  goals: GoalAnalyticsPoint[];
}

export interface TwinInsight {
  domain: string;
  title: string;
  message: string;
  type: 'positive' | 'neutral' | 'attention';
}

export interface AnalyticsResponse {
  range: AnalyticsTimeRange;
  start_date: string;
  end_date: string;
  has_data: boolean;
  overview_metrics: AnalyticsOverviewMetrics;
  productivity_trend: ProductivityTrendData;
  study_analytics: StudyAnalyticsData;
  financial_analytics: FinancialAnalyticsData;
  habit_lifestyle_analytics: HabitLifestyleAnalyticsData;
  goals_progress: GoalsAnalyticsData;
  twin_insights: TwinInsight[];
}

// ---------------------------------------------------------------------------
// What-If Simulation
// ---------------------------------------------------------------------------

export type SimulationDomain = 'finance' | 'study' | 'habits';

export interface FinancialGoalItem {
  goal_id: number;
  goal_name: string;
  target_amount: number;
  current_progress: number;
  target_date: string | null;
}

export interface SimulationBaselineFinancial {
  has_data: boolean;
  monthly_income: number;
  monthly_expenses: number;
  monthly_savings: number;
  total_savings: number;
  goals: FinancialGoalItem[];
}

export interface SimulationBaselineStudy {
  has_data: boolean;
  avg_hours_per_day: number;
  avg_performance_score: number;
  subjects: string[];
  days_active: number;
}

export interface SimulationBaselineHabits {
  has_data: boolean;
  avg_completion_rate: number;
  exercise_frequency: number;
  avg_steps: number;
  avg_sleep_hours: number;
  avg_exercise_minutes: number;
  habit_names: string[];
}

export interface SimulationBaselineResponse {
  financial: SimulationBaselineFinancial;
  study: SimulationBaselineStudy;
  habits: SimulationBaselineHabits;
}

export interface CustomScenarioInput {
  name: string;
  description?: string;
  monthly_saving?: number;
  monthly_expenses?: number;
  hours_per_day?: number;
  completion_rate?: number;
  exercise_frequency?: number;
}

export interface RunSimulationRequest {
  domain: SimulationDomain;
  horizon_months: number;
  consistency?: number;
  custom_scenarios?: CustomScenarioInput[];
}

export interface ScenarioResult {
  name: string;
  description: string;
  is_baseline: boolean;
  input_params: Record<string, any>;
  output_metrics: Record<string, any>;
  score: number;
  score_breakdown: Record<string, number>;
  time_series: Array<Record<string, any>>;
}

export interface SimulationRecommendation {
  recommended_scenario: string;
  score: number;
  reason: string;
  benefits: string[];
  risks: string[];
  next_actions: string[];
  baseline_comparison: Record<string, any>;
}

export interface RunSimulationResponse {
  domain: SimulationDomain;
  horizon_months: number;
  has_baseline_data: boolean;
  scenarios: ScenarioResult[];
  comparison_table: Array<Record<string, any>>;
  recommendation: SimulationRecommendation | null;
  assumptions: string[];
  disclaimer: string;
}

export interface SaveSimulationRequest {
  domain: SimulationDomain;
  title: string;
  horizon_months: number;
  scenarios: ScenarioResult[];
  recommendation?: SimulationRecommendation | null;
  parameters?: Record<string, any>;
}

export interface SaveSimulationResponse {
  simulation_id: number;
  message: string;
}

export interface SimulationHistoryItem {
  simulation_id: number;
  simulation_type: string;
  title: string;
  horizon_months: number;
  created_at: string;
  parameters?: Record<string, any>;
}

// ---------------------------------------------------------------------------
// Profile & Goals
// ---------------------------------------------------------------------------

export interface UserProfileResponse {
  user_id: number;
  name: string;
  email: string;
  gender?: string | null;
  age?: number | null;
  occupation?: string | null;
  created_at: string;
  days_active: number;
  active_goals_count: number;
  completed_goals_count: number;
  avg_goal_progress: number;
  latest_health?: {
    record_date: string;
    height_cm?: number | null;
    weight_kg?: number | null;
    bmi?: number | null;
    bmi_category?: string | null;
  } | null;
}

export interface UpdateProfileRequest {
  name?: string;
  gender?: 'Male' | 'Female';
  age?: number;
  occupation?: string;
}

export interface GoalsListResponse {
  goals: Goal[];
  active_count: number;
  completed_count: number;
  avg_progress_pct: number;
}

export interface CreateGoalRequest {
  goal_name: string;
  target_amount: number;
  current_progress?: number;
  target_date?: string;
}

export interface UpdateGoalRequest {
  goal_name?: string;
  target_amount?: number;
  current_progress?: number;
  target_date?: string;
}

export interface UserPreferences {
  currency: 'INR' | 'USD' | 'EUR' | 'GBP';
  timezone: string;
  date_format: 'YYYY-MM-DD' | 'DD/MM/YYYY' | 'MM/DD/YYYY';
  theme: 'light' | 'dark' | 'system';
  ai_suggestions_enabled: boolean;
  weekly_digest_enabled: boolean;
}

export interface UpdatePreferencesRequest {
  currency?: 'INR' | 'USD' | 'EUR' | 'GBP';
  timezone?: string;
  date_format?: 'YYYY-MM-DD' | 'DD/MM/YYYY' | 'MM/DD/YYYY';
  theme?: 'light' | 'dark' | 'system';
  ai_suggestions_enabled?: boolean;
  weekly_digest_enabled?: boolean;
}

export interface AISystemConfig {
  provider: string;
  model: string;
  has_api_key: boolean;
  temperature: number;
  max_tokens: number;
  offline_fallback_active: boolean;
}

export interface AccountSecurityInfo {
  user_id: number;
  email: string;
  name: string;
  created_at?: string | null;
  auth_method: string;
  password_encryption: string;
  session_duration_hours: number;
}

export interface SettingsResponse {
  preferences: UserPreferences;
  ai_config: AISystemConfig;
  account_security: AccountSecurityInfo;
}
