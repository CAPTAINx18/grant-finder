'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface ServiceStatus {
  status: 'healthy' | 'unhealthy' | 'unknown';
  latency_ms?: number | null;
}

interface HealthData {
  status: string;
  timestamp: string;
  version: string;
  services: {
    database: ServiceStatus;
    redis: ServiceStatus;
  };
}

export default function Home() {
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [pingCount, setPingCount] = useState<number>(0);
  const [apiLatency, setApiLatency] = useState<number | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${apiUrl}/health`, {
        cache: 'no-store',
      });
      const end = performance.now();
      setApiLatency(Math.round(end - start));
      
      if (!res.ok) {
        throw new Error(`Server returned status ${res.status}`);
      }
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend api');
      setHealth(null);
      setApiLatency(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, [pingCount]);

  const handlePing = () => {
    setPingCount((prev) => prev + 1);
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white relative overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-900/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-violet-900/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Navigation Header */}
      <header className="border-b border-neutral-800/80 bg-neutral-950/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              G
            </div>
            <span className="font-semibold text-lg tracking-tight bg-gradient-to-r from-white via-neutral-200 to-neutral-400 bg-clip-text text-transparent">
              GrantFinder
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-xs px-2.5 py-1 rounded-full font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Milestone 1 Active
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-6 py-12 flex flex-col justify-center gap-8 relative z-10">
        
        {/* Banner Section */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-4 text-center md:text-left">
            <h2 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-b from-white to-neutral-400 bg-clip-text text-transparent">
              SaaS Infrastructure Verification
            </h2>
            <p className="text-neutral-400 text-lg max-w-2xl">
              This dashboard displays live system checkups querying the backend through Docker containers. It ensures the REST API, Redis memory grid, and PostgreSQL datastore are fully communicating.
            </p>
          </div>
          <div className="flex gap-4 shrink-0 justify-center md:justify-end">
            <Link 
              href="/login"
              className="px-6 py-3 bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-white rounded-xl text-sm font-semibold transition-all shadow-md"
            >
              Sign In
            </Link>
            <Link 
              href="/register"
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-all"
            >
              Get Started
            </Link>
          </div>
        </div>

        {/* Health status grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          
          {/* API Backend Card */}
          <div className="bg-neutral-900/40 border border-neutral-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex flex-col justify-between hover:border-neutral-700/50 transition-all duration-300 group">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">FastAPI API</span>
                <span className={`h-2.5 w-2.5 rounded-full ${error ? 'bg-rose-500 animate-pulse' : loading ? 'bg-amber-500' : 'bg-emerald-500 shadow-lg shadow-emerald-500/50'}`} />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white group-hover:text-indigo-400 transition-colors">Backend Server</h3>
                <p className="text-xs text-neutral-500 mt-1">Python API Gateway runtime</p>
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-neutral-800/60 flex justify-between items-baseline">
              <span className="text-neutral-500 text-sm">HTTP Latency</span>
              <span className="font-mono text-sm font-semibold text-neutral-200">
                {loading ? 'Measuring...' : error ? 'N/A' : `${apiLatency} ms`}
              </span>
            </div>
          </div>

          {/* PostgreSQL Card */}
          <div className="bg-neutral-900/40 border border-neutral-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex flex-col justify-between hover:border-neutral-700/50 transition-all duration-300 group">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">PostgreSQL</span>
                <span className={`h-2.5 w-2.5 rounded-full ${(!health || health.services.database.status !== 'healthy') ? 'bg-rose-500' : 'bg-emerald-500 shadow-lg shadow-emerald-500/50'}`} />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white group-hover:text-indigo-400 transition-colors">Relational Database</h3>
                <p className="text-xs text-neutral-500 mt-1">Postgres 16 + pgvector storage</p>
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-neutral-800/60 flex justify-between items-baseline">
              <span className="text-neutral-500 text-sm">Status</span>
              <span className={`font-mono text-sm font-semibold uppercase ${(!health || health.services.database.status !== 'healthy') ? 'text-rose-400' : 'text-emerald-400'}`}>
                {loading ? 'Reading...' : (health?.services.database.status || 'Offline')}
              </span>
            </div>
          </div>

          {/* Redis Card */}
          <div className="bg-neutral-900/40 border border-neutral-800/80 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex flex-col justify-between hover:border-neutral-700/50 transition-all duration-300 group">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold uppercase tracking-wider text-neutral-400">Redis Cache</span>
                <span className={`h-2.5 w-2.5 rounded-full ${(!health || health.services.redis.status !== 'healthy') ? 'bg-rose-500' : 'bg-emerald-500 shadow-lg shadow-emerald-500/50'}`} />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-white group-hover:text-indigo-400 transition-colors">Memory Buffer</h3>
                <p className="text-xs text-neutral-500 mt-1">Celery broker & cache layer</p>
              </div>
            </div>
            <div className="mt-8 pt-4 border-t border-neutral-800/60 flex justify-between items-baseline">
              <span className="text-neutral-500 text-sm">Broker Ping</span>
              <span className="font-mono text-sm font-semibold text-neutral-200">
                {loading ? 'Pinging...' : (health?.services.redis.latency_ms ? `${health.services.redis.latency_ms} ms` : 'N/A')}
              </span>
            </div>
          </div>

        </div>

        {/* Action Controls & API payload inspect */}
        <div className="bg-neutral-900/20 border border-neutral-800/80 rounded-2xl p-6 backdrop-blur-sm flex flex-col md:flex-row gap-6 items-stretch justify-between">
          <div className="space-y-2 flex-1">
            <h4 className="text-lg font-semibold text-white">Trigger Connection Check</h4>
            <p className="text-neutral-400 text-sm">
              Press the ping button to force the frontend to fetch system variables from FastAPI container and compute live responses.
            </p>
          </div>
          <div className="flex items-center justify-center">
            <button
              onClick={handlePing}
              disabled={loading}
              className="px-6 py-3.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-semibold text-sm shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95 transition-all w-full md:w-auto"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Fetching Status
                </span>
              ) : (
                'Ping Health Check'
              )}
            </button>
          </div>
        </div>

        {/* Raw payload console logs */}
        <div className="space-y-3">
          <div className="flex justify-between items-center px-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-neutral-500">Live JSON Feed</span>
            {health && (
              <span className="text-xs text-neutral-400 font-mono">
                API Version: {health.version} | TS: {new Date(Number(health.timestamp) * 1000).toLocaleTimeString()}
              </span>
            )}
          </div>
          <div className="bg-neutral-900 border border-neutral-800/80 rounded-2xl p-5 overflow-x-auto shadow-2xl relative">
            <pre className="font-mono text-xs text-indigo-300 leading-relaxed">
              {loading && !health
                ? '// Querying http://localhost:8000/api/v1/health...'
                : error
                ? `{\n  "error": true,\n  "message": "${error}",\n  "tip": "Verify Docker backend container is running!"\n}`
                : JSON.stringify(health, null, 2)}
            </pre>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-neutral-900 bg-neutral-950/80 mt-auto py-8">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between text-neutral-500 text-xs gap-4">
          <div>
            &copy; {new Date().getFullYear()} GrantFinder SaaS. All rights reserved.
          </div>
          <div className="flex gap-6">
            <span>Enterprise Stack Ready</span>
            <span>Clean Architecture</span>
            <span>Dockerized Deployment</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
