import { useState, useEffect, useCallback } from 'react';
import { MapPin, Clock, Star, AlertTriangle, TrendingUp, Shield, Navigation, ChevronDown, RefreshCw, Zap, Activity } from 'lucide-react';
import * as api from '../api';
import type { RideOption, RideCompareResponse } from '../types';

const SORT_OPTIONS = [
  { value: 'best_overall', label: 'Best Overall', icon: <TrendingUp size={14} /> },
  { value: 'best_driver_rating', label: 'Best Driver', icon: <Star size={14} /> },
  { value: 'lowest_fare', label: 'Lowest Fare', icon: <Navigation size={14} /> },
  { value: 'fastest_pickup', label: 'Fastest Pickup', icon: <Clock size={14} /> },
];

const CATEGORIES = ['all', 'bike', 'auto', 'economy', 'sedan', 'suv'];

const PROVIDER_COLORS: Record<string, string> = {
  Uber: '#000000',
  Ola: '#4CAF50',
  Rapido: '#FFAB00',
  Demo: '#6366f1',
};

function getProviderGradient(name: string) {
  const c = PROVIDER_COLORS[name] || '#6366f1';
  return `linear-gradient(135deg, ${c}18, ${c}08)`;
}

function ConfidenceBadge({ label }: { label: string }) {
  const colors: Record<string, string> = {
    high: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    medium: 'bg-amber-50 text-amber-700 border-amber-200',
    low: 'bg-red-50 text-red-700 border-red-200',
  };
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium border ${colors[label] || colors.low}`}>
      <Shield size={10} /> {label}
    </span>
  );
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-slate-500 text-[11px]">{label}</span>
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="w-8 text-right font-mono text-[11px] text-slate-600">{Math.round(value)}</span>
    </div>
  );
}

function RideCard({ option, rank }: { option: RideOption; rank: number }) {
  const [expanded, setExpanded] = useState(false);
  const driver = option.driver;
  const sb = option.score_breakdown;

  return (
    <div
      className="group relative bg-white rounded-xl border border-slate-200/80 hover:border-sky-300 hover:shadow-lg transition-all duration-300 overflow-hidden cursor-pointer"
      onClick={() => setExpanded(!expanded)}
      style={{ background: getProviderGradient(option.provider) }}
    >
      {rank === 1 && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-sky-500 via-teal-400 to-emerald-400" />
      )}

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center w-8 h-8 rounded-lg text-sm font-bold text-white"
              style={{ background: PROVIDER_COLORS[option.provider] || '#6366f1' }}>
              {rank}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900">{option.provider}</span>
                <span className="px-1.5 py-0.5 bg-slate-100 text-slate-500 text-[10px] font-medium rounded">{option.ride_type}</span>
              </div>
              {driver && (
                <div className="flex items-center gap-1 mt-0.5 text-xs text-slate-500">
                  <Star size={11} className="text-amber-400 fill-amber-400" />
                  <span className="font-medium text-slate-700">{driver.adjusted_rating.toFixed(2)}</span>
                  <span>({driver.rating_count} trips)</span>
                  <span className="mx-1">·</span>
                  <span>{driver.display_name}</span>
                </div>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-slate-900">
              ₹{option.estimated_fare ?? '—'}
            </div>
            <div className="text-xs text-slate-500">
              {option.pickup_eta_minutes ? `${option.pickup_eta_minutes} min away` : 'ETA N/A'}
            </div>
          </div>
        </div>

        {/* Score + Confidence */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 px-2 py-1 bg-sky-50 text-sky-700 rounded-lg">
              <Zap size={12} />
              <span className="text-sm font-bold">{option.score.toFixed(1)}</span>
            </div>
            <ConfidenceBadge label={option.confidence} />
          </div>
          <ChevronDown size={16} className={`text-slate-400 transition-transform ${expanded ? 'rotate-180' : ''}`} />
        </div>

        {/* Expanded Details */}
        {expanded && (
          <div className="mt-4 pt-3 border-t border-slate-100 space-y-3 animate-in">
            <p className="text-xs text-slate-600 italic leading-relaxed">{option.ranking_explanation}</p>

            <div className="space-y-1.5">
              <ScoreBar label="Rating" value={sb.rating} color="#0ea5e9" />
              <ScoreBar label="Reliability" value={sb.reliability} color="#10b981" />
              <ScoreBar label="ETA" value={sb.eta} color="#f59e0b" />
              <ScoreBar label="Fare" value={sb.fare} color="#8b5cf6" />
              <ScoreBar label="Freshness" value={sb.freshness} color="#6366f1" />
            </div>

            {driver && (
              <div className="flex flex-wrap gap-2 text-[11px]">
                <span className="px-2 py-1 bg-slate-50 rounded text-slate-600">
                  Cancel rate: {(driver.smoothed_driver_cancel_rate * 100).toFixed(1)}%
                </span>
                {driver.vehicle_model && (
                  <span className="px-2 py-1 bg-slate-50 rounded text-slate-600">
                    {driver.vehicle_model}
                  </span>
                )}
                <span className="px-2 py-1 bg-slate-50 rounded text-slate-600">
                  {driver.confidence_label}
                </span>
              </div>
            )}

            <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
              <Activity size={10} />
              Source: {option.source_type} · {new Date(option.observed_at).toLocaleTimeString()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function RideCompare() {
  const [origin, setOrigin] = useState('zone_sms_hospital');
  const [destination, setDestination] = useState('zone_c_scheme');
  const [sortBy, setSortBy] = useState('best_overall');
  const [category, setCategory] = useState('all');
  const [data, setData] = useState<RideCompareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchRides = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await api.compareRides(origin, destination, sortBy, category);
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to compare rides');
    } finally {
      setLoading(false);
    }
  }, [origin, destination, sortBy, category]);

  useEffect(() => { fetchRides(); }, [fetchRides]);

  return (
    <div className="space-y-5">
      {/* Search Controls */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Navigation className="text-sky-600" size={20} />
          <h2 className="text-lg font-bold text-slate-900">Compare Rides</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 mb-4 items-end">
          <div className="sm:col-span-5">
            <label className="block text-xs font-medium text-slate-500 mb-1">Pickup Zone (Jaipur)</label>
            <div className="relative">
              <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-emerald-500 z-10" />
              <select
                id="pickup-zone"
                className="w-full pl-8 pr-3 py-2.5 rounded-lg border border-slate-200 bg-slate-50/50 text-sm focus:ring-2 focus:ring-sky-200 focus:border-sky-400 transition"
                value={origin}
                onChange={e => setOrigin(e.target.value)}
              >
                <option value="zone_sms_hospital">SMS Medical Hospital & Trauma</option>
                <option value="zone_jaipur_junction">Jaipur Junction Railway Station</option>
                <option value="zone_airport">Jaipur International Airport (JAI)</option>
                <option value="zone_c_scheme">C-Scheme Central Business District</option>
                <option value="zone_apex_hospital">Apex & EHCC Hospital Corridor</option>
                <option value="zone_malviya_nagar">Malviya Nagar Tech & Retail Hub</option>
                <option value="zone_mansarovar">Mansarovar Metro Terminus</option>
                <option value="zone_vaishali_nagar">Vaishali Nagar Amrapali Circle</option>
                <option value="zone_raja_park">Raja Park Shopping Promenade</option>
              </select>
            </div>
          </div>

          <div className="sm:col-span-2 flex justify-center">
            <button
              type="button"
              title="Swap pickup and destination"
              onClick={() => {
                const temp = origin;
                setOrigin(destination);
                setDestination(temp);
              }}
              className="p-2.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-500 transition-colors"
            >
              ⇄
            </button>
          </div>

          <div className="sm:col-span-5">
            <label className="block text-xs font-medium text-slate-500 mb-1">Destination Zone (Jaipur)</label>
            <div className="relative">
              <MapPin size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-rose-500 z-10" />
              <select
                id="destination-zone"
                className="w-full pl-8 pr-3 py-2.5 rounded-lg border border-slate-200 bg-slate-50/50 text-sm focus:ring-2 focus:ring-sky-200 focus:border-sky-400 transition"
                value={destination}
                onChange={e => setDestination(e.target.value)}
              >
                <option value="zone_c_scheme">C-Scheme Central Business District</option>
                <option value="zone_sms_hospital">SMS Medical Hospital & Trauma</option>
                <option value="zone_jaipur_junction">Jaipur Junction Railway Station</option>
                <option value="zone_airport">Jaipur International Airport (JAI)</option>
                <option value="zone_apex_hospital">Apex & EHCC Hospital Corridor</option>
                <option value="zone_malviya_nagar">Malviya Nagar Tech & Retail Hub</option>
                <option value="zone_mansarovar">Mansarovar Metro Terminus</option>
                <option value="zone_vaishali_nagar">Vaishali Nagar Amrapali Circle</option>
                <option value="zone_raja_park">Raja Park Shopping Promenade</option>
              </select>
            </div>
          </div>
        </div>

        {/* Quick Jaipur Trip Presets */}
        <div className="flex flex-wrap items-center gap-1.5 mb-4 text-xs">
          <span className="text-slate-400 text-[11px] font-medium mr-1">Popular:</span>
          {[
            { label: 'Airport ✈️ → C-Scheme', orig: 'zone_airport', dest: 'zone_c_scheme' },
            { label: 'Junction 🚆 → SMS Hospital', orig: 'zone_jaipur_junction', dest: 'zone_sms_hospital' },
            { label: 'Mansarovar 🚇 → Malviya Nagar', orig: 'zone_mansarovar', dest: 'zone_malviya_nagar' },
            { label: 'Vaishali Nagar 🛍️ → C-Scheme', orig: 'zone_vaishali_nagar', dest: 'zone_c_scheme' },
          ].map(p => (
            <button
              key={p.label}
              type="button"
              className="px-2 py-1 rounded-md bg-slate-100 hover:bg-sky-50 hover:text-sky-700 text-slate-600 text-[11px] transition-colors"
              onClick={() => {
                setOrigin(p.orig);
                setDestination(p.dest);
              }}
            >
              {p.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Sort Options */}
          <div className="flex items-center gap-1 bg-slate-50 rounded-lg p-0.5">
            {SORT_OPTIONS.map(s => (
              <button
                key={s.value}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  sortBy === s.value
                    ? 'bg-white text-sky-700 shadow-sm'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
                onClick={() => setSortBy(s.value)}
              >
                {s.icon} {s.label}
              </button>
            ))}
          </div>

          {/* Category */}
          <select
            id="ride-category"
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs bg-white"
            value={category}
            onChange={e => setCategory(e.target.value)}
          >
            {CATEGORIES.map(c => (
              <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
            ))}
          </select>

          <button
            id="compare-btn"
            className="ml-auto flex items-center gap-1.5 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
            onClick={fetchRides}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            {loading ? 'Comparing…' : 'Compare'}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700">
          <AlertTriangle size={16} /> {error}
        </div>
      )}

      {/* Summary Strip */}
      {data && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: 'Options Found', value: data.summary.total_options, icon: <Activity size={16} className="text-sky-500" /> },
            { label: 'Best Driver', value: data.summary.best_rated_driver?.toFixed(1) ?? '—', icon: <Star size={16} className="text-amber-400 fill-amber-400" /> },
            { label: 'Lowest Fare', value: data.summary.lowest_estimated_fare ? `₹${data.summary.lowest_estimated_fare}` : '—', icon: <TrendingUp size={16} className="text-emerald-500" /> },
            { label: 'Fastest ETA', value: data.summary.fastest_pickup_eta ? `${data.summary.fastest_pickup_eta} min` : '—', icon: <Clock size={16} className="text-violet-500" /> },
          ].map((s, i) => (
            <div key={i} className="flex items-center gap-3 bg-white rounded-xl border border-slate-200/80 p-3.5 shadow-sm">
              {s.icon}
              <div>
                <div className="text-[11px] text-slate-500">{s.label}</div>
                <div className="text-lg font-bold text-slate-900">{s.value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Ride Cards */}
      {data && (
        <div className="space-y-3">
          {data.options.map((opt, i) => (
            <RideCard key={opt.id} option={opt} rank={i + 1} />
          ))}
        </div>
      )}

      {/* Demo Notice */}
      {data?.is_demo && (
        <div className="flex items-start gap-2 px-4 py-3 bg-indigo-50/60 border border-indigo-100 rounded-xl text-xs text-indigo-600">
          <AlertTriangle size={14} className="mt-0.5 shrink-0" />
          <span>{data.demo_notice}</span>
        </div>
      )}
    </div>
  );
}
