import React, { useState } from 'react';
import { Dna, Lock, Mail, User, Briefcase, Calendar } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

export const LoginPage: React.FC = () => {
  const { login, register } = useAuth();
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Login form state
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register form state
  const [regName, setRegName] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regGender, setRegGender] = useState('Male');
  const [regAge, setRegAge] = useState<number>(25);
  const [regOccupation, setRegOccupation] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginEmail || !loginPassword) {
      setError('Please fill in both email and password.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await login(loginEmail, loginPassword);
    } catch (err: any) {
      setError(err?.message || 'Login failed. Check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regName || !regEmail || !regPassword) {
      setError('Name, email and password are required.');
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      await register({
        name: regName,
        email: regEmail,
        password: regPassword,
        gender: regGender,
        age: Number(regAge),
        occupation: regOccupation,
      });
    } catch (err: any) {
      setError(err?.message || 'Registration failed.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center items-center px-4 py-12">
      {/* Brand Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-indigo-600 text-white mb-3 shadow-md shadow-indigo-200">
          <Dna className="w-6 h-6" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Digital Twin AI
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Personal Life Simulation & Decision Intelligence System
        </p>
      </div>

      <Card className="w-full max-w-md p-8 shadow-sm border-slate-200">
        {/* Tab Switcher */}
        <div className="flex bg-slate-100 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => {
              setTab('login');
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              tab === 'login'
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Sign In
          </button>
          <button
            type="button"
            onClick={() => {
              setTab('register');
              setError(null);
            }}
            className={`flex-1 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              tab === 'register'
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Create Twin
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-xl leading-relaxed">
            {error}
          </div>
        )}

        {tab === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full pl-10 pr-3.5 py-2.5 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full mt-2"
              isLoading={isLoading}
            >
              Sign In to Your Twin
            </Button>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={regName}
                  onChange={(e) => setRegName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  placeholder="jane@example.com"
                  className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Gender
                </label>
                <select
                  value={regGender}
                  onChange={(e) => setRegGender(e.target.value)}
                  className="w-full px-3 py-2 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Age
                </label>
                <div className="relative">
                  <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                  <input
                    type="number"
                    min={10}
                    max={100}
                    value={regAge}
                    onChange={(e) => setRegAge(Number(e.target.value))}
                    className="w-full pl-9 pr-3 py-2 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                  />
                </div>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Occupation
              </label>
              <div className="relative">
                <Briefcase className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  value={regOccupation}
                  onChange={(e) => setRegOccupation(e.target.value)}
                  placeholder="e.g. Software Engineer / Student"
                  className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  className="w-full pl-10 pr-3.5 py-2 text-sm bg-slate-50/70 border border-slate-200 rounded-xl outline-none focus:border-indigo-500 focus:bg-white text-slate-900"
                  required
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full mt-2"
              isLoading={isLoading}
            >
              Create My Digital Twin
            </Button>
          </form>
        )}
      </Card>
    </div>
  );
};
