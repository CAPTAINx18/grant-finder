'use client';

import React, { use } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  ArrowLeft, 
  Bookmark, 
  Loader2, 
  ExternalLink, 
  Download, 
  FileText,
  Building,
  Target,
  Sparkles,
  Info
} from 'lucide-react';

interface EligibilityRule {
  id: string;
  applicant_type: string | null;
  sector: string | null;
  project_stage: string | null;
  min_funding_required: number;
}

interface GrantDetails {
  id: string;
  name: string;
  description: string;
  funding_amount_min: number | null;
  funding_amount_max: number | null;
  currency: string;
  official_source_link: string | null;
  document_url: string | null;
  click_count: number;
  bookmark_count: number;
  is_bookmarked: boolean;
  provider: {
    id: string;
    name: string;
    website: string | null;
    provider_type: string | null;
  } | null;
  eligibility_rules: EligibilityRule[];
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

export default function GrantDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();

  // 1. Fetch grant detail parameters
  const { data: grant, isLoading, isError, error } = useQuery<GrantDetails>({
    queryKey: ['grant-details', id],
    queryFn: () => api.get(`/search/grants/${id}`),
  });

  // 2. Bookmark toggle mutation
  const toggleBookmarkMutation = useMutation({
    mutationFn: () => api.post(`/search/grants/${id}/bookmark`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['grant-details', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-bookmarks'] });
      queryClient.invalidateQueries({ queryKey: ['search-grants'] });
    },
  });

  // 3. Authenticated Document Download stream handler
  const handleDownload = async (fileKey: string) => {
    if (typeof window === 'undefined') return;
    
    const token = localStorage.getItem('access_token');
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    
    try {
      const response = await fetch(`${apiUrl}/documents/download/${encodeURIComponent(fileKey)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to download file with status: ${response.status}`);
      }

      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      
      const filename = fileKey.includes('/') ? fileKey.split('/').pop()! : fileKey;
      link.download = filename;
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err: any) {
      alert(`Failed to download guidelines document: ${err.message || err}`);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-[400px] flex flex-col items-center justify-center gap-3">
        <Loader2 className="animate-spin text-indigo-500" size={32} />
        <span className="text-neutral-400 text-xs">Loading grant specifications...</span>
      </div>
    );
  }

