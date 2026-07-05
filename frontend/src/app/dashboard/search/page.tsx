'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { api } from '@/utils/api';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  Search, 
  SlidersHorizontal, 
  Bookmark, 
  Loader2, 
  BookOpen, 
  Info,
  DollarSign,
  FilterX
} from 'lucide-react';

interface SearchResult {
  id: string;
  name: string;
  description: string;
  funding_amount_max: number | null;
  currency: string;
  deadline: string | null;
  score: number;
}

interface SearchResponse {
  query: string;
  results_count: number;
  results: SearchResult[];
}

// Funding Display dual-currency formatter (USD/EUR conversions, INR Crore/Lakh formatting)
export const formatFunding = (amount: number | null, currency: string): string => {
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

  // Live conversion estimation
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

export default function GrantSearchPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [limit, setLimit] = useState(20); // Default to 20 results
  const [threshold, setThreshold] = useState(0.2); // Tweak similarity
  const [showFilters, setShowFilters] = useState(false);

  // Filters state
  const [selectedSector, setSelectedSector] = useState<string>('All');
  const [selectedCountry, setSelectedCountry] = useState<string>('All');
  const [maxFundingLimit, setMaxFundingLimit] = useState<number>(100000000); // 10 Cr or 100M USD

  // 1. Fetch query results
  const { data, isLoading, isError, error } = useQuery<SearchResponse>({
    queryKey: ['search-grants', debouncedQuery, limit, threshold],
    queryFn: () => api.get(`/search?q=${encodeURIComponent(debouncedQuery)}&limit=${limit}&threshold=${threshold}`),
    enabled: debouncedQuery.length >= 1,
  });

  // 2. Fetch user's bookmarks
  const { data: bookmarkedList = [] } = useQuery<any[]>({
    queryKey: ['dashboard-bookmarks'],
    queryFn: () => api.get('/search/bookmarks'),
  });

  const bookmarkedIds = new Set(bookmarkedList.map((b) => b.id));

  // 3. Bookmark toggle mutation
  const toggleBookmarkMutation = useMutation({
    mutationFn: (grantId: string) => api.post(`/search/grants/${grantId}/bookmark`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard-bookmarks'] });
      queryClient.invalidateQueries({ queryKey: ['search-grants'] });
    },
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim().length >= 1) {
      setDebouncedQuery(searchQuery.trim());
    }
  };

  const handleClearFilters = () => {
    setSelectedSector('All');
    setSelectedCountry('All');
    setMaxFundingLimit(100000000);
  };

  // Client-side filtering logic
  const results = data?.results || [];
  const filteredResults = results.filter((grant) => {
    // 1. Funding Limit check
    if (grant.funding_amount_max && grant.funding_amount_max > maxFundingLimit) {
      return false;
    }
    // 2. Country/Eligibility check
    if (selectedCountry !== 'All') {
      const desc = grant.description.toLowerCase();
      const name = grant.name.toLowerCase();
      const matchIn = name.includes('india') || desc.includes('india') || desc.includes('indian');
      const matchEu = name.includes('eu') || name.includes('europe') || desc.includes('europe') || desc.includes('european');
      
      if (selectedCountry === 'India' && !matchIn) return false;
      if (selectedCountry === 'Europe' && !matchEu) return false;
      if (selectedCountry === 'Global' && (matchIn || matchEu)) return false;
    }
    // 3. Sector matching check
    if (selectedSector !== 'All') {
      const desc = grant.description.toLowerCase();
      const name = grant.name.toLowerCase();
      const isTech = name.includes('tech') || name.includes('digital') || name.includes('computer') || name.includes('semiconductor') || desc.includes('technology') || desc.includes('software') || desc.includes('machine learning');
      const isEnv = name.includes('climate') || name.includes('environment') || name.includes('water') || desc.includes('agriculture') || desc.includes('ecology') || desc.includes('clean energy');
      const isBio = name.includes('biotech') || name.includes('birac') || name.includes('biology') || desc.includes('biotechnology') || desc.includes('healthcare') || desc.includes('vaccine');
      
      if (selectedSector === 'Technology' && !isTech) return false;
      if (selectedSector === 'Environment' && !isEnv) return false;
      if (selectedSector === 'Biotechnology' && !isBio) return false;
    }
    return true;
  });

  return (
    <div className="space-y-8">
      
      {/* Title Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Smart Search Engine</h1>
        <p className="text-neutral-400 text-sm mt-1">
          Search thousands of grants using our hybrid search query engine. Prioritized for Indian founders and global eligible schemes.
        </p>
      </div>

      {/* Query Bar */}
      <form onSubmit={handleSearchSubmit} className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-neutral-500" size={18} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Type search terms (e.g. 'Startup India', 'Biotech', 'Green Energy')..."
            className="w-full pl-12 pr-4 py-3.5 bg-neutral-900/40 border border-neutral-900 rounded-xl text-sm focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all text-neutral-200"
          />
        </div>
        <button
          type="submit"
          className="px-6 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl font-semibold text-sm shadow-md transition-all shrink-0"
        >
          Search
        </button>
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className={`p-3.5 border rounded-xl transition-all shrink-0 flex items-center justify-center ${
            showFilters || selectedSector !== 'All' || selectedCountry !== 'All'
              ? 'border-indigo-500/30 bg-indigo-600/10 text-indigo-400'
              : 'border-neutral-900 text-neutral-400 hover:text-white hover:bg-neutral-900/50'
          }`}
        >
          <SlidersHorizontal size={18} />
        </button>
      </form>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-neutral-900/20 border border-neutral-900 rounded-2xl p-6 backdrop-blur-sm grid grid-cols-1 md:grid-cols-4 gap-6 items-end relative overflow-hidden">
          
          {/* Sector Selector */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Sector Filter</label>
            <select
              value={selectedSector}
              onChange={(e) => setSelectedSector(e.target.value)}
              className="w-full bg-neutral-950/60 border border-neutral-900 rounded-xl px-3 py-2.5 text-xs text-neutral-300 focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all outline-none"
            >
              <option value="All">All Sectors</option>
              <option value="Technology">Technology & AI</option>
              <option value="Environment">Green Tech & Agri</option>
              <option value="Biotechnology">Biotech & Healthcare</option>
            </select>
          </div>

          {/* Country Filter */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider block">Country / Eligibility</label>
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="w-full bg-neutral-950/60 border border-neutral-900 rounded-xl px-3 py-2.5 text-xs text-neutral-300 focus:border-indigo-500/80 focus:ring-1 focus:ring-indigo-500/80 transition-all outline-none"
            >
              <option value="All">All Regions</option>
              <option value="India">India</option>
              <option value="Europe">Europe (IN Eligible)</option>
              <option value="Global">Global Opportunities</option>
            </select>
          </div>

          {/* Funding Limit Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-baseline">
              <label className="text-xs font-semibold text-neutral-400 uppercase tracking-wider">Max Funding</label>
              <span className="text-xs font-mono font-semibold text-indigo-400">
                {maxFundingLimit >= 10000000 ? `₹${maxFundingLimit / 10000000} Cr` : `$${maxFundingLimit.toLocaleString()}`}
              </span>
            </div>
            <input
              type="range"
              min="100000"
              max="50000000"
              step="500000"
              value={maxFundingLimit}
              onChange={(e) => setMaxFundingLimit(parseInt(e.target.value))}
              className="w-full accent-indigo-500 h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Reset Filters button */}
          <button
            onClick={handleClearFilters}
            className="w-full py-2.5 bg-neutral-950 hover:bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition-all h-[42px]"
          >
            <FilterX size={14} />
            <span>Reset Filters</span>
          </button>
        </div>
      )}

      {/* Main Results View */}
      <div className="space-y-4">
        {debouncedQuery === '' ? (
          <div className="bg-neutral-900/10 border border-neutral-900 rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 backdrop-blur-sm min-h-[300px]">
            <div className="h-12 w-12 rounded-full bg-neutral-900 flex items-center justify-center text-neutral-500 mb-2">
              <Search size={20} />
            </div>
            <span className="text-neutral-300 text-sm font-semibold">Enter a Search Query</span>
            <p className="text-neutral-500 text-xs max-w-sm">
              Scan our vector databases by typing details of your project or keywords in the query bar above.
            </p>
          </div>
        ) : isLoading ? (
          <div className="flex flex-col items-center justify-center p-12 gap-3 min-h-[300px]">
            <Loader2 className="animate-spin text-indigo-500" size={32} />
            <span className="text-neutral-400 text-xs font-medium">Running hybrid search RRF rankings...</span>
          </div>
        ) : isError ? (
          <div className="bg-rose-500/5 border border-rose-500/10 rounded-2xl p-8 text-center flex flex-col items-center justify-center gap-2 min-h-[300px]">
            <Info className="text-rose-400" size={24} />
            <span className="text-neutral-300 text-sm font-semibold">Failed to retrieve search results</span>
            <span className="text-neutral-500 text-xs max-w-sm">{(error as any).message || 'Connection to backend API failed.'}</span>
          </div>
        ) : filteredResults.length === 0 ? (
          <div className="bg-neutral-900/10 border border-neutral-900 rounded-2xl p-12 text-center flex flex-col items-center justify-center gap-3 backdrop-blur-sm min-h-[300px]">
            <div className="h-12 w-12 rounded-full bg-neutral-900 flex items-center justify-center text-neutral-500 mb-2">
              <BookOpen size={20} />
            </div>
            <span className="text-neutral-300 text-sm font-semibold">No Grants Found</span>
            <p className="text-neutral-500 text-xs max-w-sm">
              We couldn't find any opportunities matching your criteria or active similarity thresholds. Try lowering the cutoff or resetting filters.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex justify-between items-center px-1">
              <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider">
                Showing {filteredResults.length} matching grants ({results.length} raw results found)
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredResults.map((grant) => {
                const isBookmarked = bookmarkedIds.has(grant.id);
                return (
                  <div 
                    key={grant.id}
                    className="bg-neutral-900/30 border border-neutral-900 hover:border-neutral-800 rounded-2xl p-6 backdrop-blur-sm flex flex-col justify-between shadow-xl relative group transition-all duration-300"
                  >
                    {/* Upper Card Info */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-start gap-4">
                        <h3 className="text-md font-bold text-neutral-200 group-hover:text-indigo-400 transition-colors line-clamp-1 leading-snug">
                          {grant.name}
                        </h3>
                        
                        {/* Bookmark Button */}
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            toggleBookmarkMutation.mutate(grant.id);
                          }}
                          disabled={toggleBookmarkMutation.isPending}
                          className={`p-2 rounded-lg border transition-all shrink-0 hover:scale-105 active:scale-95 ${
                            isBookmarked
                              ? 'bg-rose-600/10 border-rose-500/20 text-rose-400'
                              : 'bg-neutral-950/60 border-neutral-900 text-neutral-500 hover:text-rose-400 hover:border-rose-500/10'
                          }`}
                        >
                          <Bookmark size={14} fill={isBookmarked ? 'currentColor' : 'none'} />
                        </button>
                      </div>

                      <p className="text-neutral-400 text-xs leading-relaxed line-clamp-3">
                        {grant.description}
                      </p>
                    </div>

                    {/* Bottom stats details */}
                    <div className="mt-6 pt-4 border-t border-neutral-900 flex justify-between items-center text-xs">
                      <div className="flex items-center gap-1.5 text-neutral-200 font-semibold font-mono">
                        <DollarSign size={14} className="text-indigo-400" />
                        <span>
                          {formatFunding(grant.funding_amount_max, grant.currency)}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {/* Match Score label */}
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-semibold bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-mono">
                          Score: {grant.score}
                        </span>
                        
                        <Link 
                          href={`/dashboard/search/${grant.id}`}
                          className="text-xs text-indigo-400 hover:text-indigo-300 font-bold transition-colors"
                        >
                          View Details
                        </Link>
                      </div>
                    </div>

                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
