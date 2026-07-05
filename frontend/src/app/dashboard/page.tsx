'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { api } from '@/utils/api';
import { useQuery } from '@tanstack/react-query';
import { 
  Bookmark, 
  Database, 
  ArrowUpRight, 
  Loader2, 
  Clock,
  Sparkles,
  Info
} from 'lucide-react';

interface BookmarkedGrant {
  id: string;
  name: string;
  description: string;
  funding_amount_max: number | null;
  currency: string;
  deadline: string | null;
  bookmark_count: number;
}

// Local currency helper
const formatFunding = (amount: number | null, currency: string): string => {
  if (!amount) return 'Funding: N/A';
  
  const formatINR = (val: number) => {
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2).replace(/\.?0+$/, '')} Crore`;
    }
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2).replace(/\.?0+$/, '')} Lakh`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  if (currency === 'INR') {
    return formatINR(amount);
  }

  let inrVal = amount;
  if (currency === 'USD') inrVal = amount * 85.0;
  else if (currency === 'EUR') inrVal = amount * 92.0;

  const originalStr = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0
  }).format(amount);

  return `${originalStr} (≈ ${formatINR(inrVal)})`;
};

export default function UserDashboard() {
  const { user } = useAuth();
  const [latency, setLatency] = useState<number | null>(null);

  // 1. Fetch user bookmarks
  const { data: bookmarks = [], isLoading: isLoadingBookmarks, error: bookmarksError } = useQuery<BookmarkedGrant[]>({
    queryKey: ['dashboard-bookmarks'],
    queryFn: () => api.get('/search/bookmarks'),
  });

  // 2. Fetch ingestion sources count
  const { data: sources = [], isLoading: isLoadingSources } = useQuery<any[]>({
    queryKey: ['dashboard-sources'],
    queryFn: () => api.get('/ingestion/sources'),
  });

  // 3. Measure health latency dynamic check
  useEffect(() => {
    const measureLatency = async () => {
      const start = performance.now();
      try {
        await api.get('/health', { skipAuth: true });
        const end = performance.now();
        setLatency(Math.round(end - start));
      } catch (err) {
        setLatency(null);
      }
    };

    measureLatency();
    const interval = setInterval(measureLatency, 30000);
    return () => clearInterval(interval);
  }, []);

  const stats = [
    {
      name: 'Bookmarked Grants',
      value: isLoadingBookmarks ? '...' : bookmarks.length,
      icon: Bookmark,
      color: 'from-pink-500/20 to-rose-500/20',
      textColor: 'text-rose-400',
    },
    {
      name: 'Crawler Registries',
      value: isLoadingSources ? '...' : sources.length,
      icon: Database,
      color: 'from-indigo-500/20 to-violet-500/20',
      textColor: 'text-indigo-400',
    },
    {
      name: 'System Network Latency',
      value: latency === null ? 'Offline' : `${latency} ms`,
      icon: Clock,
      color: 'from-emerald-500/20 to-teal-500/20',
      textColor: latency === null ? 'text-rose-400' : 'text-emerald-400',
    },
  ];

  return (
    <div className="space-y-10">
      
      {/* Upper Dashboard header banner */}
      <div className="bg-gradient-to-r from-neutral-900/60 to-neutral-900/10 border border-neutral-900 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden">
        <div className="absolute top-[-20%] right-[-10%] w-[40%] h-[140%] bg-indigo-900/10 rounded-full blur-[80px] pointer-events-none" />
        <div className="space-y-3 relative z-10">
          <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold tracking-wider uppercase">
            <Sparkles size={14} />
            <span>Workspace Dashboard</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white leading-tight">
            Hello, {user?.email.split('@')[0]}
          </h1>
          <p className="text-neutral-400 text-sm max-w-2xl">
            Welcome to your GrantFinder SaaS platform workspace. Run semantic search queries against thousands of grants, review crawling registries, or trigger background celery workers to scrape new sources.
          </p>
        </div>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div 
              key={idx} 
              className="bg-neutral-900/30 border border-neutral-900 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex items-center justify-between hover:border-neutral-800 transition-all duration-300 group"
            >
              <div className="space-y-1.5">
                <span className="text-xs font-medium text-neutral-400 tracking-wide uppercase">{stat.name}</span>
                <h3 className="text-2xl font-bold text-white tracking-tight">{stat.value}</h3>
              </div>
              <div className={`h-12 w-12 rounded-xl bg-gradient-to-tr ${stat.color} flex items-center justify-center ${stat.textColor} shadow-lg shadow-indigo-500/5`}>
                <Icon size={20} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Primary Panels: Action buttons and Bookmarked Grants */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Recent Bookmarks */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center px-1">
            <h3 className="text-lg font-bold text-white tracking-tight">Your Saved Bookmarks</h3>
            <Link href="/dashboard/search" className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors">
              Search Grants <ArrowUpRight size={14} />
            </Link>
          </div>

          <div className="bg-neutral-900/20 border border-neutral-900 rounded-2xl p-6 min-h-[300px] flex flex-col backdrop-blur-sm">
            {isLoadingBookmarks ? (
              <div className="flex-1 flex flex-col items-center justify-center gap-3">
                <Loader2 className="animate-spin text-indigo-500" size={24} />
                <span className="text-neutral-400 text-xs">Loading bookmarks...</span>
              </div>
            ) : bookmarksError ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-2">
                <Info className="text-rose-400" size={24} />
                <span className="text-neutral-300 text-sm font-semibold">Failed to load bookmarks</span>
                <span className="text-neutral-500 text-xs max-w-sm">Please verify the database is active and refresh.</span>
              </div>
            ) : bookmarks.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 gap-3">
                <div className="h-12 w-12 rounded-full bg-neutral-900 flex items-center justify-center text-neutral-500 mb-2">
                  <Bookmark size={20} />
                </div>
                <span className="text-neutral-300 text-sm font-semibold">No Bookmarks Saved Yet</span>
                <span className="text-neutral-500 text-xs max-w-xs">
                  Browse matching grants using the search engine and save bookmarks for quick retrieval.
                </span>
                <Link 
                  href="/dashboard/search" 
                  className="mt-2 px-4 py-2 bg-neutral-900 border border-neutral-800 text-neutral-300 hover:text-white rounded-xl text-xs font-semibold hover:bg-neutral-800 transition-all"
                >
                  Discover Opportunities
                </Link>
              </div>
            ) : (
              <div className="space-y-4 flex-1">
                {bookmarks.map((grant) => (
                  <Link 
                    key={grant.id} 
                    href={`/dashboard/search/${grant.id}`}
                    className="block bg-neutral-900/40 hover:bg-neutral-900/90 border border-neutral-900/60 hover:border-neutral-800/80 rounded-xl p-4 transition-all duration-300 group"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="min-w-0 space-y-1">
                        <h4 className="font-semibold text-neutral-200 group-hover:text-indigo-400 transition-colors truncate text-sm">
                          {grant.name}
                        </h4>
                        <p className="text-neutral-400 text-xs line-clamp-2 leading-relaxed">
                          {grant.description}
                        </p>
                      </div>
                      <div className="shrink-0 flex flex-col items-end gap-1">
                        <span className="text-xs font-bold text-neutral-200">
                          {formatFunding(grant.funding_amount_max, grant.currency)}
                        </span>
                        <span className="text-[10px] text-neutral-500 bg-neutral-950 px-2 py-0.5 rounded-full border border-neutral-900">
                          Saved by {grant.bookmark_count} users
                        </span>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Quick Utilities */}
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-white tracking-tight px-1">Quick Tools</h3>
          
          <div className="bg-neutral-900/20 border border-neutral-900 rounded-2xl p-6 backdrop-blur-sm space-y-5">
            
            {/* Quick search shortcut card */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Search Engine</h4>
              <p className="text-neutral-400 text-xs leading-relaxed">
                Scan grants with the Hybrid Search engine merging FTS indexing with pgvector similarity ranks.
              </p>
              <Link 
                href="/dashboard/search" 
                className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-indigo-500/10 transition-all w-full justify-center"
              >
                Open Smart Search <ArrowUpRight size={14} />
              </Link>
            </div>

            <hr className="border-neutral-900" />

            {/* Quick crawler registry card */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-400">Ingestion Worker</h4>
              <p className="text-neutral-400 text-xs leading-relaxed">
                Manage registered data sources, check cron scheduling, and review run statuses.
              </p>
              <Link 
                href="/dashboard/ingestion" 
                className="inline-flex items-center gap-1.5 px-4 py-2.5 bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-white rounded-xl text-xs font-semibold transition-all w-full justify-center"
              >
                Open Ingestion Center <ArrowUpRight size={14} />
              </Link>
            </div>

            <hr className="border-neutral-900" />

            {/* Quick tips */}
            <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl p-4 flex gap-3">
              <Info className="text-indigo-400 shrink-0 mt-0.5" size={16} />
              <div className="space-y-1">
                <h5 className="text-[11px] font-semibold text-neutral-300">Local Development Tip</h5>
                <p className="text-[10px] text-neutral-500 leading-relaxed">
                  Trigger scraping jobs on the Ingestion tab. Newly fetched grants will automatically appear on the search panel.
                </p>
              </div>
            </div>

          </div>
        </div>

      </div>

    </div>
  );
}
