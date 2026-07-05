'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  LayoutDashboard, 
  Search, 
  Database, 
  User as UserIcon, 
  LogOut, 
  Menu, 
  X, 
  Loader2 
} from 'lucide-react';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // While checking authentication tokens, render a premium full-screen loader
  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col items-center justify-center gap-4">
        <Loader2 className="animate-spin text-indigo-500" size={40} />
        <span className="text-neutral-400 text-sm font-medium tracking-wide">Validating session...</span>
      </div>
    );
  }

  // If session failed and auth protection redirected, return null to prevent layout flicker
  if (!user) {
    return null;
  }

  const menuItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Grant Search', href: '/dashboard/search', icon: Search },
    { name: 'Ingestion Registry', href: '/dashboard/ingestion', icon: Database },
    { name: 'My Profile', href: '/dashboard/profile', icon: UserIcon },
  ];

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex font-sans relative overflow-hidden">
      
      {/* Background ambient lighting */}
      <div className="absolute top-[-30%] left-[-20%] w-[60%] h-[60%] bg-indigo-900/5 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-30%] right-[-20%] w-[60%] h-[60%] bg-violet-900/5 rounded-full blur-[140px] pointer-events-none" />

      {/* Desktop Sidebar */}
      <aside className="hidden md:flex flex-col w-64 bg-neutral-900/30 border-r border-neutral-900 backdrop-blur-md shrink-0 justify-between p-6 z-20">
        <div className="space-y-8">
          {/* Logo Brand Header */}
          <div className="flex items-center gap-3 px-2">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              G
            </div>
            <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-neutral-200 to-neutral-400 bg-clip-text text-transparent">
              GrantFinder
            </span>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {menuItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 font-semibold'
                      : 'border border-transparent text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/50'
                  }`}
                >
                  <Icon size={18} />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card & Logout Footer */}
        <div className="pt-6 border-t border-neutral-900 space-y-4">
          <div className="flex items-center gap-3 px-2">
            <div className="h-9 w-9 rounded-xl bg-neutral-800 flex items-center justify-center font-semibold text-neutral-300">
              {user.email.substring(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-neutral-300 truncate">{user.email}</p>
              <p className="text-[10px] text-neutral-500 font-mono">Active Account</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-3 border border-transparent hover:bg-rose-500/5 hover:border-rose-500/10 text-neutral-400 hover:text-rose-400 rounded-xl text-sm font-medium transition-all"
          >
            <LogOut size={18} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header Bar */}
      <div className="flex flex-col flex-1 min-w-0">
        <header className="md:hidden flex items-center justify-between h-16 px-6 bg-neutral-950/80 border-b border-neutral-900 sticky top-0 z-30 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center font-bold text-white shadow-md">
              G
            </div>
            <span className="font-bold tracking-tight text-white">GrantFinder</span>
          </div>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 border border-neutral-800 rounded-lg text-neutral-400 hover:text-white"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </header>

        {/* Mobile Slideout Nav Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 bg-neutral-950 z-40 flex flex-col p-6 pt-20">
            <button
              onClick={() => setMobileMenuOpen(false)}
              className="absolute top-4 right-6 p-1.5 border border-neutral-800 rounded-lg text-neutral-400"
            >
              <X size={20} />
            </button>

            <nav className="space-y-2 mb-8">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3.5 rounded-xl text-sm font-medium transition-all ${
                      isActive
                        ? 'bg-indigo-600/10 border border-indigo-500/25 text-indigo-400'
                        : 'border border-transparent text-neutral-400 hover:bg-neutral-900/50'
                    }`}
                  >
                    <Icon size={18} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="mt-auto border-t border-neutral-900 pt-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-xl bg-neutral-800 flex items-center justify-center font-semibold text-neutral-300">
                  {user.email.substring(0, 2).toUpperCase()}
                </div>
                <div>
                  <p className="text-xs font-semibold text-neutral-300">{user.email}</p>
                  <p className="text-[10px] text-neutral-500">Active Account</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  logout();
                }}
                className="w-full flex items-center justify-center gap-3 px-4 py-3.5 bg-rose-500/10 text-rose-400 rounded-xl text-sm font-semibold border border-rose-500/20"
              >
                <LogOut size={18} />
                <span>Sign Out</span>
              </button>
            </div>
          </div>
        )}

        {/* Dynamic Inner Page Workspace */}
        <main className="flex-1 overflow-y-auto p-6 md:p-10 relative z-10 w-full max-w-7xl mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
