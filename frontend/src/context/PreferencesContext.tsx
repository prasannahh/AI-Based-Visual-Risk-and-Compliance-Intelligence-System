import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import { api } from '../services/api';
import type { UpdatePreferencesRequest } from '../types/api';
import {
  formatCurrency as formatCurrencyUtil,
  formatCompactCurrency as formatCompactCurrencyUtil,
  formatDate as formatDateUtil,
  CURRENCY_SYMBOLS,
  type CurrencyCode,
  type DateFormat,
} from '../utils/formatters';

interface PreferencesContextType {
  theme: 'light' | 'dark' | 'system';
  resolvedTheme: 'light' | 'dark';
  currency: CurrencyCode;
  currencySymbol: string;
  dateFormat: DateFormat;
  timezone: string;
  aiSuggestions: boolean;
  weeklyDigest: boolean;
  isLoading: boolean;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  updatePreferences: (updates: Partial<UpdatePreferencesRequest>) => Promise<void>;
  formatCurrency: (val: number | string | null | undefined, overrideCurrency?: CurrencyCode) => string;
  formatCompactCurrency: (val: number | null | undefined, overrideCurrency?: CurrencyCode) => string;
  formatDate: (date: string | number | Date | null | undefined, overrideFormat?: DateFormat) => string;
}

const PreferencesContext = createContext<PreferencesContextType | undefined>(undefined);

// Storage keys
const STORAGE_THEME = 'dt_pref_theme';
const STORAGE_CURRENCY = 'dt_pref_currency';
const STORAGE_DATE_FORMAT = 'dt_pref_date_format';
const STORAGE_TIMEZONE = 'dt_pref_timezone';
const STORAGE_AI_SUGGESTIONS = 'dt_pref_ai_suggestions';
const STORAGE_WEEKLY_DIGEST = 'dt_pref_weekly_digest';

