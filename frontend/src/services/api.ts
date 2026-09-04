import type {
  ChatStatusResponse,
  ChatTurnResponse,
  CreateStudyActivityRequest,
  CreateTaskRequest,
  DashboardSummaryResponse,
  Goal,
  StudyActivity,
  StudyOverviewResponse,
  StudyPredictRequest,
  StudyPredictResponse,
  SuggestionsResponse,
  TaskItem,
  TasksResponse,
  TaskStatus,
  UpdateStudyActivityRequest,
  UpdateTaskRequest,
  User,
  CreateTransactionRequest,
  UpdateTransactionRequest,
  ExpenseClassifyRequest,
  ExpenseClassifyResponse,
  ForecastSimulateRequest,
  ForecastSimulateResponse,
  TransactionItem,
  WealthOverviewResponse,
  AnalyticsResponse,
  AnalyticsTimeRange,
  SimulationBaselineResponse,
  RunSimulationRequest,
  RunSimulationResponse,
  SaveSimulationRequest,
  SaveSimulationResponse,
  SimulationHistoryItem,
  UserProfileResponse,
  UpdateProfileRequest,
  GoalsListResponse,
  CreateGoalRequest,
  UpdateGoalRequest,
  SettingsResponse,
  UpdatePreferencesRequest,
} from '../types/api';

