import { useState, useEffect } from 'react';
import { Radar, Navigation, Flame, BarChart3, Zap, Beaker, Heart, Wifi, WifiOff, Menu, X } from 'lucide-react';
import RideCompare from './components/RideCompare';
import HotZoneMap from './components/HotZoneMap';
import InsightsPanel from './components/InsightsPanel';
import PriorityDispatch from './components/PriorityDispatch';
import DemoScenarios from './components/DemoScenarios';
import * as api from './api';

type Tab = 'rides' | 'hotZones' | 'insights' | 'priority' | 'demo';

const TABS: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: 'rides', label: 'Compare', icon: <Navigation size={18} /> },
  { id: 'hotZones', label: 'Hot Zones', icon: <Flame size={18} /> },
  { id: 'insights', label: 'Insights', icon: <BarChart3 size={18} /> },
  { id: 'priority', label: 'Priority', icon: <Zap size={18} /> },
  { id: 'demo', label: 'Scenarios', icon: <Beaker size={18} /> },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('rides');
  const [online, setOnline] = useState<boolean | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    api.getHealth()
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50/80">
      {/* Top Nav */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/60 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-500 to-indigo-600 flex items-center justify-center shadow-md shadow-sky-200/50">
                <Radar size={18} className="text-white" />
              </div>
              <div>
                <span className="font-bold text-slate-900 text-base tracking-tight">RideRadar</span>
                <span className="hidden sm:inline text-[10px] text-slate-400 ml-1.5 font-medium">Jaipur</span>
              </div>
            </div>

            {/* Desktop Tabs */}
            <nav className="hidden md:flex items-center gap-1">
              {TABS.map(t => (
                <button
                  key={t.id}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                    tab === t.id
                      ? 'bg-sky-50 text-sky-700 shadow-sm'
                      : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                  }`}
                  onClick={() => setTab(t.id)}
                >
                  {t.icon}
                  {t.label}
                </button>
              ))}
            </nav>

            {/* Status + Mobile Toggle */}
            <div className="flex items-center gap-3">
              {online !== null && (
                <div className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] font-medium ${
                  online ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-600'
                }`}>
                  {online ? <Wifi size={10} /> : <WifiOff size={10} />}
                  {online ? 'API Online' : 'Offline'}
                </div>
              )}
              <span className="hidden sm:flex items-center gap-1 px-2 py-1 bg-indigo-50 text-indigo-600 rounded-full text-[10px] font-medium">
                <Heart size={9} /> Demo
              </span>

              {/* Mobile Menu Button */}
              <button
                className="md:hidden p-1.5 rounded-lg hover:bg-slate-100 transition"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
              </button>
            </div>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <nav className="md:hidden pb-3 border-t border-slate-100 pt-2 space-y-1">
              {TABS.map(t => (
                <button
                  key={t.id}
                  className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                    tab === t.id ? 'bg-sky-50 text-sky-700' : 'text-slate-500 hover:bg-slate-50'
                  }`}
                  onClick={() => { setTab(t.id); setMobileMenuOpen(false); }}
                >
                  {t.icon} {t.label}
                </button>
              ))}
            </nav>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-5">
        {/* Offline Banner */}
        {online === false && (
          <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-700">
            <WifiOff size={16} />
            Backend is offline. Start it with: <code className="px-1.5 py-0.5 bg-amber-100 rounded text-xs font-mono">cd backend && uvicorn app.main:app --reload</code>
          </div>
        )}

        {tab === 'rides' && <RideCompare />}
        {tab === 'hotZones' && <HotZoneMap />}
        {tab === 'insights' && <InsightsPanel />}
        {tab === 'priority' && <PriorityDispatch />}
        {tab === 'demo' && <DemoScenarios />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200/60 bg-white/50 backdrop-blur mt-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between text-[11px] text-slate-400">
          <span>RideRadar v1.0 · Jaipur Demo · No real booking</span>
          <span className="flex items-center gap-1">
            <Heart size={9} className="text-rose-400" /> Built with transparency
          </span>
        </div>
      </footer>
    </div>
  );
}