export const PreferencesProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Synchronous cache read for instant flash-free rendering
  const [theme, setThemeState] = useState<'light' | 'dark' | 'system'>(() => {
    const cached = localStorage.getItem(STORAGE_THEME);
    if (cached === 'light' || cached === 'dark' || cached === 'system') return cached;
    return 'light';
  });

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  const [currency, setCurrencyState] = useState<CurrencyCode>(() => {
    const cached = localStorage.getItem(STORAGE_CURRENCY);
    if (cached === 'INR' || cached === 'USD' || cached === 'EUR' || cached === 'GBP') return cached;
    return 'INR';
  });

  const [dateFormat, setDateFormatState] = useState<DateFormat>(() => {
    const cached = localStorage.getItem(STORAGE_DATE_FORMAT);
    if (cached === 'YYYY-MM-DD' || cached === 'DD/MM/YYYY' || cached === 'MM/DD/YYYY') return cached;
    return 'YYYY-MM-DD';
  });

  const [timezone, setTimezoneState] = useState<string>(() => {
    return localStorage.getItem(STORAGE_TIMEZONE) || 'Asia/Kolkata';
  });

  const [aiSuggestions, setAiSuggestionsState] = useState<boolean>(() => {
    const cached = localStorage.getItem(STORAGE_AI_SUGGESTIONS);
    return cached !== 'false';
  });

  const [weeklyDigest, setWeeklyDigestState] = useState<boolean>(() => {
    const cached = localStorage.getItem(STORAGE_WEEKLY_DIGEST);
    return cached === 'true';
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Apply Theme effect
  useEffect(() => {
    const root = document.documentElement;

    const applyResolved = (isDark: boolean) => {
      if (isDark) {
        root.classList.add('dark');
        root.style.colorScheme = 'dark';
        setResolvedTheme('dark');
      } else {
        root.classList.remove('dark');
        root.style.colorScheme = 'light';
        setResolvedTheme('light');
      }
    };

    if (theme === 'dark') {
      applyResolved(true);
    } else if (theme === 'light') {
      applyResolved(false);
    } else {
      // System mode: check system preferences and listen for changes
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      applyResolved(mediaQuery.matches);

      const handler = (e: MediaQueryListEvent) => {
        applyResolved(e.matches);
      };

      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    }
  }, [theme]);

  // Sync preferences from backend on authentication / startup
  useEffect(() => {
    let isMounted = true;

    async function loadBackendPreferences() {
      const token = localStorage.getItem('dt_auth_token');
      if (!token) return;

      try {
        setIsLoading(true);
        const data = await api.getSettings();
        if (!isMounted) return;

        const p = data.preferences;
        if (p.theme && (p.theme === 'light' || p.theme === 'dark' || p.theme === 'system')) {
          setThemeState(p.theme);
          localStorage.setItem(STORAGE_THEME, p.theme);
        }
        if (p.currency && (p.currency === 'INR' || p.currency === 'USD' || p.currency === 'EUR' || p.currency === 'GBP')) {
          setCurrencyState(p.currency);
          localStorage.setItem(STORAGE_CURRENCY, p.currency);
        }
        if (p.date_format && (p.date_format === 'YYYY-MM-DD' || p.date_format === 'DD/MM/YYYY' || p.date_format === 'MM/DD/YYYY')) {
          setDateFormatState(p.date_format);
          localStorage.setItem(STORAGE_DATE_FORMAT, p.date_format);
        }
        if (p.timezone) {
          setTimezoneState(p.timezone);
          localStorage.setItem(STORAGE_TIMEZONE, p.timezone);
        }
        setAiSuggestionsState(p.ai_suggestions_enabled);
        localStorage.setItem(STORAGE_AI_SUGGESTIONS, String(p.ai_suggestions_enabled));

        setWeeklyDigestState(p.weekly_digest_enabled);
        localStorage.setItem(STORAGE_WEEKLY_DIGEST, String(p.weekly_digest_enabled));
      } catch (err) {
        console.warn('PreferencesContext: using local preferences cache', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    loadBackendPreferences();

    return () => {
      isMounted = false;
    };
  }, []);

  const setTheme = useCallback((newTheme: 'light' | 'dark' | 'system') => {
    setThemeState(newTheme);
    localStorage.setItem(STORAGE_THEME, newTheme);
  }, []);

  const updatePreferences = useCallback(
    async (updates: Partial<UpdatePreferencesRequest>) => {
      // 1. Instantly update local state and localStorage for immediate visual reactivity
      if (updates.theme !== undefined) {
        setThemeState(updates.theme);
        localStorage.setItem(STORAGE_THEME, updates.theme);
      }
      if (updates.currency !== undefined) {
        setCurrencyState(updates.currency);
        localStorage.setItem(STORAGE_CURRENCY, updates.currency);
      }
      if (updates.date_format !== undefined) {
        setDateFormatState(updates.date_format);
        localStorage.setItem(STORAGE_DATE_FORMAT, updates.date_format);
      }
      if (updates.timezone !== undefined) {
        setTimezoneState(updates.timezone);
        localStorage.setItem(STORAGE_TIMEZONE, updates.timezone);
      }
      if (updates.ai_suggestions_enabled !== undefined) {
        setAiSuggestionsState(updates.ai_suggestions_enabled);
        localStorage.setItem(STORAGE_AI_SUGGESTIONS, String(updates.ai_suggestions_enabled));
      }
      if (updates.weekly_digest_enabled !== undefined) {
        setWeeklyDigestState(updates.weekly_digest_enabled);
        localStorage.setItem(STORAGE_WEEKLY_DIGEST, String(updates.weekly_digest_enabled));
      }

      // 2. Persist to backend if token exists
      const token = localStorage.getItem('dt_auth_token');
      if (token) {
        await api.updateSettings(updates);
      }
    },
    []
  );

  const formatCurrency = useCallback(
    (val: number | string | null | undefined, overrideCurrency?: CurrencyCode) => {
      return formatCurrencyUtil(val, overrideCurrency || currency);
    },
    [currency]
  );

  const formatCompactCurrency = useCallback(
    (val: number | null | undefined, overrideCurrency?: CurrencyCode) => {
      return formatCompactCurrencyUtil(val, overrideCurrency || currency);
    },
    [currency]
  );

  const formatDate = useCallback(
    (date: string | number | Date | null | undefined, overrideFormat?: DateFormat) => {
      return formatDateUtil(date, overrideFormat || dateFormat);
    },
    [dateFormat]
  );

  const currencySymbol = useMemo(() => CURRENCY_SYMBOLS[currency] || '₹', [currency]);

  return (
    <PreferencesContext.Provider
      value={{
        theme,
        resolvedTheme,
        currency,
        currencySymbol,
        dateFormat,
        timezone,
        aiSuggestions,
        weeklyDigest,
        isLoading,
        setTheme,
        updatePreferences,
        formatCurrency,
        formatCompactCurrency,
        formatDate,
      }}
    >
      {children}
    </PreferencesContext.Provider>
  );
};

export const usePreferences = (): PreferencesContextType => {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
};
