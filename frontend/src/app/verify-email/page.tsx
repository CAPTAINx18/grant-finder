'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/utils/api';
import { Loader2, CheckCircle2, XCircle, ArrowRight, RefreshCw } from 'lucide-react';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  const [statusState, setStatusState] = useState<'loading' | 'success' | 'failed'>('loading');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(4);

  useEffect(() => {
    const performVerification = async () => {
      if (!token) {
        setStatusState('failed');
        setErrorMessage('Verification token is missing from link.');
        return;
      }

      try {
        await api.post('/auth/verify-email', { token }, { skipAuth: true });
        setStatusState('success');
      } catch (err: any) {
        setStatusState('failed');
        setErrorMessage(err.message || 'Token is invalid, expired, or already used.');
      }
    };

    performVerification();
  }, [token]);

  // Handle redirect countdown on success
  useEffect(() => {
    if (statusState === 'success') {
      const interval = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(interval);
            router.push('/login');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [statusState, router]);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center font-sans selection:bg-indigo-500 selection:text-white px-4 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-[-30%] left-[-20%] w-[60%] h-[60%] bg-indigo-900/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[60%] h-[60%] bg-violet-900/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="w-full max-w-md bg-neutral-900/40 border border-neutral-800/80 rounded-3xl p-8 md:p-10 backdrop-blur-md shadow-2xl relative z-10 text-center">
        {/* Loading state */}
        {statusState === 'loading' && (
          <div className="space-y-6">
            <Loader2 className="animate-spin text-indigo-500 mx-auto" size={48} />
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">Verifying Email</h1>
              <p className="text-neutral-400 text-xs mt-2">Connecting with server to activate account...</p>
            </div>
          </div>
        )}

        {/* Verification Success state */}
        {statusState === 'success' && (
          <div className="space-y-6">
            <div className="h-14 w-14 rounded-full bg-emerald-500/10 border border-emerald-500/25 flex items-center justify-center text-emerald-400 mx-auto">
              <CheckCircle2 size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Email Verified!</h1>
              <p className="text-neutral-400 text-sm mt-2 leading-relaxed">
                Your account is activated and ready. You will be redirected to the login portal automatically in{' '}
                <span className="font-bold text-indigo-400 font-mono">{countdown}</span> seconds.
              </p>
            </div>
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 w-full py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 transition-all"
            >
              <span>Go to Login</span>
              <ArrowRight size={16} />
            </Link>
          </div>
        )}

        {/* Verification Failed state */}
        {statusState === 'failed' && (
          <div className="space-y-6">
            <div className="h-14 w-14 rounded-full bg-rose-500/10 border border-rose-500/25 flex items-center justify-center text-rose-400 mx-auto">
              <XCircle size={32} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Verification Failed</h1>
              <p className="text-neutral-400 text-xs mt-2 leading-relaxed">
                {errorMessage || 'The activation link is invalid or has expired.'}
              </p>
            </div>
            <div className="space-y-3 pt-2">
              <Link
                href="/login"
                className="block w-full py-3.5 bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-white rounded-xl text-xs font-semibold transition-all"
              >
                Back to Sign In
              </Link>
              <Link
                href="/register"
                className="block w-full py-3.5 bg-neutral-900/40 hover:bg-neutral-900 border border-neutral-900 text-neutral-400 hover:text-neutral-200 rounded-xl text-xs font-semibold transition-all"
              >
                Register New Account
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-neutral-950 text-neutral-100 flex items-center justify-center gap-4">
          <Loader2 className="animate-spin text-indigo-500" size={40} />
          <span className="text-neutral-400 text-sm font-medium tracking-wide">Initializing secure verification...</span>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
