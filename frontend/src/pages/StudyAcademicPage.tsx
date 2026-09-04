import React, { useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  Calendar,
  Clock,
  GraduationCap,
  Award,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Plus,
  Trash2,
  Edit3,
  Sparkles,
  Zap,
  Target,
  X,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { api } from '../services/api';
import type {
  StudyActivity,
  StudyOverviewResponse,
  StudyPredictResponse,
} from '../types/api';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Badge } from '../components/ui/Badge';
import type { BadgeVariant } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { usePreferences } from '../context/PreferencesContext';

export const StudyAcademicPage: React.FC = () => {
  const { formatDate } = usePreferences();
  const [data, setData] = useState<StudyOverviewResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Subject filter in activity table
  const [selectedSubjectFilter, setSelectedSubjectFilter] = useState<string>('All');

  // Log/Edit Activity Modal
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingActivity, setEditingActivity] = useState<StudyActivity | null>(null);
  const [formSubject, setFormSubject] = useState<string>('Mathematics');
  const [formHours, setFormHours] = useState<string>('2.0');
  const [formScore, setFormScore] = useState<string>('');
  const [formDate, setFormDate] = useState<string>(() => new Date().toISOString().split('T')[0]);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  // ML Performance Predictor State
  const [predictSubject, setPredictSubject] = useState<string>('Mathematics');
  const [predictHours, setPredictHours] = useState<number>(4.0);
  const [predictDays, setPredictDays] = useState<number>(14);
  const [predictConsistency, setPredictConsistency] = useState<number>(0.8);
  const [predictPriorScore, setPredictPriorScore] = useState<string>('');
  const [isPredicting, setIsPredicting] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<StudyPredictResponse | null>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  const fetchStudyData = async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const resp = await api.getStudyOverview();
      setData(resp);
      if (resp.supported_subjects && resp.supported_subjects.length > 0) {
        if (!resp.supported_subjects.includes(formSubject)) {
          setFormSubject(resp.supported_subjects[0]);
        }
        if (!resp.supported_subjects.includes(predictSubject)) {
          setPredictSubject(resp.supported_subjects[0]);
        }
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to retrieve study intelligence from database.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStudyData();
  }, []);

  // Open Add Modal
  const handleOpenAddModal = () => {
    setEditingActivity(null);
    const defaultSubject =
      data?.supported_subjects && data.supported_subjects.length > 0
        ? data.supported_subjects[0]
        : 'Mathematics';
    setFormSubject(defaultSubject);
    setFormHours('2.0');
    setFormScore('');
    setFormDate(new Date().toISOString().split('T')[0]);
    setFormError(null);
    setIsModalOpen(true);
  };

  // Open Edit Modal
  const handleOpenEditModal = (activity: StudyActivity) => {
    setEditingActivity(activity);
    setFormSubject(activity.subject);
    setFormHours(String(activity.hours_logged));
    setFormScore(activity.performance_score !== null ? String(activity.performance_score) : '');
    setFormDate(activity.date);
    setFormError(null);
    setIsModalOpen(true);
  };

  // Handle Submit Modal Form
  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    const hours = parseFloat(formHours);
    if (isNaN(hours) || hours <= 0 || hours > 24) {
      setFormError('Please enter a valid study duration between 0.1 and 24 hours.');
      return;
    }

    let score: number | null = null;
    if (formScore.trim() !== '') {
      score = parseFloat(formScore);
      if (isNaN(score) || score < 0 || score > 100) {
        setFormError('Performance score must be between 0 and 100.');
        return;
      }
    }

    if (!formSubject.trim()) {
      setFormError('Please select or specify a subject.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      if (editingActivity) {
        await api.updateStudyActivity(editingActivity.activity_id, {
          subject: formSubject.trim(),
          hours_logged: hours,
          performance_score: score,
          date: formDate,
        });
      } else {
        await api.createStudyActivity({
          subject: formSubject.trim(),
          hours_logged: hours,
          performance_score: score,
          date: formDate,
        });
      }
      setIsModalOpen(false);
      await fetchStudyData(true);
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save study activity.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Delete Activity
  const handleDeleteActivity = async (activityId: number) => {
    if (!window.confirm('Are you sure you want to remove this logged study session?')) return;
    try {
      await api.deleteStudyActivity(activityId);
      await fetchStudyData(true);
    } catch (err: any) {
      alert(err?.message || 'Could not delete study activity.');
    }
  };

  // Handle Run ML Prediction
  const handleRunPrediction = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsPredicting(true);
    setPredictError(null);
    try {
      const prior = predictPriorScore.trim() ? parseFloat(predictPriorScore) : null;
      const resp = await api.predictStudyPerformance({
        subject: predictSubject,
        hours_logged: predictHours,
        days_to_exam: predictDays,
        study_consistency: predictConsistency,
        prior_score: prior,
      });
      setPredictionResult(resp);
    } catch (err: any) {
      setPredictError(err?.message || 'Machine learning prediction model failed.');
    } finally {
      setIsPredicting(false);
    }
  };

  // Filtered Activities
  const filteredActivities = useMemo(() => {
    if (!data?.activities) return [];
    if (selectedSubjectFilter === 'All') return data.activities;
    return data.activities.filter((a) => a.subject === selectedSubjectFilter);
  }, [data?.activities, selectedSubjectFilter]);

  // Unique subjects from activities + supported
  const filterOptions = useMemo(() => {
    const list = new Set<string>();
    if (data?.activities) {
      data.activities.forEach((a) => list.add(a.subject));
    }
    return Array.from(list).sort();
  }, [data?.activities]);

  const getRiskBadgeVariant = (level: string): BadgeVariant => {
    switch (level.toLowerCase()) {
      case 'critical':
        return 'danger';
      case 'high':
        return 'warning';
      case 'medium':
        return 'purple';
      case 'low':
        return 'indigo';
      case 'good':
      default:
        return 'success';
    }
  };

  const getScoreColor = (score: number | null) => {
    if (score === null) return 'text-slate-400';
    if (score >= 80) return 'text-emerald-600';
    if (score >= 60) return 'text-indigo-600';
    if (score >= 40) return 'text-amber-600';
    return 'text-rose-600';
  };

  const getBandBadgeVariant = (band: string): BadgeVariant => {
    if (band.includes('A') || band.includes('Distinction')) return 'success';
    if (band.includes('B') || band.includes('Merit')) return 'indigo';
    if (band.includes('C') || band.includes('Pass')) return 'warning';
    return 'danger';
  };

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
          title="Study System Connection Error"
          message={error}
          onRetry={() => fetchStudyData()}
        />
      </div>
    );
  }

  const hasData = data?.has_data ?? false;
  const summary = data?.summary;
  const weeklyHours = data?.weekly_hours ?? [];
  const weakSubjects = data?.weak_subjects ?? [];
  const subjectsSummary = data?.subjects_summary ?? [];
  const studyGoals = data?.study_goals ?? [];
  const supportedSubjects = data?.supported_subjects ?? [
    'Mathematics',
    'Physics',
    'Chemistry',
    'Biology',
    'Computer Science',
    'Economics',
    'History',
    'Literature',
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Study & Academic Intelligence
            </h1>
            <Badge variant="indigo" size="sm">
              Phase 7
            </Badge>
          </div>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Real-time focus logs, curriculum mastery breakdowns, and ML exam performance forecasts
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchStudyData(true)}
            isLoading={isRefreshing}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />}
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleOpenAddModal}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            Log Study Session
          </Button>
        </div>
      </div>

      {/* 2. Key Academic Metrics (KPI Cards) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Study Time"
          value={
            hasData && summary?.total_hours !== null && summary?.total_hours !== undefined
              ? `${summary.total_hours} hrs`
              : 'No Data'
          }
          subtitle={
            hasData
              ? `${summary?.total_sessions ?? 0} logged session${summary?.total_sessions === 1 ? '' : 's'}`
              : 'Requires logged sessions'
          }
          icon={<Clock className="w-4 h-4" />}
          badgeText={hasData ? 'PostgreSQL' : 'Uncalibrated'}
          badgeVariant={hasData ? 'indigo' : 'default'}
        />

        <MetricCard
          title="Average Performance"
          value={
            hasData && summary?.avg_performance_score !== null && summary?.avg_performance_score !== undefined
              ? `${summary.avg_performance_score}%`
              : 'Uncalibrated'
          }
          subtitle={
            hasData && summary?.avg_performance_score !== null
              ? 'Historical quiz & exam average'
              : 'Scores calibrate with entries'
          }
          icon={<Award className="w-4 h-4" />}
          badgeText={hasData && summary?.avg_performance_score !== null ? 'Graded' : 'Pending Data'}
          badgeVariant={hasData && summary?.avg_performance_score !== null ? 'success' : 'default'}
        />

        <MetricCard
          title="Active Study Days"
          value={hasData && summary?.days_active ? `${summary.days_active} Days` : '0 Days'}
          subtitle={
            hasData && summary?.avg_hours_per_day !== null && summary?.avg_hours_per_day !== undefined
              ? `Avg ${summary.avg_hours_per_day}h / active day`
              : 'No active days logged'
          }
          icon={<Calendar className="w-4 h-4" />}
          badgeText={hasData ? 'Consistency' : 'Inactive'}
          badgeVariant={hasData ? 'indigo' : 'default'}
        />

        <MetricCard
          title="Peak Focus Window"
          value={summary?.peak_focus_time || 'Not Enough Data'}
          subtitle={
            hasData && summary?.peak_focus_time !== 'Not Enough Data'
              ? 'Derived from study schedule'
              : 'Awaiting activity pattern'
          }
          icon={<Zap className="w-4 h-4" />}
          badgeText={hasData ? 'Optimized' : 'Calibrating'}
          badgeVariant={hasData ? 'purple' : 'default'}
        />
      </div>

      {/* 3. Weekly Focus Distribution & ML Weak Subject Detection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Weekly Study Time (Bar Chart) (Col Span 2) */}
        <Card className="lg:col-span-2 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900 tracking-tight">
                    Weekly Focus Distribution
                  </h2>
                  <p className="text-xs text-slate-500">
                    Daily study hours logged over the last 7 calendar days
                  </p>
                </div>
              </div>
              <Badge variant="indigo" size="sm">
                7 Days
              </Badge>
            </div>

            <div className="h-64 w-full pt-2">
              {hasData && weeklyHours.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyHours} margin={{ top: 10, right: 10, left: -15, bottom: 0 }}>
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
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05)',
                      }}
                      formatter={(val: any) => [`${val} hrs`, 'Study Hours']}
                    />
                    <Bar dataKey="hours" fill="#6366f1" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState
                  icon={<Clock className="w-6 h-6 text-slate-400" />}
                  title="No Study Hours This Week"
                  description="No study sessions have been logged for the current calendar week. Daily focus distribution will automatically chart as sessions are recorded."
                  className="h-full justify-center border-dashed"
                />
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              Real PostgreSQL session records
            </span>
            <span>Target: 20 hrs/week</span>
          </div>
        </Card>

        {/* Right Column: ML Weak Subject & Risk Detection (Col 1) */}
        <Card className="flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-base font-semibold text-slate-900 tracking-tight">
                    Academic Risk Radar
                  </h2>
                  <p className="text-xs text-slate-500">AI detection of weak curriculum areas</p>
                </div>
              </div>
              <Badge variant="purple" size="sm">
                ML Model
              </Badge>
            </div>

            <div className="space-y-3">
              {weakSubjects.length > 0 ? (
                weakSubjects.map((sub, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-slate-50/80 border border-slate-200/60 transition-all hover:bg-slate-50"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-semibold text-slate-900">
                          #{sub.rank} {sub.subject}
                        </span>
                      </div>
                      <Badge variant={getRiskBadgeVariant(sub.level)} size="sm">
                        {sub.level} Risk
                      </Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-2 mt-2 pt-2 border-t border-slate-200/60 text-[11px] text-slate-500">
                      <div>
                        Avg Score:{' '}
                        <span className="font-semibold text-slate-700">
                          {sub.avg_score.toFixed(1)}%
                        </span>
                      </div>
                      <div className="text-right">
                        Risk Score:{' '}
                        <span className="font-semibold text-rose-600">
                          {sub.risk_score.toFixed(1)}/100
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              ) : hasData ? (
                <div className="p-4 text-center rounded-xl bg-emerald-50/60 border border-emerald-100">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
                  <p className="text-xs font-semibold text-emerald-900">
                    No Critical Weak Areas Detected
                  </p>
                  <p className="text-[11px] text-emerald-700 mt-1">
                    All tracked subjects currently meet or exceed healthy performance baselines.
                  </p>
                </div>
              ) : (
                <div className="p-5 text-center rounded-xl bg-slate-50 border border-dashed border-slate-200 text-xs text-slate-500">
                  <Sparkles className="w-5 h-5 text-slate-400 mx-auto mb-2" />
                  <p className="font-medium text-slate-700">ML Risk Radar Calibrating</p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Log at least one study session with a performance score to initiate machine learning risk detection.
                  </p>
                </div>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400 text-center">
            Powered by Random Forest regression & heuristic risk classification.
          </div>
        </Card>
      </div>

      {/* 4. Subject Mastery Breakdown & Active Study Goals */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Subject Mastery Table (Col Span 2) */}
        <Card className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-semibold text-slate-900 tracking-tight">
                Subject Mastery Breakdown
              </h2>
              <p className="text-xs text-slate-500">
                Aggregated hours and average scores per course
              </p>
            </div>
            <span className="text-xs font-medium text-slate-500">
              {subjectsSummary.length} Subject{subjectsSummary.length === 1 ? '' : 's'} Active
            </span>
          </div>

          {subjectsSummary.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-100 text-xs font-semibold uppercase text-slate-400">
                    <th className="pb-3 font-medium">Subject</th>
                    <th className="pb-3 font-medium text-right">Total Hours</th>
                    <th className="pb-3 font-medium text-right">Sessions</th>
                    <th className="pb-3 font-medium text-right">Avg Score</th>
                    <th className="pb-3 font-medium text-right">Mastery Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {subjectsSummary.map((sub, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3 font-medium text-slate-900 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-indigo-500" />
                        {sub.subject}
                      </td>
                      <td className="py-3 text-right font-medium text-slate-700">
                        {sub.total_hours}h
                      </td>
                      <td className="py-3 text-right text-slate-500">
                        {sub.session_count}
                      </td>
                      <td className={`py-3 text-right font-semibold ${getScoreColor(sub.avg_score)}`}>
                        {sub.avg_score !== null ? `${sub.avg_score.toFixed(1)}%` : '—'}
                      </td>
                      <td className="py-3 text-right">
                        {sub.avg_score !== null ? (
                          sub.avg_score >= 80 ? (
                            <Badge variant="success" size="sm">Mastered</Badge>
                          ) : sub.avg_score >= 60 ? (
                            <Badge variant="indigo" size="sm">Proficient</Badge>
                          ) : (
                            <Badge variant="warning" size="sm">Needs Review</Badge>
                          )
                        ) : (
                          <Badge variant="default" size="sm">Logged Only</Badge>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-slate-400 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
              No subject logs recorded yet. Add your study sessions to track course mastery.
            </div>
          )}
        </Card>

        {/* Academic Goals (Col 1) */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <Target className="w-4 h-4" />
              </div>
              <h2 className="text-base font-semibold text-slate-900 tracking-tight">
                Study Goals
              </h2>
            </div>
            <Badge variant="default" size="sm">
              Targets
            </Badge>
          </div>

          <div className="space-y-4">
            {studyGoals.length > 0 ? (
              studyGoals.map((g) => (
                <div key={g.goal_id} className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-800">{g.goal_name}</span>
                    <span className="text-slate-500 font-mono">
                      {g.current_progress} / {g.target_amount}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-indigo-600 h-full rounded-full transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.max(0, g.progress_pct))}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-slate-400">
                    <span>Target: {g.target_date ? formatDate(g.target_date) : 'Ongoing'}</span>
                    <span className="font-medium text-indigo-600">{g.progress_pct.toFixed(0)}%</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-5 text-center text-xs text-slate-400 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                <p className="font-medium text-slate-600">No Academic Goals Defined</p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Create target GPA or study milestone goals in your Twin Profile.
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* 5. Interactive ML Performance Predictor Card */}
      <Card className="border-indigo-100 bg-gradient-to-br from-white via-indigo-50/20 to-purple-50/20">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md shadow-indigo-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                ML Exam Performance & Grade Predictor
                <Badge variant="indigo" size="sm">
                  Python ML
                </Badge>
              </h2>
              <p className="text-xs text-slate-500">
                Deterministic regression model forecasting test marks and GPA from study intensity, exam proximity, and prior scores
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleRunPrediction} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Subject Selector */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Subject / Course
            </label>
            <select
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={predictSubject}
              onChange={(e) => setPredictSubject(e.target.value)}
            >
              {supportedSubjects.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Planned Hours Logged */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Study Hours Logged
            </label>
            <input
              type="number"
              step="0.5"
              min="0.5"
              max="50"
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={predictHours}
              onChange={(e) => setPredictHours(parseFloat(e.target.value) || 0)}
              required
            />
          </div>

          {/* Days to Exam */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Days to Exam
            </label>
            <input
              type="number"
              min="1"
              max="365"
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={predictDays}
              onChange={(e) => setPredictDays(parseInt(e.target.value) || 1)}
              required
            />
          </div>

          {/* Consistency */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Consistency: {(predictConsistency * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              className="w-full accent-indigo-600 cursor-pointer mt-2"
              value={predictConsistency}
              onChange={(e) => setPredictConsistency(parseFloat(e.target.value))}
            />
          </div>

          {/* Optional Prior Score Override */}
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
              Prior Score % (Optional)
            </label>
            <input
              type="number"
              min="0"
              max="100"
              placeholder="Auto (Historical avg)"
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
              value={predictPriorScore}
              onChange={(e) => setPredictPriorScore(e.target.value)}
            />
          </div>

          <div className="md:col-span-2 lg:col-span-3 flex items-end">
            <Button
              type="submit"
              variant="primary"
              size="md"
              className="w-full sm:w-auto"
              isLoading={isPredicting}
              leftIcon={<Sparkles className="w-4 h-4" />}
            >
              Run AI Grade Predictor
            </Button>
          </div>
        </form>

        {predictError && (
          <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            {predictError}
          </div>
        )}

        {/* Prediction Output Card */}
        {predictionResult && (
          <div className="mt-6 p-4 rounded-xl bg-white border border-indigo-200 shadow-sm animate-fade-in">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-indigo-600" />
                <span className="text-sm font-semibold text-slate-900">
                  Predicted Outcome for {predictionResult.subject}
                </span>
              </div>
              <Badge variant="purple" size="sm">
                🤖 Machine Learning Forecast
              </Badge>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-4">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                  Expected Exam Score
                </span>
                <span className="text-2xl font-bold text-slate-900">
                  {predictionResult.predicted_score.toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Baseline prior: {predictionResult.prior_score.toFixed(1)}%
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                  Estimated GPA Equivalent
                </span>
                <span className="text-2xl font-bold text-indigo-600">
                  {predictionResult.predicted_gpa.toFixed(2)} / 4.0
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Standard 4.0 scale
                </span>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 flex flex-col justify-between">
                <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                  Academic Performance Band
                </span>
                <div className="my-1">
                  <Badge variant={getBandBadgeVariant(predictionResult.band)} size="md">
                    {predictionResult.band}
                  </Badge>
                </div>
                <span className="text-[10px] text-slate-500 block">
                  Calculated from simulated study consistency
                </span>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 6. Recent Study Sessions Table */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900 tracking-tight">
              Logged Study Sessions
            </h2>
            <p className="text-xs text-slate-500">
              Historical activity log stored in PostgreSQL Study_Activities
            </p>
          </div>

          <div className="flex items-center gap-3">
            {filterOptions.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs text-slate-600">
                <span>Filter:</span>
                <select
                  className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none"
                  value={selectedSubjectFilter}
                  onChange={(e) => setSelectedSubjectFilter(e.target.value)}
                >
                  <option value="All">All Subjects ({data?.activities.length ?? 0})</option>
                  {filterOptions.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <Button
              variant="secondary"
              size="sm"
              onClick={handleOpenAddModal}
              leftIcon={<Plus className="w-3.5 h-3.5" />}
            >
              Add Session
            </Button>
          </div>
        </div>

        {filteredActivities.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs font-semibold uppercase text-slate-400">
                  <th className="pb-3 font-medium">Date</th>
                  <th className="pb-3 font-medium">Subject</th>
                  <th className="pb-3 font-medium text-right">Hours Logged</th>
                  <th className="pb-3 font-medium text-right">Performance Score</th>
                  <th className="pb-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredActivities.map((act) => (
                  <tr key={act.activity_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 text-slate-600 text-xs font-mono">
                      {formatDate(act.date)}
                    </td>
                    <td className="py-3 font-medium text-slate-900 flex items-center gap-2">
                      <BookOpen className="w-3.5 h-3.5 text-indigo-500" />
                      {act.subject}
                    </td>
                    <td className="py-3 text-right font-medium text-slate-800">
                      {act.hours_logged.toFixed(1)} hrs
                    </td>
                    <td className={`py-3 text-right font-semibold ${getScoreColor(act.performance_score)}`}>
                      {act.performance_score !== null ? `${act.performance_score}%` : '—'}
                    </td>
                    <td className="py-3 text-right space-x-1">
                      <button
                        onClick={() => handleOpenEditModal(act)}
                        className="p-1 text-slate-400 hover:text-indigo-600 rounded hover:bg-slate-100 transition-colors"
                        title="Edit session"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteActivity(act.activity_id)}
                        className="p-1 text-slate-400 hover:text-rose-600 rounded hover:bg-slate-100 transition-colors"
                        title="Delete session"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={<GraduationCap className="w-8 h-8 text-slate-400" />}
            title="No Study Sessions Recorded"
            description="Start by logging your daily study hours and quiz scores. The AI engine will track your progress and provide predictive performance intelligence."
            actionText="Log First Session"
            onAction={handleOpenAddModal}
            className="py-12 border-dashed"
          />
        )}
      </Card>

      {/* 7. Modal for Logging / Editing Study Session */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-fade-in">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl border border-slate-200 relative">
            <button
              onClick={() => setIsModalOpen(false)}
              className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
                <BookOpen className="w-4 h-4" />
              </div>
              <h3 className="text-base font-semibold text-slate-900">
                {editingActivity ? 'Edit Study Session' : 'Log Study Session'}
              </h3>
            </div>

            {formError && (
              <div className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmitForm} className="space-y-4">
              {/* Subject */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Subject / Topic
                </label>
                <div className="space-y-2">
                  <select
                    className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                    value={formSubject}
                    onChange={(e) => setFormSubject(e.target.value)}
                  >
                    {supportedSubjects.map((s) => (
                      <option key={s} value={s}>
                        {s}
                      </option>
                    ))}
                    <option value="custom">Other (Custom Subject)</option>
                  </select>
                  {formSubject === 'custom' && (
                    <input
                      type="text"
                      placeholder="Enter custom subject name"
                      className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none"
                      onChange={(e) => setFormSubject(e.target.value)}
                      required
                    />
                  )}
                </div>
              </div>

              {/* Hours Logged */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Hours Logged
                </label>
                <input
                  type="number"
                  step="0.25"
                  min="0.1"
                  max="24"
                  placeholder="e.g. 2.5"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  value={formHours}
                  onChange={(e) => setFormHours(e.target.value)}
                  required
                />
              </div>

              {/* Performance Score (Optional) */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Quiz / Test Score % (Optional)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0"
                  max="100"
                  placeholder="e.g. 85 (leave blank if unassigned)"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  value={formScore}
                  onChange={(e) => setFormScore(e.target.value)}
                />
              </div>

              {/* Date */}
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-600 mb-1.5">
                  Date
                </label>
                <input
                  type="date"
                  className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-xs focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20"
                  value={formDate}
                  onChange={(e) => setFormDate(e.target.value)}
                  required
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2.5">
                <Button
                  type="button"
                  variant="ghost"
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
                  {editingActivity ? 'Update Session' : 'Save Session'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
