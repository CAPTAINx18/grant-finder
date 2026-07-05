'use client';

import React, { useState } from 'react';
import { api } from '@/utils/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Database, 
  Play, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  RefreshCw,
  Info
} from 'lucide-react';

interface CrawlerSource {
  id: string;
  name: string;
  url: string;
  update_method: string;
  cron_schedule: string;
  is_active: boolean;
  last_run_at: string | null;
  last_run_status: string | null;
  last_run_error: string | null;
  metadata_json: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

interface IngestionMonitoring {
  total_grants_imported: number;
  last_sync_time: string | null;
  failed_sources: { id: string; name: string; error: string | null }[];
}

export default function IngestionDashboard() {
  const queryClient = useQueryClient();
  const [triggeringSourceId, setTriggeringSourceId] = useState<string | null>(null);

  // 1. Fetch crawler sources registry with automatic polling every 5 seconds
  const { data: sources = [], isLoading, isError, error } = useQuery<CrawlerSource[]>({
    queryKey: ['ingestion-sources'],
    queryFn: () => api.get('/ingestion/sources'),
    refetchInterval: 5000, // Poll source states every 5s automatically!
  });

  // 2. Fetch aggregation monitoring metrics
  const { data: metrics, isLoading: isLoadingMetrics } = useQuery<IngestionMonitoring>({
    queryKey: ['ingestion-monitoring'],
    queryFn: () => api.get('/ingestion/monitoring'),
    refetchInterval: 5000, // Poll metrics every 5s automatically!
  });

  // 3. Trigger crawling job mutation
  const triggerCrawlMutation = useMutation({
    mutationFn: (sourceId: string) => api.post(`/ingestion/trigger/${sourceId}`, {}),
    onMutate: (sourceId) => {
      setTriggeringSourceId(sourceId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingestion-sources'] });
      queryClient.invalidateQueries({ queryKey: ['ingestion-monitoring'] });
      setTriggeringSourceId(null);
    },
    onError: (err: any) => {
      alert(`Trigger failed: ${err.message || err}`);
      setTriggeringSourceId(null);
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center gap-3">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
        <span className="text-neutral-400 text-xs">Loading crawler source registries...</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-500/5 border border-rose-500/10 rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-2 max-w-xl mx-auto mt-10">
        <AlertTriangle className="text-rose-400" size={28} />
        <span className="text-neutral-200 font-bold">Failed to load crawler sources</span>
        <span className="text-neutral-500 text-xs max-w-sm">{(error as any).message || 'Backend API server offline.'}</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Title Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Crawler Registry Ingestion</h1>
          <p className="text-neutral-400 text-sm mt-1">
            Activate, schedule, and trigger background scraping pipelines asynchronously via Celery worker pools.
          </p>
        </div>
        <div className="flex items-center gap-2 text-neutral-500 text-xs font-mono bg-neutral-900 px-3.5 py-1.5 rounded-full border border-neutral-800">
          <RefreshCw size={12} className="animate-spin text-indigo-500" />
          <span>Polling state real-time (5s)</span>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-neutral-900/30 border border-neutral-900 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex items-center justify-between">
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-neutral-400 tracking-wide uppercase">Total Grants Imported</span>
            <h3 className="text-2xl font-bold text-white tracking-tight">
              {isLoadingMetrics ? '...' : metrics?.total_grants_imported ?? 0}
            </h3>
          </div>
          <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-indigo-500/20 to-violet-500/20 flex items-center justify-center text-indigo-400 shadow-lg shadow-indigo-500/5">
            <Database size={20} />
          </div>
        </div>

        <div className="bg-neutral-900/30 border border-neutral-900 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex items-center justify-between">
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-neutral-400 tracking-wide uppercase">Last Sync Timestamp</span>
            <h3 className="text-sm font-semibold text-neutral-200 tracking-tight">
              {isLoadingMetrics ? '...' : metrics?.last_sync_time ? new Date(metrics.last_sync_time).toLocaleString() : 'Never'}
            </h3>
          </div>
          <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-emerald-500/20 to-teal-500/20 flex items-center justify-center text-emerald-400 shadow-lg shadow-emerald-500/5">
            <Clock size={20} />
          </div>
        </div>

        <div className={`bg-neutral-900/30 border rounded-2xl p-6 backdrop-blur-sm shadow-xl flex items-center justify-between transition-all duration-300 ${
          metrics?.failed_sources && metrics.failed_sources.length > 0 ? 'border-rose-500/30 bg-rose-500/5' : 'border-neutral-900'
        }`}>
          <div className="space-y-1.5">
            <span className="text-xs font-medium text-neutral-400 tracking-wide uppercase">Failing Sync Pipelines</span>
            <h3 className={`text-2xl font-bold tracking-tight ${
              metrics?.failed_sources && metrics.failed_sources.length > 0 ? 'text-rose-400 animate-pulse' : 'text-white'
            }`}>
              {isLoadingMetrics ? '...' : metrics?.failed_sources?.length ?? 0}
            </h3>
          </div>
          <div className={`h-12 w-12 rounded-xl flex items-center justify-center shadow-lg ${
            metrics?.failed_sources && metrics.failed_sources.length > 0
              ? 'bg-rose-500/20 text-rose-400 shadow-rose-500/5'
              : 'bg-neutral-900 text-neutral-500 shadow-indigo-500/5'
          }`}>
            <AlertTriangle size={20} />
          </div>
        </div>
      </div>

      {sources.length === 0 ? (
        <div className="bg-neutral-900/10 border border-neutral-900 rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 backdrop-blur-sm min-h-[300px]">
          <div className="h-12 w-12 rounded-full bg-neutral-900 flex items-center justify-center text-neutral-500 mb-2">
            <Database size={20} />
          </div>
          <span className="text-neutral-300 text-sm font-semibold">No Crawler Sources Configured</span>
          <p className="text-neutral-500 text-xs max-w-sm">
            Please run Alembic migrations or wait for the system to auto-seed active crawler source entries.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6">
          {sources.map((source) => {
            const isTriggering = triggeringSourceId === source.id;
            const isRunning = source.last_run_status === 'running';
            const isSuccess = source.last_run_status === 'success';
            const isFailed = source.last_run_status === 'failed';

            return (
              <div 
                key={source.id}
                className="bg-neutral-900/30 border border-neutral-900 rounded-2xl p-6 backdrop-blur-sm shadow-xl flex flex-col gap-6"
              >
                {/* Upper block info and action triggers */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="text-base font-bold text-neutral-200 truncate">{source.name}</h3>
                      <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-950 text-neutral-400 border border-neutral-900 uppercase font-semibold font-mono tracking-wider">
                        {source.update_method}
                      </span>
                      <span className={`text-[10px] px-2.5 py-0.5 rounded-full font-semibold uppercase ${
                        source.is_active 
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                          : 'bg-neutral-800 text-neutral-500'
                      }`}>
                        {source.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <p className="text-neutral-500 text-xs truncate leading-relaxed">
                      Target Link: <a href={source.url} target="_blank" rel="noreferrer" className="text-indigo-400 hover:text-indigo-300 transition-colors">{source.url}</a>
                    </p>
                  </div>

                  {/* Trigger crawl action */}
                  <button
                    onClick={() => triggerCrawlMutation.mutate(source.id)}
                    disabled={isTriggering || isRunning || !source.is_active}
                    className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-semibold text-xs shadow-md disabled:opacity-50 disabled:cursor-not-allowed transition-all shrink-0 w-full md:w-auto hover:scale-[1.02] active:scale-[0.98]"
                  >
                    {isTriggering || isRunning ? (
                      <>
                        <Loader2 className="animate-spin" size={14} />
                        <span>Worker Busy...</span>
                      </>
                    ) : (
                      <>
                        <Play size={14} fill="currentColor" />
                        <span>Run Scraper Job</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Status details & Scheduling details */}
                <div className="pt-5 border-t border-neutral-900 grid grid-cols-1 md:grid-cols-3 gap-6 items-center text-xs">
                  {/* Active Scheduling cron */}
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-neutral-500" />
                    <div>
                      <p className="text-[10px] text-neutral-500 uppercase font-semibold">Cron Frequency</p>
                      <p className="text-neutral-300 font-mono font-medium">{source.cron_schedule}</p>
                    </div>
                  </div>

                  {/* Latest run status metrics */}
                  <div className="flex items-center gap-2">
                    {isRunning ? (
                      <Loader2 className="animate-spin text-indigo-400 shrink-0" size={18} />
                    ) : isSuccess ? (
                      <CheckCircle2 className="text-emerald-400 shrink-0" size={18} />
                    ) : isFailed ? (
                      <XCircle className="text-rose-400 shrink-0" size={18} />
                    ) : (
                      <Clock className="text-neutral-500 shrink-0" size={18} />
                    )}
                    <div>
                      <p className="text-[10px] text-neutral-500 uppercase font-semibold">Latest Run Result</p>
                      <p className={`font-semibold capitalize ${
                        isRunning ? 'text-indigo-400 animate-pulse' : isSuccess ? 'text-emerald-400' : isFailed ? 'text-rose-400' : 'text-neutral-400'
                      }`}>
                        {source.last_run_status || 'Never Executed'}
                      </p>
                    </div>
                  </div>

                  {/* Last crawl timestamp */}
                  <div className="flex items-center gap-2">
                    <Clock size={16} className="text-neutral-500" />
                    <div>
                      <p className="text-[10px] text-neutral-500 uppercase font-semibold">Last Ingest Time</p>
                      <p className="text-neutral-300 font-medium">
                        {source.last_run_at ? new Date(source.last_run_at).toLocaleString() : 'N/A'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Error Console Logs (rendered only upon crawler failures) */}
                {isFailed && source.last_run_error && (
                  <div className="bg-rose-950/10 border border-rose-500/10 rounded-xl p-4 flex gap-3 text-xs text-rose-400">
                    <AlertTriangle className="shrink-0 mt-0.5" size={16} />
                    <div className="space-y-1 overflow-x-auto w-full">
                      <p className="font-semibold uppercase tracking-wider text-[10px]">Crawl Exception Log:</p>
                      <pre className="font-mono text-[10px] leading-relaxed whitespace-pre-wrap">{source.last_run_error}</pre>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
}
