import React, { useEffect, useMemo, useState } from 'react';
import {
  Target,
  Calendar,
  Edit3,
  Trash2,
  Plus,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Check,
  X,
  Sparkles,
  HeartPulse,
  Briefcase,
  AlertTriangle,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  UserProfileResponse,
  UpdateProfileRequest,
  Goal,
  CreateGoalRequest,
  UpdateGoalRequest,
} from '../types/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { MetricCard } from '../components/ui/MetricCard';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { EmptyState } from '../components/ui/EmptyState';
import { usePreferences } from '../context/PreferencesContext';

export const ProfilePage: React.FC = () => {
  const { formatCurrency, formatDate } = usePreferences();
  // Profile state
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [loadingProfile, setLoadingProfile] = useState<boolean>(true);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Edit profile state
  const [editingProfile, setEditingProfile] = useState<boolean>(false);
  const [editName, setEditName] = useState<string>('');
  const [editOccupation, setEditOccupation] = useState<string>('');
  const [editGender, setEditGender] = useState<'Male' | 'Female'>('Male');
  const [editAge, setEditAge] = useState<string>('25');
  const [savingProfile, setSavingProfile] = useState<boolean>(false);
  const [profileSuccessMsg, setProfileSuccessMsg] = useState<string | null>(null);

  // Goals state
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loadingGoals, setLoadingGoals] = useState<boolean>(true);
  const [goalFilter, setGoalFilter] = useState<'all' | 'active' | 'completed'>('all');

  // Add goal modal / form state
  const [isAddGoalOpen, setIsAddGoalOpen] = useState<boolean>(false);
  const [newGoalName, setNewGoalName] = useState<string>('');
  const [newTargetAmount, setNewTargetAmount] = useState<string>('10000');
  const [newCurrentProgress, setNewCurrentProgress] = useState<string>('0');
  const [newTargetDate, setNewTargetDate] = useState<string>('');
  const [savingGoal, setSavingGoal] = useState<boolean>(false);
  const [goalError, setGoalError] = useState<string | null>(null);

  // Edit goal modal state
  const [editingGoal, setEditingGoal] = useState<Goal | null>(null);
  const [editGoalName, setEditGoalName] = useState<string>('');
  const [editTargetAmount, setEditTargetAmount] = useState<string>('');
  const [editCurrentProgress, setEditCurrentProgress] = useState<string>('');
  const [editTargetDate, setEditTargetDate] = useState<string>('');
  const [updatingGoal, setUpdatingGoal] = useState<boolean>(false);

  // Delete confirmation state
  const [deletingGoalId, setDeletingGoalId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Quick progress update inline
  const [quickProgressGoalId, setQuickProgressGoalId] = useState<number | null>(null);
  const [quickProgressVal, setQuickProgressVal] = useState<string>('');
  const [savingQuickProgress, setSavingQuickProgress] = useState<boolean>(false);

  // Fetch profile
  const fetchProfile = async () => {
    try {
      setLoadingProfile(true);
      setProfileError(null);
      const res = await api.getProfile();
      setProfile(res);
      setEditName(res.name || '');
      setEditOccupation(res.occupation || '');
      setEditGender((res.gender as 'Male' | 'Female') || 'Male');
      setEditAge(res.age ? String(res.age) : '25');
    } catch (err: any) {
      setProfileError(err.message || 'Failed to load user profile.');
    } finally {
      setLoadingProfile(false);
    }
  };

  // Fetch goals
  const fetchGoals = async () => {
    try {
      setLoadingGoals(true);
      const res = await api.getGoals();
      setGoals(res.goals || []);
    } catch (err: any) {
      console.error('Failed to load goals', err);
    } finally {
      setLoadingGoals(false);
    }
  };

  useEffect(() => {
    fetchProfile();
    fetchGoals();
  }, []);

  // Handle profile update
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editName.trim()) {
      alert('Please enter your full name.');
      return;
    }
    try {
      setSavingProfile(true);
      setProfileSuccessMsg(null);
      const payload: UpdateProfileRequest = {
        name: editName.trim(),
        occupation: editOccupation.trim(),
        gender: editGender,
        age: editAge ? parseInt(editAge, 10) : undefined,
      };
      const updated = await api.updateProfile(payload);
      setProfile(updated);
      setEditingProfile(false);
      setProfileSuccessMsg('Profile information updated successfully.');
      setTimeout(() => setProfileSuccessMsg(null), 4000);
    } catch (err: any) {
      alert(`Could not update profile: ${err.message || 'Unknown error'}`);
    } finally {
      setSavingProfile(false);
    }
  };

  // Handle create goal
  const handleCreateGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newGoalName.trim()) {
      setGoalError('Goal title is required.');
      return;
    }
    const target = parseFloat(newTargetAmount);
    if (isNaN(target) || target <= 0) {
      setGoalError('Target amount must be greater than zero.');
      return;
    }
    const progress = parseFloat(newCurrentProgress) || 0;
    if (progress < 0) {
      setGoalError('Current progress cannot be negative.');
      return;
    }

    try {
      setSavingGoal(true);
      setGoalError(null);
      const payload: CreateGoalRequest = {
        goal_name: newGoalName.trim(),
        target_amount: target,
        current_progress: progress,
        target_date: newTargetDate || undefined,
      };
      await api.createGoal(payload);
      setIsAddGoalOpen(false);
      setNewGoalName('');
      setNewTargetAmount('10000');
      setNewCurrentProgress('0');
      setNewTargetDate('');
      fetchGoals();
      fetchProfile();
    } catch (err: any) {
      setGoalError(err.message || 'Failed to create goal.');
    } finally {
      setSavingGoal(false);
    }
  };

  // Open edit goal modal
  const handleStartEditGoal = (g: Goal) => {
    setEditingGoal(g);
    setEditGoalName(g.goal_name);
    setEditTargetAmount(String(g.target_amount));
    setEditCurrentProgress(String(g.current_progress));
    setEditTargetDate(g.target_date || '');
  };

  // Handle save edit goal
  const handleSaveEditGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingGoal) return;
    const target = parseFloat(editTargetAmount);
    if (isNaN(target) || target <= 0) {
      alert('Target amount must be greater than zero.');
      return;
    }
    const progress = parseFloat(editCurrentProgress) || 0;
    if (progress < 0) {
      alert('Current progress cannot be negative.');
      return;
    }

    try {
      setUpdatingGoal(true);
      const payload: UpdateGoalRequest = {
        goal_name: editGoalName.trim(),
        target_amount: target,
        current_progress: progress,
        target_date: editTargetDate || undefined,
      };
      await api.updateGoal(editingGoal.goal_id, payload);
      setEditingGoal(null);
      fetchGoals();
      fetchProfile();
    } catch (err: any) {
      alert(`Could not update goal: ${err.message || 'Unknown error'}`);
    } finally {
      setUpdatingGoal(false);
    }
  };

  // Handle quick progress save
  const handleQuickProgressSave = async (goalId: number) => {
    const val = parseFloat(quickProgressVal);
    if (isNaN(val) || val < 0) {
      alert('Please enter a valid non-negative progress value.');
      return;
    }
    try {
      setSavingQuickProgress(true);
      await api.updateGoal(goalId, { current_progress: val });
      setQuickProgressGoalId(null);
      fetchGoals();
      fetchProfile();
    } catch (err: any) {
      alert(`Could not update progress: ${err.message || 'Unknown error'}`);
    } finally {
      setSavingQuickProgress(false);
    }
  };

  // Handle delete goal
  const handleConfirmDelete = async () => {
    if (!deletingGoalId) return;
    try {
      setIsDeleting(true);
      await api.deleteGoal(deletingGoalId);
      setDeletingGoalId(null);
      fetchGoals();
      fetchProfile();
    } catch (err: any) {
      alert(`Could not delete goal: ${err.message || 'Unknown error'}`);
    } finally {
      setIsDeleting(false);
    }
  };

  // Filtered goals
  const filteredGoals = useMemo(() => {
    if (goalFilter === 'active') {
      return goals.filter((g) => !g.is_completed);
    }
    if (goalFilter === 'completed') {
      return goals.filter((g) => g.is_completed);
    }
    return goals;
  }, [goals, goalFilter]);

  // Compute initials for avatar
  const initials = useMemo(() => {
    if (!profile?.name) return 'U';
    const parts = profile.name.trim().split(/\s+/);
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }, [profile?.name]);

  if (loadingProfile && !profile) {
    return <LoadingSkeleton rows={4} />;
  }

  if (profileError && !profile) {
    return (
      <ErrorState
        title="Failed to Load Profile"
        message={profileError}
        onRetry={fetchProfile}
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
              Profile &amp; Goals
            </h1>
            <Badge variant="indigo" size="sm" showDot>
              Account Center
            </Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Manage your personal information, calibrated Twin vitals, and target milestones.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              fetchProfile();
              fetchGoals();
            }}
            disabled={loadingProfile || loadingGoals}
            className="flex items-center gap-1.5"
          >
            <RotateCcw
              className={`w-3.5 h-3.5 text-slate-500 ${
                loadingProfile || loadingGoals ? 'animate-spin' : ''
              }`}
            />
            <span>Refresh</span>
          </Button>
        </div>
      </div>

      {profileSuccessMsg && (
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 animate-fadeIn">
          <Check className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{profileSuccessMsg}</span>
        </div>
      )}

      {/* ----------------- Profile Identity & Twin Overview ----------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: User Identity Card */}
        <Card className="p-6 border-slate-200/80 bg-white flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-800 text-white flex items-center justify-center font-bold text-xl shadow-xs">
                {initials}
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900 leading-tight">
                  {profile?.name || 'User'}
                </h2>
                <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                  <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                  {profile?.occupation || 'Digital Twin Member'}
                </p>
                <p className="text-xs text-slate-400 mt-0.5">{profile?.email}</p>
              </div>
            </div>

            <div className="space-y-2 pt-3 border-t border-slate-100 text-xs text-slate-600">
              <div className="flex justify-between">
                <span className="text-slate-500">Gender</span>
                <span className="font-semibold text-slate-800">{profile?.gender || '—'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Age</span>
                <span className="font-semibold text-slate-800">
                  {profile?.age ? `${profile.age} yrs` : '—'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Registered</span>
                <span className="font-semibold text-slate-800">
                  {profile?.created_at
                    ? formatDate(profile.created_at)
                    : 'Active'}
                </span>
              </div>
            </div>
          </div>

          <div className="mt-5 pt-3 border-t border-slate-100">
            <Button
              variant={editingProfile ? 'secondary' : 'primary'}
              size="sm"
              onClick={() => setEditingProfile(!editingProfile)}
              className="w-full flex items-center justify-center gap-1.5"
            >
              {editingProfile ? (
                <>
                  <X className="w-3.5 h-3.5" />
                  <span>Cancel Edit</span>
                </>
              ) : (
                <>
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>Edit Profile</span>
                </>
              )}
            </Button>
          </div>
        </Card>

        {/* Right: Digital Twin Vitals & Metrics */}
        <div className="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <MetricCard
            title="Days Active"
            value={profile?.days_active ?? 0}
            subtitle="Calendar days logged"
            icon={<Calendar className="w-4 h-4 text-indigo-600" />}
          />
          <MetricCard
            title="Active Goals"
            value={profile?.active_goals_count ?? 0}
            subtitle="Current target targets"
            icon={<Target className="w-4 h-4 text-amber-600" />}
          />
          <MetricCard
            title="Completed Goals"
            value={profile?.completed_goals_count ?? 0}
            subtitle="Achieved milestones"
            icon={<CheckCircle2 className="w-4 h-4 text-emerald-600" />}
          />
          <MetricCard
            title="Avg Goal Progress"
            value={`${profile?.avg_goal_progress?.toFixed(0) ?? 0}%`}
            subtitle="Overall pace completion"
            icon={<Sparkles className="w-4 h-4 text-purple-600" />}
            progressValue={profile?.avg_goal_progress ?? 0}
            progressColor="bg-purple-600"
          />

          {profile?.latest_health && (
            <Card className="col-span-2 sm:col-span-4 p-4 border-slate-200/80 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                  <HeartPulse className="w-5 h-5" />
                </div>
                <div>
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Latest Health Calibration
                  </span>
                  <div className="text-xs text-slate-700 font-medium mt-0.5">
                    Height: {profile.latest_health.height_cm || '—'} cm · Weight:{' '}
                    {profile.latest_health.weight_kg || '—'} kg
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">BMI:</span>
                <span className="text-sm font-bold text-slate-800">
                  {profile.latest_health.bmi || '—'}
                </span>
                {profile.latest_health.bmi_category && (
                  <Badge variant="default" size="sm">
                    {profile.latest_health.bmi_category}
                  </Badge>
                )}
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* ----------------- Edit Profile Form (Conditional) ----------------- */}
      {editingProfile && (
        <Card className="p-6 border-indigo-200/80 bg-indigo-50/30 shadow-xs animate-fadeIn">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-indigo-100">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Edit3 className="w-4 h-4 text-indigo-600" />
              Update Personal Information
            </h3>
            <span className="text-xs text-slate-500">Email is fixed to Account Identity</span>
          </div>

          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Full Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  required
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Occupation / Role</label>
                <input
                  type="text"
                  value={editOccupation}
                  onChange={(e) => setEditOccupation(e.target.value)}
                  placeholder="e.g. Software Engineer, Student, Analyst"
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Gender</label>
                <select
                  value={editGender}
                  onChange={(e) => setEditGender(e.target.value as 'Male' | 'Female')}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">Age</label>
                <input
                  type="number"
                  min={10}
                  max={120}
                  value={editAge}
                  onChange={(e) => setEditAge(e.target.value)}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-indigo-100">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setEditingProfile(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" size="sm" disabled={savingProfile}>
                {savingProfile ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      {/* ----------------- Goals Header & Actions ----------------- */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200/80 pb-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-600" />
              Digital Twin Goals
            </h2>
            <p className="text-xs text-slate-500">
              Milestones actively integrated with your Dashboard, Simulations, and Recommendations.
            </p>
          </div>

          <div className="flex items-center gap-2">
            {/* Filter tabs */}
            <div className="flex items-center bg-slate-100 p-1 rounded-lg">
              <button
                type="button"
                onClick={() => setGoalFilter('all')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  goalFilter === 'all'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All ({goals.length})
              </button>
              <button
                type="button"
                onClick={() => setGoalFilter('active')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  goalFilter === 'active'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Active ({goals.filter((g) => !g.is_completed).length})
              </button>
              <button
                type="button"
                onClick={() => setGoalFilter('completed')}
                className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                  goalFilter === 'completed'
                    ? 'bg-white text-slate-900 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Completed ({goals.filter((g) => g.is_completed).length})
              </button>
            </div>

            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setIsAddGoalOpen(true);
                setGoalError(null);
              }}
              className="flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4 text-white" />
              <span>Add Goal</span>
            </Button>
          </div>
        </div>

        {/* Add Goal Form / Modal */}
        {isAddGoalOpen && (
          <Card className="p-5 border-indigo-200 bg-white shadow-md animate-fadeIn">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Target className="w-4 h-4 text-indigo-600" />
                Define a New Target Goal
              </h3>
              <button
                type="button"
                onClick={() => setIsAddGoalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {goalError && (
              <div className="mb-4 p-2.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{goalError}</span>
              </div>
            )}

            <form onSubmit={handleCreateGoal} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-1 sm:col-span-2">
                  <label className="text-xs font-semibold text-slate-700">Goal Title</label>
                  <input
                    type="text"
                    value={newGoalName}
                    onChange={(e) => setNewGoalName(e.target.value)}
                    placeholder="e.g., Emergency Reserve Fund, Complete AWS Certification"
                    className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Target Amount</label>
                  <input
                    type="number"
                    min={1}
                    step={100}
                    value={newTargetAmount}
                    onChange={(e) => setNewTargetAmount(e.target.value)}
                    placeholder="e.g. 50000"
                    className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Current Progress</label>
                  <input
                    type="number"
                    min={0}
                    step={100}
                    value={newCurrentProgress}
                    onChange={(e) => setNewCurrentProgress(e.target.value)}
                    placeholder="e.g. 10000"
                    className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="space-y-1 sm:col-span-2">
                  <label className="text-xs font-semibold text-slate-700">
                    Target Completion Date (Optional)
                  </label>
                  <input
                    type="date"
                    value={newTargetDate}
                    onChange={(e) => setNewTargetDate(e.target.value)}
                    className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsAddGoalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" variant="primary" size="sm" disabled={savingGoal}>
                  {savingGoal ? 'Creating...' : 'Create Goal'}
                </Button>
              </div>
            </form>
          </Card>
        )}

        {/* Edit Goal Modal */}
        {editingGoal && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <Card className="w-full max-w-md p-6 bg-white shadow-xl animate-fadeIn">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Edit3 className="w-4 h-4 text-indigo-600" />
                  Edit Goal: {editingGoal.goal_name}
                </h3>
                <button
                  type="button"
                  onClick={() => setEditingGoal(null)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleSaveEditGoal} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Goal Title</label>
                  <input
                    type="text"
                    value={editGoalName}
                    onChange={(e) => setEditGoalName(e.target.value)}
                    className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                    required
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700">Target Amount</label>
                    <input
                      type="number"
                      min={1}
                      step={100}
                      value={editTargetAmount}
                      onChange={(e) => setEditTargetAmount(e.target.value)}
                      className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                      required
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700">Current Progress</label>
                    <input
                      type="number"
                      min={0}
                      step={100}
                      value={editCurrentProgress}
                      onChange={(e) => setEditCurrentProgress(e.target.value)}
                      className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-700">Target Date</label>
                  <input
                    type="date"
                    value={editTargetDate}
                    onChange={(e) => setEditTargetDate(e.target.value)}
                    className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-300 rounded-lg text-slate-900 focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() => setEditingGoal(null)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" size="sm" disabled={updatingGoal}>
                    {updatingGoal ? 'Saving...' : 'Save Changes'}
                  </Button>
                </div>
              </form>
            </Card>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {deletingGoalId && (
          <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
            <Card className="w-full max-w-sm p-6 bg-white shadow-xl animate-fadeIn space-y-4">
              <div className="flex items-center gap-3 text-rose-600">
                <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Delete Goal?</h3>
                  <p className="text-xs text-slate-500">
                    This will permanently remove this goal from your Digital Twin. This action
                    cannot be undone.
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setDeletingGoalId(null)}
                  disabled={isDeleting}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={handleConfirmDelete}
                  disabled={isDeleting}
                >
                  {isDeleting ? 'Deleting...' : 'Delete Goal'}
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* ----------------- Goals List ----------------- */}
        {loadingGoals ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <LoadingSkeleton rows={2} />
            <LoadingSkeleton rows={2} />
          </div>
        ) : filteredGoals.length === 0 ? (
          <EmptyState
            icon={<Target className="w-6 h-6 text-slate-400" />}
            title={
              goalFilter === 'all'
                ? 'No Goals Established Yet'
                : goalFilter === 'active'
                ? 'No Active Goals'
                : 'No Completed Goals Yet'
            }
            description={
              goalFilter === 'all'
                ? 'Define your financial, academic, or lifestyle goals to unlock cross-domain pacing and intelligent scenario simulation.'
                : 'You have zero goals in this category.'
            }
            actionText={goalFilter === 'all' ? 'Create Your First Goal' : undefined}
            onAction={goalFilter === 'all' ? () => setIsAddGoalOpen(true) : undefined}
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredGoals.map((g) => {
              const pct = g.progress_pct;
              const isOverdue = g.status === 'overdue';
              const isCompleted = g.is_completed;

              return (
                <Card
                  key={g.goal_id}
                  className={`p-5 flex flex-col justify-between transition-all bg-white ${
                    isCompleted
                      ? 'border-emerald-200/80 bg-emerald-50/10'
                      : isOverdue
                      ? 'border-rose-200/80 bg-rose-50/10'
                      : 'border-slate-200/80 shadow-xs'
                  }`}
                >
                  <div>
                    {/* Header */}
                    <div className="flex items-start justify-between gap-3 mb-2">
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 leading-tight">
                          {g.goal_name}
                        </h3>
                        <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                          {g.target_date ? (
                            <span className="flex items-center gap-1">
                              <Calendar className="w-3 h-3 text-slate-400" />
                              Target: {formatDate(g.target_date)}
                            </span>
                          ) : (
                            <span>Open Horizon</span>
                          )}
                          {typeof g.days_remaining === 'number' && (
                            <span
                              className={`font-semibold ${
                                g.days_remaining < 0
                                  ? 'text-rose-600'
                                  : g.days_remaining <= 14
                                  ? 'text-amber-600'
                                  : 'text-slate-500'
                              }`}
                            >
                              ·{' '}
                              {g.days_remaining < 0
                                ? `Overdue by ${Math.abs(g.days_remaining)}d`
                                : `${g.days_remaining}d remaining`}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0">
                        {isCompleted ? (
                          <Badge variant="success" size="sm">
                            Completed
                          </Badge>
                        ) : isOverdue ? (
                          <Badge variant="danger" size="sm">
                            Overdue
                          </Badge>
                        ) : (
                          <Badge variant="indigo" size="sm">
                            Active
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mt-4 mb-2">
                      <div className="flex justify-between text-xs mb-1.5">
                        <span className="font-semibold text-slate-700">
                          {formatCurrency(g.current_progress)} / {formatCurrency(g.target_amount)}
                        </span>
                        <span className="font-bold text-indigo-700">{pct.toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${
                            isCompleted
                              ? 'bg-emerald-600'
                              : isOverdue
                              ? 'bg-rose-500'
                              : 'bg-indigo-600'
                          }`}
                          style={{ width: `${Math.min(pct, 100)}%` }}
                        />
                      </div>
                    </div>

                    {/* Quick Progress Editor */}
                    {quickProgressGoalId === g.goal_id && (
                      <div className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-200/80 animate-fadeIn">
                        <div className="flex items-center justify-between gap-2">
                          <input
                            type="number"
                            min={0}
                            value={quickProgressVal}
                            onChange={(e) => setQuickProgressVal(e.target.value)}
                            placeholder="New progress value"
                            className="w-full text-xs px-2.5 py-1.5 bg-white border border-slate-300 rounded-lg text-slate-800"
                          />
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleQuickProgressSave(g.goal_id)}
                            disabled={savingQuickProgress}
                            className="shrink-0"
                          >
                            Save
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => setQuickProgressGoalId(null)}
                            className="shrink-0"
                          >
                            <X className="w-3.5 h-3.5" />
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions footer */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <button
                      type="button"
                      onClick={() => {
                        setQuickProgressGoalId(
                          quickProgressGoalId === g.goal_id ? null : g.goal_id
                        );
                        setQuickProgressVal(String(g.current_progress));
                      }}
                      className="text-xs font-semibold text-indigo-600 hover:text-indigo-800 transition-colors"
                    >
                      Update Progress
                    </button>

                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => handleStartEditGoal(g)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all"
                        title="Edit goal details"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeletingGoalId(g.goal_id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-all"
                        title="Delete goal"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
