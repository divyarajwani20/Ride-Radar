import { useState, useEffect } from 'react';
import { Beaker, Play, CheckCircle, Activity, Tag } from 'lucide-react';
import * as api from '../api';
import type { DemoScenario } from '../types';

const CAT_COLORS: Record<string, string> = {
  ride_comparison: 'bg-sky-50 text-sky-700 border-sky-200',
  hot_zones: 'bg-amber-50 text-amber-700 border-amber-200',
  priority_dispatch: 'bg-rose-50 text-rose-700 border-rose-200',
  reliability: 'bg-violet-50 text-violet-700 border-violet-200',
  forecasting: 'bg-teal-50 text-teal-700 border-teal-200',
};

export default function DemoScenarios() {
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [activating, setActivating] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.getDemoScenarios().then(setScenarios).catch(() => {});
  }, []);

  const activate = async (id: string) => {
    setActivating(id);
    setMessage('');
    try {
      const res = await api.activateScenario(id);
      setActiveId(id);
      setMessage(res.message);
    } catch (e: unknown) {
      setMessage(e instanceof Error ? e.message : 'Activation failed');
    } finally {
      setActivating(null);
    }
  };

  return (
    <div className="space-y-5">
      <div className="bg-gradient-to-r from-indigo-600 to-violet-600 rounded-2xl p-5 text-white shadow-lg shadow-indigo-200/50">
        <div className="flex items-center gap-2 mb-1">
          <Beaker size={22} />
          <h2 className="text-lg font-bold">Demo Scenarios</h2>
        </div>
        <p className="text-indigo-100 text-sm">14 repeatable test scenarios with deterministic seed data</p>
      </div>

      {message && (
        <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-700">
          <CheckCircle size={16} /> {message}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {scenarios.map(s => (
          <div
            key={s.id}
            className={`bg-white rounded-xl border p-4 transition-all ${
              activeId === s.id ? 'border-indigo-300 ring-2 ring-indigo-100 shadow-md' : 'border-slate-200/80 hover:shadow-md'
            }`}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm text-slate-900 truncate">{s.name}</div>
                <span className={`inline-flex items-center gap-1 px-2 py-0.5 mt-1 rounded-full text-[10px] font-medium border ${CAT_COLORS[s.category] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
                  <Tag size={9} /> {s.category.replace(/_/g, ' ')}
                </span>
              </div>
              {activeId === s.id && <CheckCircle size={16} className="text-emerald-500 shrink-0" />}
            </div>
            <p className="text-xs text-slate-500 mb-2 line-clamp-2">{s.description}</p>
            <p className="text-[11px] text-slate-400 mb-3 italic">Expected: {s.expected_outcome}</p>
            <button
              className={`w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                activeId === s.id
                  ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                  : 'bg-slate-50 text-slate-700 hover:bg-sky-50 hover:text-sky-700 border border-slate-200'
              }`}
              onClick={() => activate(s.id)}
              disabled={activating === s.id}
            >
              {activating === s.id ? <Activity size={12} className="animate-spin" /> : <Play size={12} />}
              {activeId === s.id ? 'Re-activate' : 'Activate'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
