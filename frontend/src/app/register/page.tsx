'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Mail, KeyRound, AlertTriangle, CheckCircle, ArrowRight } from 'lucide-react';

export default function RegisterPage() {
  const { register } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<boolean>(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password || !confirmPassword) {
      setError('Please fill in all fields.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setLoading(true);

    try {
      await register(email, password);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Email might already exist.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center font-sans selection:bg-indigo-500 selection:text-white px-4">
        <div className="w-full max-w-md bg-neutral-900/40 border border-neutral-800/80 rounded-3xl p-8 md:p-10 backdrop-blur-md shadow-2xl text-center">
          <div className="h-14 w-14 rounded-full bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 mx-auto mb-6">
            <CheckCircle size={28} />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-2">Account Created!</h1>
          <p className="text-neutral-400 text-sm mb-6 leading-relaxed">
            Onboarding mail dispatched. Since we are running in development mode, please open the SMTP mail trap mock system to verify the email and activate the account.
          </p>

          <div className="bg-neutral-950/60 border border-neutral-800/80 rounded-2xl p-5 mb-8 text-left">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 mb-1.5">Action Required</h4>
            <p className="text-neutral-300 text-xs leading-relaxed mb-3">
              Click the verification link in the received activation mail to complete authentication.
            </p>
            <a
              href="http://localhost:8025"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1.5 transition-colors"
            >
              Open Mailpit Mail Server (localhost:8025) <ArrowRight size={14} />
            </a>
          </div>

          <Link
            href="/login"
            className="block w-full py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 transition-all"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center font-sans selection:bg-indigo-500 selection:text-white relative overflow-hidden px-4">
      {/* Background Gradients */}
      <div className="absolute top-[-30%] left-[-20%] w-[60%] h-[60%] bg-indigo-900/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[60%] h-[60%] bg-violet-900/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="w-full max-w-md bg-neutral-900/40 border border-neutral-800/80 rounded-3xl p-8 md:p-10 backdrop-blur-md shadow-2xl relative z-10 hover:border-neutral-700/30 transition-all duration-300">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center font-bold text-white shadow-xl shadow-indigo-500/25 mb-4 text-xl">
            G
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Create Account</h1>
          <p className="text-neutral-400 text-sm mt-1">Get matching recommendations instantly</p>
        </div>

        {error && (
          <div className="mb-6 bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs px-4 py-3.5 rounded-xl flex items-center gap-2.5">
            <AlertTriangle size={16} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
              Email Address
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@domain.com"
                className="w-full pl-11 pr-4 py-3 bg-neutral-950/60 border border-neutral-800/80 rounded-xl text-sm focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all text-neutral-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
              Password
            </label>
            <div className="relative">
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 8 characters"
                className="w-full pl-11 pr-4 py-3 bg-neutral-950/60 border border-neutral-800/80 rounded-xl text-sm focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all text-neutral-200"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider mb-2">
              Confirm Password
            </label>
            <div className="relative">
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                className="w-full pl-11 pr-4 py-3 bg-neutral-950/60 border border-neutral-800/80 rounded-xl text-sm focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all text-neutral-200"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all mt-4 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Creating Account...
              </>
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-neutral-800/60 text-center">
          <p className="text-neutral-400 text-xs">
            Already have an account?{' '}
            <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