const API_BASE = '/api';

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('dt_auth_token');
  }

  setToken(token: string) {
    localStorage.setItem('dt_auth_token', token);
  }

  clearToken() {
    localStorage.removeItem('dt_auth_token');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      // If unauthorized, clear token so app can route to login
      this.clearToken();
      window.dispatchEvent(new Event('auth:unauthorized'));
    }

    if (!response.ok) {
      let errorMessage = `HTTP Error ${response.status}`;
      try {
        const errorBody = await response.json();
        errorMessage = errorBody.detail || errorBody.message || errorMessage;
      } catch {
        // use default status
      }
      throw new Error(errorMessage);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string): Promise<{ token: string; user: User }> {
    const data = await this.request<{ token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.token);
    return data;
  }

  async register(payload: {
    name: string;
    email: string;
    password: string;
    gender?: string;
    age?: number;
    occupation?: string;
  }): Promise<{ token: string; user: User }> {
    const data = await this.request<{ token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    this.setToken(data.token);
    return data;
  }

  async me(): Promise<{ user: User }> {
    return this.request<{ user: User }>('/auth/me');
  }

  // Dashboard
  async getDashboardSummary(): Promise<DashboardSummaryResponse> {
    return this.request<DashboardSummaryResponse>('/dashboard/summary');
  }

  // Profile
  async getProfile(): Promise<UserProfileResponse> {
    return this.request<UserProfileResponse>('/profile');
  }

  async updateProfile(data: UpdateProfileRequest): Promise<UserProfileResponse> {
    return this.request<UserProfileResponse>('/profile', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Goals
  async getGoals(): Promise<GoalsListResponse> {
    return this.request<GoalsListResponse>('/goals');
  }

  async createGoal(data: CreateGoalRequest): Promise<Goal> {
    return this.request<Goal>('/goals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateGoal(goalId: number, data: UpdateGoalRequest): Promise<Goal> {
    return this.request<Goal>(`/goals/${goalId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteGoal(goalId: number): Promise<{ message: string; goal_id: number }> {
    return this.request<{ message: string; goal_id: number }>(`/goals/${goalId}`, {
      method: 'DELETE',
    });
  }

  // Settings & Preferences
  async getSettings(): Promise<SettingsResponse> {
    return this.request<SettingsResponse>('/settings');
  }

  async updateSettings(data: UpdatePreferencesRequest): Promise<SettingsResponse> {
    return this.request<SettingsResponse>('/settings', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // AI Chat
  async getChatStatus(): Promise<ChatStatusResponse> {
    return this.request<ChatStatusResponse>('/chat/status');
  }

  async askChat(message: string): Promise<ChatTurnResponse> {
    return this.request<ChatTurnResponse>('/chat/ask', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  }

  // Tasks & Planner
  async getTasks(date?: string): Promise<TasksResponse> {
    const query = date ? `?date=${encodeURIComponent(date)}` : '';
    return this.request<TasksResponse>(`/tasks${query}`);
  }

  async createTask(data: CreateTaskRequest): Promise<TaskItem> {
    return this.request<TaskItem>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTaskStatus(
    scheduleId: number,
    status: TaskStatus
  ): Promise<{ schedule_id: number; status: TaskStatus; ok: boolean }> {
    return this.request<{ schedule_id: number; status: TaskStatus; ok: boolean }>(
      `/tasks/${scheduleId}/status`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      }
    );
  }

  async updateTask(
    scheduleId: number,
    data: UpdateTaskRequest
  ): Promise<{ schedule_id: number; ok: boolean; message: string }> {
    return this.request<{ schedule_id: number; ok: boolean; message: string }>(
      `/tasks/${scheduleId}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
  }

  async deleteTask(scheduleId: number): Promise<{ ok: boolean; message: string }> {
    return this.request<{ ok: boolean; message: string }>(`/tasks/${scheduleId}`, {
      method: 'DELETE',
    });
  }

  // Study & Academic
  async getStudyOverview(): Promise<StudyOverviewResponse> {
    return this.request<StudyOverviewResponse>('/study');
  }

  async createStudyActivity(data: CreateStudyActivityRequest): Promise<StudyActivity> {
    return this.request<StudyActivity>('/study/activities', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateStudyActivity(
    activityId: number,
    data: UpdateStudyActivityRequest
  ): Promise<{ activity_id: number; ok: boolean; message: string }> {
    return this.request<{ activity_id: number; ok: boolean; message: string }>(
      `/study/activities/${activityId}`,
      {
        method: 'PUT',
        body: JSON.stringify(data),
      }
    );
  }

  async deleteStudyActivity(activityId: number): Promise<{ ok: boolean; message: string }> {
    return this.request<{ ok: boolean; message: string }>(`/study/activities/${activityId}`, {
      method: 'DELETE',
    });
  }

  async predictStudyPerformance(data: StudyPredictRequest): Promise<StudyPredictResponse> {
    return this.request<StudyPredictResponse>('/study/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Suggestions & Recommendations
  async getSuggestions(): Promise<SuggestionsResponse> {
    return this.request<SuggestionsResponse>('/suggestions');
  }

  // Wealth & Finance
  async getWealthOverview(): Promise<WealthOverviewResponse> {
    return this.request<WealthOverviewResponse>('/wealth');
  }

  async createTransaction(data: CreateTransactionRequest): Promise<TransactionItem> {
    return this.request<TransactionItem>('/wealth/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateTransaction(
    recordId: number,
    data: UpdateTransactionRequest
  ): Promise<TransactionItem> {
    return this.request<TransactionItem>(`/wealth/transactions/${recordId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteTransaction(recordId: number): Promise<{ message: string; record_id: number }> {
    return this.request<{ message: string; record_id: number }>(`/wealth/transactions/${recordId}`, {
      method: 'DELETE',
    });
  }

  async classifyExpense(data: ExpenseClassifyRequest): Promise<ExpenseClassifyResponse> {
    return this.request<ExpenseClassifyResponse>('/wealth/classify', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async simulateSavingsForecast(
    data: ForecastSimulateRequest
  ): Promise<ForecastSimulateResponse> {
    return this.request<ForecastSimulateResponse>('/wealth/forecast', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Analytics
  async getAnalytics(range: AnalyticsTimeRange = '30D'): Promise<AnalyticsResponse> {
    return this.request<AnalyticsResponse>(`/analytics?range=${range}`);
  }

  // What-If Simulation
  async getSimulationBaseline(): Promise<SimulationBaselineResponse> {
    return this.request<SimulationBaselineResponse>('/simulation/baseline');
  }

  async runSimulation(data: RunSimulationRequest): Promise<RunSimulationResponse> {
    return this.request<RunSimulationResponse>('/simulation/run', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async saveSimulation(data: SaveSimulationRequest): Promise<SaveSimulationResponse> {
    return this.request<SaveSimulationResponse>('/simulation/save', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getSimulationHistory(domain?: string): Promise<SimulationHistoryItem[]> {
    const query = domain ? `?domain=${encodeURIComponent(domain)}` : '';
    return this.request<SimulationHistoryItem[]>(`/simulation/history${query}`);
  }
}

export const api = new ApiService();
