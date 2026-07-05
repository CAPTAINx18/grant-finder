'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { KeyRound, Mail, AlertTriangle, ShieldAlert, Loader2 } from 'lucide-react';

function LoginContent() {
  const { login } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expiredMsg, setExpiredMsg] = useState(false);

  useEffect(() => {
    if (searchParams.get('expired') === 'true') {
      setExpiredMsg(true);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setLoading(true);
    setError(null);
    setExpiredMsg(false);

    try {
      await login(email, password);
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Incorrect email or password. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center font-sans selection:bg-indigo-500 selection:text-white relative overflow-hidden px-4">
      {/* Dynamic Background Gradients */}
      <div className="absolute top-[-30%] left-[-20%] w-[60%] h-[60%] bg-indigo-900/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[60%] h-[60%] bg-violet-900/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="w-full max-w-md bg-neutral-900/40 border border-neutral-800/80 rounded-3xl p-8 md:p-10 backdrop-blur-md shadow-2xl relative z-10 hover:border-neutral-700/30 transition-all duration-300">
        
        {/* Brand Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="h-12 w-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center font-bold text-white shadow-xl shadow-indigo-500/25 mb-4 text-xl">
            G
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Welcome Back</h1>
          <p className="text-neutral-400 text-sm mt-1">Sign in to search global grants</p>
        </div>

        {/* Notifications and Alerts */}
        {expiredMsg && (
          <div className="mb-6 bg-amber-500/10 border border-amber-500/25 text-amber-400 text-xs px-4 py-3.5 rounded-xl flex items-center gap-2.5">
            <ShieldAlert size={16} className="shrink-0" />
            <span>Your session has expired. Please sign in again.</span>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-rose-500/10 border border-rose-500/25 text-rose-400 text-xs px-4 py-3.5 rounded-xl flex items-center gap-2.5">
            <AlertTriangle size={16} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
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
            <div className="flex justify-between items-baseline mb-2">
              <label className="block text-xs font-semibold text-neutral-400 uppercase tracking-wider">
                Password
              </label>
            </div>
            <div className="relative">
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
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
                <Loader2 className="animate-spin" size={14} />
                <span>Signing In...</span>
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer Links */}
        <div className="mt-8 pt-6 border-t border-neutral-800/60 text-center">
          <p className="text-neutral-400 text-xs">
            Don't have an account?{' '}
            <Link href="/register" className="text-indigo-400 hover:text-indigo-300 font-semibold transition-colors">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense 
      fallback={
        <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center gap-4">
          <Loader2 className="animate-spin text-indigo-500" size={40} />
          <span className="text-neutral-400 text-sm font-medium tracking-wide">Loading secure login...</span>
        </div>
      }
    >
      <LoginContent />
    </Suspense>
  );
}