  if (isError || !grant) {
    return (
      <div className="bg-neutral-900/20 border border-neutral-900 rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 max-w-xl mx-auto mt-10">
        <Info className="text-rose-400" size={28} />
        <h3 className="text-neutral-200 font-bold">Failed to load grant details</h3>
        <p className="text-neutral-500 text-xs leading-relaxed">
          {error?.message || 'The requested grant opportunity does not exist or has been deleted.'}
        </p>
        <Link 
          href="/dashboard/search" 
          className="mt-4 px-5 py-2.5 bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-white rounded-xl text-xs font-semibold transition-all"
        >
          Back to Search
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* Back navigation and Bookmark toggle row */}
      <div className="flex justify-between items-center">
        <Link 
          href="/dashboard/search"
          className="inline-flex items-center gap-2 text-xs text-neutral-400 hover:text-white font-medium transition-colors"
        >
          <ArrowLeft size={14} />
          <span>Back to Opportunities</span>
        </Link>

        <button
          onClick={() => toggleBookmarkMutation.mutate()}
          disabled={toggleBookmarkMutation.isPending}
          className={`inline-flex items-center gap-2 px-4 py-2 border rounded-xl text-xs font-semibold transition-all hover:scale-105 active:scale-95 ${
            grant.is_bookmarked
              ? 'bg-rose-600/10 border-rose-500/20 text-rose-400'
              : 'bg-neutral-900/40 border-neutral-800 text-neutral-400 hover:text-rose-400 hover:border-rose-500/10'
          }`}
        >
          <Bookmark size={14} fill={grant.is_bookmarked ? 'currentColor' : 'none'} />
          <span>{grant.is_bookmarked ? 'Bookmarked' : 'Save Bookmark'}</span>
        </button>
      </div>

      {/* Main Grid: Details left, Sidebar right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Description & Rules */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Main info panel */}
          <div className="bg-neutral-900/20 border border-neutral-900 rounded-3xl p-6 md:p-8 space-y-6 backdrop-blur-sm">
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight leading-snug">
              {grant.name}
            </h1>
            
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Opportunity Description</h3>
              <p className="text-neutral-300 text-sm leading-relaxed whitespace-pre-line">
                {grant.description}
              </p>
            </div>
          </div>

          {/* Eligibility Rules Panel */}
          <div className="bg-neutral-900/20 border border-neutral-900 rounded-3xl p-6 md:p-8 space-y-6 backdrop-blur-sm">
            <h3 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
              <Target size={16} className="text-indigo-400" />
              <span>Eligibility Guidelines</span>
            </h3>

            {grant.eligibility_rules.length === 0 ? (
              <p className="text-neutral-500 text-xs italic">No specific eligibility rules recorded for this opportunity.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {grant.eligibility_rules.map((rule, idx) => (
                  <div key={rule.id || idx} className="bg-neutral-900/40 border border-neutral-900/80 rounded-xl p-4 space-y-2">
                    <div className="text-[10px] text-neutral-500 font-mono font-semibold uppercase">Rule Spec #{idx + 1}</div>
                    
                    <div className="space-y-1 text-xs">
                      {rule.applicant_type && (
                        <div className="flex justify-between">
                          <span className="text-neutral-500">Applicant:</span>
                          <span className="text-neutral-300 font-medium">{rule.applicant_type}</span>
                        </div>
                      )}
                      {rule.sector && (
                        <div className="flex justify-between">
                          <span className="text-neutral-500">Industry:</span>
                          <span className="text-neutral-300 font-medium">{rule.sector}</span>
                        </div>
                      )}
                      {rule.project_stage && (
                        <div className="flex justify-between">
                          <span className="text-neutral-500">Project Stage:</span>
                          <span className="text-neutral-300 font-medium">{rule.project_stage}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Funding details, Provider info, guideline files */}
        <div className="space-y-8">
          
          {/* Funding amount card */}
          <div className="bg-gradient-to-tr from-indigo-900/20 to-violet-900/20 border border-indigo-500/20 rounded-3xl p-6 backdrop-blur-sm space-y-4">
            <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
              <Sparkles size={14} />
              <span>Funding Value Range</span>
            </h4>
            
            <div className="space-y-1">
              <span className="text-xl font-extrabold text-white tracking-tight flex items-baseline gap-1">
                {formatFunding(grant.funding_amount_max, grant.currency)}
              </span>
              <p className="text-neutral-400 text-[10px]">
                {grant.funding_amount_min 
                  ? `Min Funding Limit starts at ${formatFunding(grant.funding_amount_min, grant.currency)}` 
                  : 'No minimum funding floor limit configured.'}
              </p>
            </div>

            {grant.official_source_link && (
              <a
                href={grant.official_source_link}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-center gap-2 px-4 py-3 bg-white text-neutral-950 font-bold rounded-xl text-xs shadow-lg hover:bg-neutral-200 transition-all w-full mt-4"
              >
                <span>Official Source URL</span>
                <ExternalLink size={14} />
              </a>
            )}
          </div>

          {/* Provider Card */}
          <div className="bg-neutral-900/20 border border-neutral-900 rounded-3xl p-6 backdrop-blur-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
              <Building size={14} className="text-neutral-500" />
              <span>Grant Publisher Agency</span>
            </h4>

            {grant.provider ? (
              <div className="space-y-3">
                <div>
                  <h5 className="font-semibold text-neutral-200 text-sm leading-snug">{grant.provider.name}</h5>
                  <p className="text-neutral-500 text-[10px] mt-0.5 font-mono">{grant.provider.provider_type || 'NGO'}</p>
                </div>
                {grant.provider.website && (
                  <a
                    href={grant.provider.website}
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 transition-colors"
                  >
                    <span>Visit Agency Website</span>
                    <ExternalLink size={12} />
                  </a>
                )}
              </div>
            ) : (
              <p className="text-neutral-500 text-xs italic">Publisher information not documented.</p>
            )}
          </div>

          {/* Guideline attachments card */}
          <div className="bg-neutral-900/20 border border-neutral-900 rounded-3xl p-6 backdrop-blur-sm space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
              <FileText size={14} className="text-neutral-500" />
              <span>Guidelines Documentation</span>
            </h4>

            {grant.document_url ? (
              <div className="space-y-3">
                <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl p-3.5 flex items-center gap-3">
                  <FileText className="text-indigo-400 shrink-0" size={24} />
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-neutral-300 truncate">
                      {grant.document_url.includes('/') ? grant.document_url.split('/').pop()! : grant.document_url}
                    </p>
                    <p className="text-[10px] text-neutral-500 font-mono">S3 Stored Asset</p>
                  </div>
                </div>
                
                <button
                  onClick={() => handleDownload(grant.document_url!)}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 hover:text-white rounded-xl text-xs font-semibold transition-all w-full"
                >
                  <Download size={14} />
                  <span>Download Attachment</span>
                </button>
              </div>
            ) : (
              <p className="text-neutral-500 text-xs italic">No guidelines file attached to this opportunity.</p>
            )}
          </div>

        </div>

      </div>

    </div>
  );
}
