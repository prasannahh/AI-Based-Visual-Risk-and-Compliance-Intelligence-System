import React, { useEffect, useMemo, useState } from 'react';
import {
  Globe,
  Bell,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Save,
  Sparkles,
  Lock,
  Sun,
  Moon,
  Laptop,
} from 'lucide-react';
import { api } from '../services/api';
import type {
  SettingsResponse,
  UpdatePreferencesRequest,
} from '../types/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorState } from '../components/ui/ErrorState';
import { usePreferences } from '../context/PreferencesContext';
import type { CurrencyCode, DateFormat } from '../utils/formatters';

type SettingsTab = 'all' | 'preferences' | 'notifications' | 'ai' | 'security';

export const SettingsPage: React.FC = () => {
  const {
    setTheme: setGlobalTheme,
    updatePreferences,
  } = usePreferences();

  const [activeTab, setActiveTab] = useState<SettingsTab>('all');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Persistent settings state from backend
  const [persistedSettings, setPersistedSettings] = useState<SettingsResponse | null>(null);

  // Working preferences form state
  const [currency, setCurrency] = useState<CurrencyCode>('INR');
  const [timezone, setTimezone] = useState<string>('Asia/Kolkata');
  const [dateFormat, setDateFormat] = useState<DateFormat>('YYYY-MM-DD');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('light');
  const [weeklyDigest, setWeeklyDigest] = useState<boolean>(false);
  const [aiSuggestions, setAiSuggestions] = useState<boolean>(true);

  // Saving state & feedback
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getSettings();
      setPersistedSettings(data);
      setCurrency(data.preferences.currency);
      setTimezone(data.preferences.timezone);
      setDateFormat(data.preferences.date_format);
      setTheme(data.preferences.theme);
      setWeeklyDigest(data.preferences.weekly_digest_enabled);
      setAiSuggestions(data.preferences.ai_suggestions_enabled);
    } catch (err: any) {
      setError(err?.message || 'Failed to load application settings.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  // Detect unsaved changes
  const hasUnsavedChanges = useMemo(() => {
    if (!persistedSettings) return false;
    const p = persistedSettings.preferences;
    return (
      currency !== p.currency ||
      timezone !== p.timezone ||
      dateFormat !== p.date_format ||
      theme !== p.theme ||
      weeklyDigest !== p.weekly_digest_enabled ||
      aiSuggestions !== p.ai_suggestions_enabled
    );
  }, [persistedSettings, currency, timezone, dateFormat, theme, weeklyDigest, aiSuggestions]);

  const handleSelectTheme = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    setGlobalTheme(newTheme); // Instant live preview
  };

  const handleReset = () => {
    if (!persistedSettings) return;
    const p = persistedSettings.preferences;
    setCurrency(p.currency);
    setTimezone(p.timezone);
    setDateFormat(p.date_format);
    setTheme(p.theme);
    setGlobalTheme(p.theme); // Revert live preview
    setWeeklyDigest(p.weekly_digest_enabled);
    setAiSuggestions(p.ai_suggestions_enabled);
    setSaveError(null);
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!hasUnsavedChanges) return;

    setIsSaving(true);
    setSaveError(null);
    setSuccessMessage(null);

    const payload: UpdatePreferencesRequest = {
      currency,
      timezone,
      date_format: dateFormat,
      theme,
      weekly_digest_enabled: weeklyDigest,
      ai_suggestions_enabled: aiSuggestions,
    };

    try {
      // Updates global context (state + localStorage) AND backend API
      await updatePreferences(payload);
      const updated = await api.getSettings();
      setPersistedSettings(updated);
      setSuccessMessage('Application preferences saved and applied across the system.');
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setSaveError(err?.message || 'Failed to update preferences. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex flex-col gap-2">
          <div className="h-8 w-48 bg-slate-200 dark:bg-slate-800 rounded animate-pulse" />
          <div className="h-4 w-96 bg-slate-100 dark:bg-slate-850 rounded animate-pulse" />
        </div>
        <Card className="p-6">
          <LoadingSkeleton rows={6} />
        </Card>
      </div>
    );
  }

  if (error || !persistedSettings) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">Settings</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">Configure your Digital Twin environment</p>
          </div>
        </div>
        <ErrorState
          title="Unable to Load Settings"
          message={error || 'An unexpected error occurred while fetching your settings.'}
          onRetry={fetchSettings}
        />
      </div>
    );
  }

  const { ai_config: aiConfig, account_security: accountSec } = persistedSettings;

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">Settings & Preferences</h1>
            <Badge variant="indigo" size="sm">
              v1.0
            </Badge>
            <Badge variant="success" size="sm" showDot>
              Engine Connected
            </Badge>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Manage application defaults, localization, conversational AI parameters, and security policies.
          </p>
        </div>

        {/* Action Button Group */}
        <div className="flex items-center gap-3">
          {hasUnsavedChanges && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleReset}
              disabled={isSaving}
              className="flex items-center gap-1.5"
            >
              <RotateCcw className="w-4 h-4 text-slate-500 dark:text-slate-400" />
              Discard
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={() => handleSave()}
            disabled={!hasUnsavedChanges || isSaving}
            className="flex items-center gap-1.5 shadow-sm"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {successMessage && (
        <div className="flex items-center gap-2 p-4 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200 rounded-lg text-sm animate-in fade-in duration-200">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 flex-shrink-0" />
          <span>{successMessage}</span>
        </div>
      )}

      {saveError && (
        <div className="flex items-center gap-2 p-4 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-200 rounded-lg text-sm animate-in fade-in duration-200">
          <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400 flex-shrink-0" />
          <span>{saveError}</span>
        </div>
      )}

      {hasUnsavedChanges && !successMessage && !saveError && (
        <div className="flex items-center justify-between p-3.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 rounded-lg text-sm">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            <span className="font-medium">You have unsaved preference changes.</span>
          </div>
          <button
            onClick={() => handleSave()}
            disabled={isSaving}
            className="text-xs font-semibold text-amber-900 dark:text-amber-300 hover:text-amber-800 underline underline-offset-2 cursor-pointer"
          >
            Save now
          </button>
        </div>
      )}

      {/* Navigation Pills */}
      <div className="flex items-center gap-1 bg-slate-100/80 dark:bg-slate-800/80 p-1 rounded-xl w-fit border border-slate-200/60 dark:border-slate-700/60">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'all'
              ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-indigo-300 shadow-xs border border-slate-200/50 dark:border-slate-600'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          All Settings
        </button>
        <button
          onClick={() => setActiveTab('preferences')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'preferences'
              ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-indigo-300 shadow-xs border border-slate-200/50 dark:border-slate-600'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          Preferences
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'notifications'
              ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-indigo-300 shadow-xs border border-slate-200/50 dark:border-slate-600'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          Notifications
        </button>
        <button
          onClick={() => setActiveTab('ai')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'ai'
              ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-indigo-300 shadow-xs border border-slate-200/50 dark:border-slate-600'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          Digital Twin / AI
        </button>
        <button
          onClick={() => setActiveTab('security')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
            activeTab === 'security'
              ? 'bg-white dark:bg-slate-700 text-indigo-700 dark:text-indigo-300 shadow-xs border border-slate-200/50 dark:border-slate-600'
              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100'
          }`}
        >
          Account & Security
        </button>
      </div>

      {/* Main Settings Sections */}
      <div className="space-y-8">
        {/* SECTION 1: PREFERENCES */}
        {(activeTab === 'all' || activeTab === 'preferences') && (
          <Card className="p-6">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-slate-100 dark:border-slate-800">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <Globe className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Localization & Display</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">Configure currency representation, timezone, and date format.</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Currency Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                  Display Currency
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {[
                    { code: 'INR', symbol: '₹', label: 'Rupee' },
                    { code: 'USD', symbol: '$', label: 'Dollar' },
                    { code: 'EUR', symbol: '€', label: 'Euro' },
                    { code: 'GBP', symbol: '£', label: 'Pound' },
                  ].map((item) => (
                    <button
                      key={item.code}
                      type="button"
                      onClick={() => setCurrency(item.code as any)}
                      className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all cursor-pointer ${
                        currency === item.code
                          ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 ring-2 ring-indigo-600/20'
                          : 'border-slate-200 dark:border-slate-750 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      <span className="text-base font-bold mb-0.5">{item.symbol}</span>
                      <span className="text-xs font-semibold">{item.code}</span>
                      <span className="text-[10px] text-slate-400 dark:text-slate-500">{item.label}</span>
                    </button>
                  ))}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  Used in Wealth Planner budgets, cash flow analytics, and financial goal progress.
                </p>
              </div>

              {/* Timezone Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                  Timezone
                </label>
                <div className="relative">
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-sm text-slate-800 dark:text-slate-200 focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:border-transparent transition-all shadow-2xs"
                  >
                    <option value="Asia/Kolkata">Asia/Kolkata (IST, UTC+05:30)</option>
                    <option value="UTC">UTC (Coordinated Universal Time)</option>
                    <option value="America/New_York">America/New_York (EST / EDT)</option>
                    <option value="America/Chicago">America/Chicago (CST / CDT)</option>
                    <option value="America/Denver">America/Denver (MST / MDT)</option>
                    <option value="America/Los_Angeles">America/Los_Angeles (PST / PDT)</option>
                    <option value="Europe/London">Europe/London (GMT / BST)</option>
                    <option value="Europe/Paris">Europe/Paris (CET / CEST)</option>
                    <option value="Asia/Dubai">Asia/Dubai (GST, UTC+04:00)</option>
                    <option value="Asia/Singapore">Asia/Singapore (SGT, UTC+08:00)</option>
                    <option value="Asia/Tokyo">Asia/Tokyo (JST, UTC+09:00)</option>
                    <option value="Australia/Sydney">Australia/Sydney (AEST, UTC+10:00)</option>
                  </select>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  Determines daily schedule timetables and activity calendar boundaries.
                </p>
              </div>

              {/* Date Format */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                  Date Format
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                  {[
                    { format: 'YYYY-MM-DD', example: '2026-09-04', label: 'ISO Standard' },
                    { format: 'DD/MM/YYYY', example: '04/09/2026', label: 'UK & India' },
                    { format: 'MM/DD/YYYY', example: '09/04/2026', label: 'US Standard' },
                  ].map((item) => (
                    <button
                      key={item.format}
                      type="button"
                      onClick={() => setDateFormat(item.format as any)}
                      className={`flex flex-col items-start p-3 rounded-xl border text-left transition-all cursor-pointer ${
                        dateFormat === item.format
                          ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 ring-2 ring-indigo-600/20'
                          : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      <span className="text-xs font-bold text-slate-900 dark:text-slate-100">{item.format}</span>
                      <span className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">{item.example}</span>
                      <span className="text-[10px] text-indigo-600 dark:text-indigo-400 font-medium mt-1">{item.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Theme Preference */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
                  Appearance Theme
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'light', label: 'Light', icon: Sun, desc: 'SaaS clean' },
                    { id: 'dark', label: 'Dark', icon: Moon, desc: 'High contrast' },
                    { id: 'system', label: 'System', icon: Laptop, desc: 'Auto detect' },
                  ].map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => handleSelectTheme(item.id as any)}
                        className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition-all cursor-pointer ${
                          theme === item.id
                            ? 'border-indigo-600 bg-indigo-50/50 dark:bg-indigo-950/40 text-indigo-900 dark:text-indigo-200 ring-2 ring-indigo-600/20'
                            : 'border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-200'
                        }`}
                      >
                        <Icon className="w-4 h-4 mb-1 text-slate-600 dark:text-slate-300" />
                        <span className="text-xs font-semibold">{item.label}</span>
                        <span className="text-[10px] text-slate-400 dark:text-slate-500">{item.desc}</span>
                      </button>
                    );
                  })}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-2">
                  Optimized for comfortable reading and focused analysis across desktop and mobile.
                </p>
              </div>
            </div>
          </Card>
        )}

        {/* SECTION 2: NOTIFICATIONS */}
        {(activeTab === 'all' || activeTab === 'notifications') && (
          <Card className="p-6">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-slate-100 dark:border-slate-800">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <Bell className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Notifications & Automation</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Control automated digests and proactive life intelligence alerts.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              {/* Weekly Digest Toggle */}
              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                <div className="space-y-1 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">Weekly Twin Summary Digest</span>
                    <Badge variant={weeklyDigest ? 'success' : 'default'} size="sm">
                      {weeklyDigest ? 'Subscribed' : 'Off'}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Compile weekly productivity stats, cumulative savings changes, and study time into a summary report.
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={weeklyDigest}
                  onClick={() => setWeeklyDigest(!weeklyDigest)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
                    weeklyDigest ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      weeklyDigest ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* AI Suggestions Toggle */}
              <div className="flex items-center justify-between p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40">
                <div className="space-y-1 pr-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">Proactive Twin Suggestions</span>
                    <Badge variant={aiSuggestions ? 'indigo' : 'default'} size="sm">
                      {aiSuggestions ? 'Active' : 'Muted'}
                    </Badge>
                  </div>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Enable proactive heuristic recommendations across financial spending, habit risks, and exam preparation.
                  </p>
                </div>
                <button
                  type="button"
                  role="switch"
                  aria-checked={aiSuggestions}
                  onClick={() => setAiSuggestions(!aiSuggestions)}
                  className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-hidden focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2 ${
                    aiSuggestions ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-700'
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      aiSuggestions ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>
            </div>
          </Card>
        )}

        {/* SECTION 3: DIGITAL TWIN / AI */}
        {(activeTab === 'all' || activeTab === 'ai') && (
          <Card className="p-6">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-slate-100 dark:border-slate-800">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Digital Twin AI Engine</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Real-time runtime architecture parameters and inference model connectivity.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">AI Provider</span>
                  <Badge variant="indigo" size="sm">
                    {aiConfig.provider === 'gemini' ? 'Google Gemini' : 'Rule-Based Deterministic'}
                  </Badge>
                </div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                  {aiConfig.provider === 'gemini' ? 'Gemini Generative Intelligence' : 'Grounded Assistant'}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {aiConfig.provider === 'gemini'
                    ? 'Cloud LLM reasoning grounded with user personal data and life metrics.'
                    : 'Deterministic offline heuristic assistant.'}
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Active Model</span>
                  <Badge variant="default" size="sm">
                    {aiConfig.model}
                  </Badge>
                </div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">{aiConfig.model}</div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Low-latency model architecture tuned for grounded question answering.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">API Key Connectivity</span>
                  <Badge variant={aiConfig.has_api_key ? 'success' : 'warning'} size="sm">
                    {aiConfig.has_api_key ? 'Active & Valid' : 'Offline Mode'}
                  </Badge>
                </div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">
                  {aiConfig.has_api_key ? 'Securely Configured' : 'No Key Provided'}
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  API keys are strictly managed via environment variables and never exposed to the frontend.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Safety & Resilience</span>
                  <Badge variant="success" size="sm">
                    Zero-Failure Guard
                  </Badge>
                </div>
                <div className="text-base font-bold text-slate-900 dark:text-slate-100">Deterministic Fallback Active</div>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  If the cloud LLM is unreachable, the system automatically falls back to offline grounded heuristics.
                </p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-indigo-50/50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-800 rounded-lg flex items-center justify-between text-xs text-indigo-900 dark:text-indigo-300">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0" />
                <span>
                  Model Tuning: <strong>Temperature {aiConfig.temperature}</strong> |{' '}
                  <strong>Max Tokens {aiConfig.max_tokens}</strong>
                </span>
              </div>
              <span className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium">Deterministic Life Grounding</span>
            </div>
          </Card>
        )}

        {/* SECTION 4: ACCOUNT & SECURITY */}
        {(activeTab === 'all' || activeTab === 'security') && (
          <Card className="p-6">
            <div className="flex items-center gap-3 pb-4 mb-6 border-b border-slate-100 dark:border-slate-800">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">Account & Security Policies</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Cryptographic protection standards, session integrity, and user authentication policies.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Authenticated Account ID</span>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">User #{accountSec.user_id}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-mono">{accountSec.email}</p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Authentication Scheme</span>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{accountSec.auth_method}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Signed stateless bearer token with HMAC-SHA256 signature verification.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Credential Encryption</span>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{accountSec.password_encryption}</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Passwords salted and stretched using PBKDF2 with 100,000 hashing rounds.
                </p>
              </div>

              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 space-y-1">
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">Session Longevity</span>
                <p className="text-sm font-bold text-slate-900 dark:text-slate-100">{accountSec.session_duration_hours} Hours Expiry</p>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Active sessions automatically expire after {accountSec.session_duration_hours} hours of inactivity.
                </p>
              </div>
            </div>

            <div className="mt-4 p-3.5 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800/80 flex items-start gap-3">
              <Lock className="w-4 h-4 text-slate-400 dark:text-slate-500 mt-0.5 flex-shrink-0" />
              <div className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                <strong className="text-slate-800 dark:text-slate-200">Security Note:</strong> Password hashes, database credentials, and
                JWT secrets are never exposed to client applications. Personal profile identity (name, age, occupation)
                is managed under{' '}
                <a href="/profile" className="text-indigo-600 dark:text-indigo-400 hover:underline font-medium">
                  Profile & Goals
                </a>
                .
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};
