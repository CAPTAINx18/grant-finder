'use client';

import React from 'react';
import { useAuth } from '@/context/AuthContext';
import { User, Mail, Shield, Calendar, LogOut, Info } from 'lucide-react';

export default function ProfilePage() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="space-y-8">
      
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Account Configuration</h1>
        <p className="text-neutral-400 text-sm mt-1">Review active credentials, roles, and platform settings.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Card: Account Card */}
        <div className="lg:col-span-2 bg-neutral-900/20 border border-neutral-900 rounded-3xl p-6 md:p-8 backdrop-blur-sm space-y-6">
          <h3 className="text-lg font-bold text-white tracking-tight">Personal Information</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Email field */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider block">Registered Email</span>
              <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl px-4 py-3 text-sm text-neutral-200 flex items-center gap-2">
                <Mail size={16} className="text-neutral-500" />
                <span className="truncate">{user.email}</span>
              </div>
            </div>

            {/* Account ID field */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider block">User Identifier</span>
              <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl px-4 py-3 text-xs text-neutral-300 font-mono flex items-center gap-2">
                <User size={16} className="text-neutral-500" />
                <span className="truncate">{user.id}</span>
              </div>
            </div>

            {/* Account Role field */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider block">Account Role</span>
              <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl px-4 py-3 text-sm text-neutral-200 flex items-center gap-2">
                <Shield size={16} className="text-neutral-500" />
                <span>{user.is_admin ? 'Platform Administrator (Admin)' : 'Standard Platform User'}</span>
              </div>
            </div>

            {/* Created At field */}
            <div className="space-y-1">
              <span className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider block">Registered Since</span>
              <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl px-4 py-3 text-sm text-neutral-200 flex items-center gap-2">
                <Calendar size={16} className="text-neutral-500" />
                <span>{new Date(user.created_at).toLocaleDateString(undefined, { dateStyle: 'long' })}</span>
              </div>
            </div>

          </div>
        </div>

        {/* Right Card: Quick Actions */}
        <div className="bg-neutral-900/20 border border-neutral-900 rounded-3xl p-6 backdrop-blur-sm space-y-6">
          <h3 className="text-lg font-bold text-white tracking-tight">Security Actions</h3>
          
          <div className="space-y-4">
            
            {/* Quick tips panel */}
            <div className="bg-neutral-950/60 border border-neutral-900 rounded-xl p-4 flex gap-3 text-xs">
              <Info className="text-indigo-400 shrink-0 mt-0.5" size={16} />
              <div className="space-y-1">
                <h5 className="font-semibold text-neutral-300">Identity Security</h5>
                <p className="text-[10px] text-neutral-500 leading-relaxed">
                  Your session JWT tokens automatically cycle and refresh behind the scenes. Logging out removes all credentials from client local storage.
                </p>
              </div>
            </div>

            {/* Explicit logout button */}
            <button
              onClick={logout}
              className="w-full flex items-center justify-center gap-2 px-4 py-3.5 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 rounded-xl text-xs font-semibold transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <LogOut size={14} />
              <span>Log Out of System</span>
            </button>
            
          </div>
        </div>

      </div>

    </div>
  );
}
