import React, { useEffect, useMemo, useState } from 'react';
import {
  CalendarCheck,
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  AlertCircle,
  Plus,
  Trash2,
  Edit3,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Sparkles,
  X,
} from 'lucide-react';
import { api } from '../services/api';
import type { TaskItem, TasksResponse, TaskStatus } from '../types/api';
import { Card } from '../components/ui/Card';
import { MetricCard } from '../components/ui/MetricCard';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorState } from '../components/ui/ErrorState';
import { usePreferences } from '../context/PreferencesContext';

export const TasksPlannerPage: React.FC = () => {
  const { formatDate } = usePreferences();
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    return new Date().toISOString().split('T')[0];
  });
  const [data, setData] = useState<TasksResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<'All' | TaskStatus>('All');

  // Modal / Form state
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [editingTask, setEditingTask] = useState<TaskItem | null>(null);
  const [formData, setFormData] = useState({
    activity_name: '',
    date: selectedDate,
    planned_time: '',
    actual_time: '',
    status: 'Upcoming' as TaskStatus,
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  const fetchTasks = async (dateStr: string, isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);
    try {
      const resp = await api.getTasks(dateStr);
      setData(resp);
    } catch (err: any) {
      setError(err?.message || 'Failed to load daily schedule from database.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTasks(selectedDate);
  }, [selectedDate]);

  const handlePrevDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() - 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleNextDay = () => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + 1);
    setSelectedDate(d.toISOString().split('T')[0]);
  };

  const handleToday = () => {
    const today = new Date().toISOString().split('T')[0];
    setSelectedDate(today);
  };

  // Toggle status directly from task item
  const handleToggleStatus = async (task: TaskItem) => {
    const nextStatus: TaskStatus =
      task.status === 'Completed' ? 'Upcoming' : 'Completed';
    try {
      await api.updateTaskStatus(task.schedule_id, nextStatus);
      // Fetch latest source of truth from backend
      await fetchTasks(selectedDate, true);
    } catch (err: any) {
      alert(err?.message || 'Could not update task status.');
    }
  };

  // Change specific status from dropdown
  const handleChangeStatus = async (task: TaskItem, newStatus: TaskStatus) => {
    if (task.status === newStatus) return;
    try {
      await api.updateTaskStatus(task.schedule_id, newStatus);
      await fetchTasks(selectedDate, true);
    } catch (err: any) {
      alert(err?.message || 'Could not update task status.');
    }
  };

  // Delete task
  const handleDeleteTask = async (taskId: number) => {
    if (!window.confirm('Are you sure you want to remove this scheduled activity?')) return;
    try {
      await api.deleteTask(taskId);
      await fetchTasks(selectedDate, true);
    } catch (err: any) {
      alert(err?.message || 'Could not delete task.');
    }
  };

  // Open Add modal
  const handleOpenAddModal = () => {
    setEditingTask(null);
    setFormData({
      activity_name: '',
      date: selectedDate,
      planned_time: '',
      actual_time: '',
      status: 'Upcoming',
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  // Open Edit modal
  const handleOpenEditModal = (task: TaskItem) => {
    setEditingTask(task);
    setFormData({
      activity_name: task.activity_name,
      date: task.date,
      planned_time: task.planned_time || '',
      actual_time: task.actual_time || '',
      status: task.status,
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  // Submit Add / Edit
  const handleSubmitForm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.activity_name.trim()) {
      setFormError('Activity name is required.');
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      if (editingTask) {
        await api.updateTask(editingTask.schedule_id, {
          activity_name: formData.activity_name.trim(),
          date: formData.date,
          planned_time: formData.planned_time || null,
          actual_time: formData.actual_time || null,
          status: formData.status,
        });
      } else {
        await api.createTask({
          activity_name: formData.activity_name.trim(),
          date: formData.date,
          planned_time: formData.planned_time || null,
          actual_time: formData.actual_time || null,
          status: formData.status,
        });
      }

      setIsModalOpen(false);
      // Reload current selected date
      await fetchTasks(selectedDate, true);
    } catch (err: any) {
      setFormError(err?.message || 'Failed to save scheduled activity.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredTasks = useMemo(() => {
    if (!data?.tasks) return [];
    if (statusFilter === 'All') return data.tasks;
    return data.tasks.filter((t) => t.status === statusFilter);
  }, [data?.tasks, statusFilter]);

  const formattedDate = useMemo(() => {
    try {
      const parts = selectedDate.split('-');
      const d = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]));
      const weekday = d.toLocaleDateString(undefined, { weekday: 'long' });
      return `${weekday}, ${formatDate(selectedDate)}`;
    } catch {
      return formatDate(selectedDate);
    }
  }, [selectedDate, formatDate]);

  const isToday = useMemo(() => {
    const today = new Date().toISOString().split('T')[0];
    return selectedDate === today;
  }, [selectedDate]);

  const getStatusBadgeVariant = (status: TaskStatus) => {
    switch (status) {
      case 'Completed':
        return 'success';
      case 'In Progress':
        return 'indigo';
      case 'Missed':
        return 'danger';
      case 'Upcoming':
      default:
        return 'default';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Tasks & Planner
            </h1>
            <Badge variant="indigo" size="sm">
              Live PostgreSQL
            </Badge>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Manage your daily timetable, log focus routines, and track real completion metrics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchTasks(selectedDate, true)}
            disabled={isRefreshing || isLoading}
            leftIcon={
              <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            }
          >
            {isRefreshing ? 'Refreshing...' : 'Refresh'}
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleOpenAddModal}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
          >
            Add Task
          </Button>
        </div>
      </div>

      {/* Date Navigation Bar */}
      <Card className="p-3 bg-white border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <button
            onClick={handlePrevDay}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Previous Day"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextDay}
            className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Next Day"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          {!isToday && (
            <Button variant="ghost" size="sm" onClick={handleToday} className="text-xs text-indigo-600 font-medium">
              Jump to Today
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2 font-medium text-slate-900">
          <Calendar className="w-4 h-4 text-indigo-600" />
          <span>{formattedDate}</span>
          {isToday && (
            <span className="text-[11px] font-semibold uppercase tracking-wider text-indigo-700 bg-indigo-50 border border-indigo-200/60 px-2 py-0.5 rounded-full">
              Today
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <label htmlFor="planner-date" className="text-xs text-slate-500 font-medium hidden sm:inline">
            Select Date:
          </label>
          <input
            id="planner-date"
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="text-xs px-2.5 py-1.5 border border-slate-200 rounded-lg bg-slate-50 text-slate-800 outline-none focus:border-indigo-500 focus:bg-white transition-all cursor-pointer"
          />
        </div>
      </Card>

      {/* Content Area */}
      {isLoading ? (
        <LoadingSkeleton rows={4} />
      ) : error ? (
        <ErrorState
          title="Could not load planner data"
          message={error}
          onRetry={() => fetchTasks(selectedDate)}
        />
      ) : (
        <>
          {/* KPI Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Planned Tasks"
              value={data?.summary.total_tasks ?? 0}
              icon={<CalendarCheck className="w-4 h-4 text-indigo-600" />}
              subtitle={`${data?.summary.upcoming_tasks ?? 0} upcoming activities`}
            />

            <MetricCard
              title="Completion Rate"
              value={`${data?.summary.completion_rate ?? 0}%`}
              icon={<CheckCircle2 className="w-4 h-4 text-emerald-600" />}
              subtitle={`${data?.summary.completed_tasks ?? 0} of ${data?.summary.total_tasks ?? 0} completed`}
            />

            <MetricCard
              title="Active & In Progress"
              value={data?.summary.in_progress_tasks ?? 0}
              icon={<Clock className="w-4 h-4 text-indigo-600" />}
              subtitle={`${data?.summary.missed_tasks ?? 0} missed activities`}
            />

            <MetricCard
              title="Peak Focus Time"
              value={data?.summary.peak_focus_time || 'Not enough data'}
              icon={<Sparkles className="w-4 h-4 text-purple-600" />}
              subtitle="From your logged study & focus sessions"
            />
          </div>

          {/* Main Tasks Board */}
          <Card className="p-0 overflow-hidden bg-white border-slate-200/80 shadow-xs">
            {/* Filter Tabs */}
            <div className="p-4 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50">
              <div className="flex items-center gap-1 overflow-x-auto no-scrollbar">
                {(['All', 'Upcoming', 'In Progress', 'Completed', 'Missed'] as const).map(
                  (tab) => {
                    const count =
                      tab === 'All'
                        ? data?.summary.total_tasks ?? 0
                        : tab === 'Upcoming'
                        ? data?.summary.upcoming_tasks ?? 0
                        : tab === 'In Progress'
                        ? data?.summary.in_progress_tasks ?? 0
                        : tab === 'Completed'
                        ? data?.summary.completed_tasks ?? 0
                        : data?.summary.missed_tasks ?? 0;

                    return (
                      <button
                        key={tab}
                        onClick={() => setStatusFilter(tab)}
                        className={`text-xs font-medium px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 cursor-pointer ${
                          statusFilter === tab
                            ? 'bg-white text-indigo-600 shadow-2xs border border-slate-200 font-semibold'
                            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/70'
                        }`}
                      >
                        {tab}
                        <span
                          className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                            statusFilter === tab
                              ? 'bg-indigo-50 text-indigo-700'
                              : 'bg-slate-200/60 text-slate-600'
                          }`}
                        >
                          {count}
                        </span>
                      </button>
                    );
                  }
                )}
              </div>

              <span className="text-xs text-slate-400">
                {filteredTasks.length} {filteredTasks.length === 1 ? 'task' : 'tasks'} shown
              </span>
            </div>

            {/* Task list or empty state */}
            {data?.tasks.length === 0 ? (
              <EmptyState
                icon={<CalendarCheck className="w-6 h-6 text-indigo-600" />}
                title={`No tasks scheduled for ${formattedDate}`}
                description="You haven't scheduled any tasks or activities for this date yet. Create a schedule to organize your day and build your digital twin focus profile."
                actionText="+ Schedule First Task"
                onAction={handleOpenAddModal}
                className="border-0 shadow-none py-16"
              />
            ) : filteredTasks.length === 0 ? (
              <div className="py-12 px-6 text-center text-slate-500 text-sm">
                No tasks match the selected filter <strong className="text-slate-800">"{statusFilter}"</strong>.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {filteredTasks.map((task) => (
                  <div
                    key={task.schedule_id}
                    className={`p-4 flex items-center justify-between gap-3 hover:bg-slate-50/70 transition-colors ${
                      task.status === 'Completed' ? 'bg-slate-50/40' : ''
                    }`}
                  >
                    {/* Left: Checkbox & Name */}
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <button
                        onClick={() => handleToggleStatus(task)}
                        title={task.status === 'Completed' ? 'Mark Incomplete' : 'Mark Completed'}
                        className="text-slate-400 hover:text-indigo-600 transition-colors shrink-0 cursor-pointer"
                      >
                        {task.status === 'Completed' ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                        ) : (
                          <Circle className="w-5 h-5" />
                        )}
                      </button>

                      <div className="min-w-0 flex-1">
                        <div
                          className={`text-sm font-medium truncate ${
                            task.status === 'Completed'
                              ? 'text-slate-400 line-through'
                              : 'text-slate-800'
                          }`}
                        >
                          {task.activity_name}
                        </div>

                        {/* Timing metadata */}
                        <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-400">
                          {task.planned_time ? (
                            <span className="flex items-center gap-1">
                              <Clock className="w-3 h-3 text-slate-400" />
                              Planned: <strong className="text-slate-600">{task.planned_time}</strong>
                            </span>
                          ) : (
                            <span className="italic text-slate-400">No time set</span>
                          )}

                          {task.actual_time && (
                            <span className="flex items-center gap-1 border-l border-slate-200 pl-2">
                              Actual: <strong className="text-slate-600">{task.actual_time}</strong>
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Right: Status selector & Actions */}
                    <div className="flex items-center gap-2 shrink-0">
                      <select
                        value={task.status}
                        onChange={(e) =>
                          handleChangeStatus(task, e.target.value as TaskStatus)
                        }
                        className="text-xs px-2 py-1 rounded-lg border border-slate-200 bg-white text-slate-700 outline-none focus:border-indigo-400 cursor-pointer shadow-2xs"
                      >
                        <option value="Upcoming">Upcoming</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                        <option value="Missed">Missed</option>
                      </select>

                      <Badge variant={getStatusBadgeVariant(task.status)} size="sm">
                        {task.status}
                      </Badge>

                      <button
                        onClick={() => handleOpenEditModal(task)}
                        title="Edit Activity"
                        className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => handleDeleteTask(task.schedule_id)}
                        title="Delete Activity"
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}

      {/* Add / Edit Task Modal Dialog */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 relative">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
              <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                <CalendarCheck className="w-4 h-4 text-indigo-600" />
                {editingTask ? 'Edit Scheduled Activity' : 'Add New Activity'}
              </h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {formError && (
              <div className="p-3 mb-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitForm} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Activity Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Study Mathematics, Workout, Deep Work"
                  value={formData.activity_name}
                  onChange={(e) =>
                    setFormData({ ...formData, activity_name: e.target.value })
                  }
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all text-slate-900"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Schedule Date
                </label>
                <input
                  type="date"
                  required
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all text-slate-900"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Planned Time
                  </label>
                  <input
                    type="time"
                    value={formData.planned_time}
                    onChange={(e) =>
                      setFormData({ ...formData, planned_time: e.target.value })
                    }
                    className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all text-slate-900"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Actual Time
                  </label>
                  <input
                    type="time"
                    value={formData.actual_time}
                    onChange={(e) =>
                      setFormData({ ...formData, actual_time: e.target.value })
                    }
                    className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all text-slate-900"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Status
                </label>
                <select
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      status: e.target.value as TaskStatus,
                    })
                  }
                  className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white transition-all text-slate-900"
                >
                  <option value="Upcoming">Upcoming</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Completed">Completed</option>
                  <option value="Missed">Missed</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={isSubmitting}
                >
                  {editingTask ? 'Save Changes' : 'Create Task'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
