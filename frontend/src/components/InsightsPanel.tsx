import { useState, useEffect, useCallback } from 'react';
import { BarChart3, TrendingDown, Activity, AlertTriangle, MapPin, Shield, Users } from 'lucide-react';
import * as api from '../api';
import type { InsightsSummary } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

const PIE_COLORS = ['#ef4444', '#f59e0b', '#8b5cf6'];

export default function InsightsPanel() {
  const [data, setData] = useState<InsightsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [window, setWindow] = useState('last_hour');

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getInsights('Jaipur', window);
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [window]);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Activity size={20} className="animate-spin text-sky-500" />
      </div>
    );
  }

  if (!data) return null;

  const cancelData = [
    { name: 'Driver', value: data.total_driver_cancels },
    { name: 'Passenger', value: data.total_passenger_cancels },
    { name: 'Provider', value: data.total_provider_cancels },
  ];

  return (
    <div className="space-y-5">
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="text-sky-600" size={20} />
            <h2 className="text-lg font-bold text-slate-900">City Intelligence — {data.city}</h2>
          </div>
          <div className="flex items-center gap-1 bg-slate-50 rounded-lg p-0.5">
            {['last_hour', 'today'].map(w => (
              <button
                key={w}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  window === w ? 'bg-white text-sky-700 shadow-sm' : 'text-slate-500'
                }`}
                onClick={() => setWindow(w)}
              >
                {w === 'last_hour' ? '1 Hour' : 'Today'}
              </button>
            ))}
          </div>
        </div>

        {/* Top-Level KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Observed Rides', value: data.total_observed_rides, icon: <Activity size={18} className="text-sky-500" />, color: 'bg-sky-50' },
            { label: 'Eligible Requests', value: data.total_eligible_requests, icon: <Users size={18} className="text-emerald-500" />, color: 'bg-emerald-50' },
            { label: 'Driver Cancel Rate', value: data.avg_driver_cancel_rate != null ? `${(data.avg_driver_cancel_rate * 100).toFixed(1)}%` : 'N/A', icon: <TrendingDown size={18} className="text-rose-500" />, color: 'bg-rose-50' },
            { label: 'Pax Cancel Rate', value: data.avg_passenger_cancel_rate != null ? `${(data.avg_passenger_cancel_rate * 100).toFixed(1)}%` : 'N/A', icon: <AlertTriangle size={18} className="text-amber-500" />, color: 'bg-amber-50' },
          ].map((kpi, i) => (
            <div key={i} className={`${kpi.color} rounded-xl p-4`}>
              <div className="flex items-center gap-2 mb-2">{kpi.icon}</div>
              <div className="text-2xl font-bold text-slate-900">{kpi.value}</div>
              <div className="text-[11px] text-slate-500 mt-0.5">{kpi.label}</div>
            </div>
          ))}
        </div>

        {/* Cancellation Breakdown & Lists */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Pie Chart */}
          <div className="bg-slate-50/50 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-slate-700 mb-2">Cancellation Breakdown</h3>
            <div className="h-48">
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={cancelData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={65}
                    innerRadius={35}
                    strokeWidth={2}
                    stroke="#fff"
                  >
                    {cancelData.map((_, i) => (
                      <Cell key={i} fill={PIE_COLORS[i]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Cancel Hotspots */}
          <div className="bg-slate-50/50 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-slate-700 mb-3 flex items-center gap-1">
              <AlertTriangle size={12} className="text-rose-500" />
              Top Cancellation Hotspots
            </h3>
            <div className="space-y-2">
              {data.top_cancellation_hotspots.map((name, i) => (
                <div key={i} className="flex items-center gap-2 p-2.5 bg-white rounded-lg border border-slate-100">
                  <div className="w-5 h-5 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center text-[10px] font-bold">{i + 1}</div>
                  <span className="text-sm text-slate-700">{name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Top Availability Zones */}
          <div className="bg-slate-50/50 rounded-xl p-4">
            <h3 className="text-xs font-semibold text-slate-700 mb-3 flex items-center gap-1">
              <MapPin size={12} className="text-emerald-500" />
              Top Availability Zones
            </h3>
            <div className="space-y-2">
              {data.top_availability_zones.map((name, i) => (
                <div key={i} className="flex items-center gap-2 p-2.5 bg-white rounded-lg border border-slate-100">
                  <div className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center text-[10px] font-bold">{i + 1}</div>
                  <span className="text-sm text-slate-700">{name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Provenance */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm">
        <h3 className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
          <Shield size={12} className="text-indigo-500" />
          Data Provenance
        </h3>
        <div className="space-y-1.5">
          {Object.entries(data.provenance).map(([key, val]) => (
            <div key={key} className="flex gap-2 text-xs">
              <span className="font-medium text-slate-600 capitalize">{key.replace(/_/g, ' ')}:</span>
              <span className="text-slate-500">{val}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
