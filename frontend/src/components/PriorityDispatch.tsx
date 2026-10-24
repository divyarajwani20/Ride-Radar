import { useState, useEffect } from 'react';
import { Zap, Shield, Clock, MapPin, AlertTriangle, CheckCircle, Activity, Truck, Bus, Navigation } from 'lucide-react';
import * as api from '../api';
import type { PriorityQuoteResponse, PriorityStatusResponse, PriorityZone } from '../types';

const URGENCY_CATEGORIES = [
  { value: 'medical', label: 'Medical Emergency', icon: <Zap size={14} />, color: 'text-rose-600' },
  { value: 'transit_connection', label: 'Transit Connection', icon: <Bus size={14} />, color: 'text-amber-600' },
  { value: 'urgent_meeting', label: 'Urgent Meeting', icon: <Clock size={14} />, color: 'text-sky-600' },
  { value: 'general_priority', label: 'General Priority', icon: <Shield size={14} />, color: 'text-violet-600' },
];

const STATUS_COLORS: Record<string, string> = {
  quoted: 'bg-sky-50 text-sky-700 border-sky-200',
  searching: 'bg-amber-50 text-amber-700 border-amber-200',
  driver_offered: 'bg-blue-50 text-blue-700 border-blue-200',
  driver_accepted: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  driver_arriving: 'bg-teal-50 text-teal-700 border-teal-200',
  completed: 'bg-green-50 text-green-700 border-green-200',
  unavailable: 'bg-red-50 text-red-700 border-red-200',
  cancelled: 'bg-slate-50 text-slate-700 border-slate-200',
  retrying: 'bg-orange-50 text-orange-700 border-orange-200',
};

const TIMELINE_STEPS = ['Quoted', 'Searching', 'Contacting', 'Accepted', 'Arriving', 'Complete'];

function TimelineBar({ step }: { step: number }) {
  return (
    <div className="flex items-center gap-1 mb-6">
      {TIMELINE_STEPS.map((label, i) => (
        <div key={i} className="flex-1 flex flex-col items-center">
          <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold mb-1 transition-all ${
            i <= step ? 'bg-sky-600 text-white shadow-md shadow-sky-200' : 'bg-slate-100 text-slate-400'
          }`}>
            {i < step ? '✓' : i + 1}
          </div>
          <div className={`text-[9px] font-medium ${i <= step ? 'text-sky-700' : 'text-slate-400'}`}>{label}</div>
          {i < TIMELINE_STEPS.length - 1 && (
            <div className={`h-0.5 w-full mt-2 ${i < step ? 'bg-sky-400' : 'bg-slate-200'}`} />
          )}
        </div>
      ))}
    </div>
  );
}

export default function PriorityDispatch() {
  const [zones, setZones] = useState<PriorityZone[]>([]);
  const [pickupZone, setPickupZone] = useState('');
  const [destZone, setDestZone] = useState('zone_c_scheme');
  const [urgency, setUrgency] = useState('medical');
  const [quote, setQuote] = useState<PriorityQuoteResponse | null>(null);
  const [dispatchResult, setDispatchResult] = useState<PriorityStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'zones' | 'quote' | 'dispatch'>('zones');

  useEffect(() => {
    api.getPriorityZones().then(z => {
      setZones(z);
      if (z.length > 0) setPickupZone(z[0].zone_id);
    });
  }, []);

  const handleQuote = async () => {
    setLoading(true);
    try {
      const q = await api.requestPriorityQuote(pickupZone, destZone, urgency);
      setQuote(q);
      setStep('quote');
    } finally {
      setLoading(false);
    }
  };

  const handleDispatch = async (simulate?: string) => {
    if (!quote) return;
    setLoading(true);
    try {
      const result = await api.dispatchPriority(
        quote.request_id,
        `key_${Date.now()}`,
        simulate
      );
      setDispatchResult(result);
      setStep('dispatch');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="bg-gradient-to-r from-sky-600 to-indigo-600 rounded-2xl p-5 text-white shadow-lg shadow-sky-200/50">
        <div className="flex items-center gap-2 mb-1">
          <Zap size={22} />
          <h2 className="text-lg font-bold">Emergency Priority Dispatch</h2>
        </div>
        <p className="text-sky-100 text-sm">Designated high-need zones · Transparent pricing · Guaranteed fallback</p>
      </div>

      {/* Zone Selection */}
      {step === 'zones' && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2">
            <MapPin size={16} className="text-rose-500" />
            Select Priority Pickup Zone
          </h3>

          {/* Priority Zones Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {zones.map(z => (
              <div
                key={z.zone_id}
                className={`p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                  pickupZone === z.zone_id
                    ? 'border-sky-400 bg-sky-50 shadow-md shadow-sky-100'
                    : 'border-slate-200 hover:border-sky-200 hover:bg-sky-50/30'
                }`}
                onClick={() => setPickupZone(z.zone_id)}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-medium text-sm text-slate-900">{z.zone_name}</div>
                    <div className="text-[11px] text-slate-500 mt-0.5 capitalize">{z.category?.replace(/_/g, ' ')}</div>
                  </div>
                  {z.is_enabled && (
                    <span className="px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] font-medium rounded-full border border-emerald-200">Active</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Destination */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-1">Destination Zone</label>
            <input
              className="w-full px-3 py-2.5 rounded-lg border border-slate-200 bg-slate-50/50 text-sm focus:ring-2 focus:ring-sky-200"
              value={destZone}
              onChange={e => setDestZone(e.target.value)}
            />
          </div>

          {/* Urgency */}
          <div>
            <label className="block text-xs font-medium text-slate-500 mb-2">Urgency Category</label>
            <div className="grid grid-cols-2 gap-2">
              {URGENCY_CATEGORIES.map(u => (
                <button
                  key={u.value}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border-2 text-sm font-medium transition-all ${
                    urgency === u.value
                      ? 'border-sky-400 bg-sky-50 text-sky-700'
                      : 'border-slate-200 text-slate-600 hover:border-sky-200'
                  }`}
                  onClick={() => setUrgency(u.value)}
                >
                  <span className={u.color}>{u.icon}</span>
                  {u.label}
                </button>
              ))}
            </div>
          </div>

          <button
            className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-sky-600 hover:bg-sky-700 text-white font-medium rounded-xl shadow-sm transition-colors"
            onClick={handleQuote}
            disabled={loading || !pickupZone}
          >
            {loading ? <Activity size={16} className="animate-spin" /> : <Navigation size={16} />}
            Get Priority Quote
          </button>
        </div>
      )}

      {/* Quote Display */}
      {step === 'quote' && quote && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-900 flex items-center gap-2">
              <Shield size={16} className="text-emerald-500" />
              Priority Quote
            </h3>
            <button onClick={() => setStep('zones')} className="text-xs text-slate-500 hover:text-sky-600 transition">← Back</button>
          </div>

          {/* Fare Breakdown */}
          <div className="bg-gradient-to-br from-slate-50 to-sky-50/30 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Base Estimate</span>
              <span className="font-semibold text-slate-900">₹{quote.base_estimate}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Priority Fee</span>
              <span className="font-semibold text-amber-600">₹{quote.priority_fee}</span>
            </div>
            <div className="border-t border-slate-200 pt-3 flex items-center justify-between">
              <span className="font-bold text-slate-900">Total Payable</span>
              <span className="text-2xl font-bold text-sky-700">₹{quote.total_payable}</span>
            </div>
          </div>

          {/* Details */}
          <div className="space-y-2.5 text-sm">
            <div className="flex items-start gap-2">
              <MapPin size={14} className="text-emerald-500 mt-0.5 shrink-0" />
              <div>
                <span className="font-medium text-slate-700">{quote.pickup_zone_name}</span>
                {quote.is_designated_priority_zone && (
                  <span className="ml-2 px-2 py-0.5 bg-violet-50 text-violet-700 text-[10px] rounded-full border border-violet-200">
                    Verified {quote.priority_category?.replace(/_/g, ' ')}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Clock size={14} className="text-sky-500 mt-0.5 shrink-0" />
              <span className="text-slate-600">ETA: {quote.estimated_pickup_range_min}–{quote.estimated_pickup_range_max} minutes</span>
            </div>
            <div className="flex items-start gap-2">
              <Shield size={14} className="text-indigo-500 mt-0.5 shrink-0" />
              <span className="text-slate-600 text-xs">{quote.refund_terms}</span>
            </div>
          </div>

          <p className="text-xs text-slate-500 italic">{quote.eligibility_explanation}</p>

          {/* Dispatch Actions */}
          <div className="space-y-2">
            <button
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-xl transition-colors"
              onClick={() => handleDispatch()}
              disabled={loading}
            >
              {loading ? <Activity size={16} className="animate-spin" /> : <Zap size={16} />}
              Accept & Dispatch
            </button>

            <div className="grid grid-cols-2 gap-2">
              <button
                className="px-3 py-2 bg-amber-50 hover:bg-amber-100 text-amber-700 text-xs font-medium rounded-lg border border-amber-200 transition"
                onClick={() => handleDispatch('force_decline')}
                disabled={loading}
              >
                Simulate: Decline → Retry
              </button>
              <button
                className="px-3 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 text-xs font-medium rounded-lg border border-rose-200 transition"
                onClick={() => handleDispatch('force_all_fail')}
                disabled={loading}
              >
                Simulate: All Fail
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dispatch Result */}
      {step === 'dispatch' && dispatchResult && (
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-5">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-slate-900">Dispatch Status</h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${STATUS_COLORS[dispatchResult.status] || STATUS_COLORS.searching}`}>
              {dispatchResult.status.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>

          {/* Timeline */}
          <TimelineBar step={dispatchResult.status_timeline_step} />

          {/* Message */}
          <div className="p-3.5 bg-sky-50 rounded-xl text-sm text-sky-800 border border-sky-100">
            {dispatchResult.message}
          </div>

          {/* Confirmed Driver */}
          {dispatchResult.confirmed_driver && (
            <div className="bg-emerald-50/50 rounded-xl p-4 border border-emerald-100">
              <h4 className="text-xs font-semibold text-emerald-800 mb-2 flex items-center gap-1">
                <CheckCircle size={12} /> Confirmed Driver
              </h4>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-200 rounded-full flex items-center justify-center text-emerald-700 font-bold text-sm">
                  {dispatchResult.confirmed_driver.display_name.charAt(0)}
                </div>
                <div>
                  <div className="font-medium text-slate-900">{dispatchResult.confirmed_driver.display_name}</div>
                  <div className="text-xs text-slate-500">
                    ⭐ {dispatchResult.confirmed_driver.adjusted_rating.toFixed(2)} · {dispatchResult.confirmed_driver.vehicle_model}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Candidate Ranking */}
          {dispatchResult.candidate_ranking.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-700 mb-2">Candidate Ranking</h4>
              <div className="space-y-2">
                {dispatchResult.candidate_ranking.map((c, i) => (
                  <div key={c.driver_id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="w-6 h-6 rounded-full bg-sky-100 text-sky-700 flex items-center justify-center text-[11px] font-bold">
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-slate-800">{c.driver_name}</div>
                      <div className="text-[11px] text-slate-500">
                        Score: {c.score.toFixed(1)} · {c.eta_minutes}min · {c.distance_km}km · {(c.reliability_rate * 100).toFixed(0)}% reliable
                      </div>
                    </div>
                    <span className="text-[10px] text-slate-500 shrink-0">{c.vehicle}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Attempt History */}
          {dispatchResult.attempt_history.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-700 mb-2">Attempt Ledger</h4>
              <div className="space-y-1.5">
                {dispatchResult.attempt_history.map((a, i) => (
                  <div key={i} className="flex items-center gap-2 p-2.5 bg-slate-50 rounded-lg text-xs">
                    <span className="font-mono text-slate-400">#{a.attempt_number}</span>
                    <span className="font-medium text-slate-700">{a.driver_name}</span>
                    <span className={`ml-auto px-2 py-0.5 rounded-full text-[10px] font-medium ${
                      a.outcome === 'accepted' ? 'bg-emerald-50 text-emerald-700' :
                      a.outcome === 'declined' ? 'bg-rose-50 text-rose-700' :
                      'bg-amber-50 text-amber-700'
                    }`}>{a.outcome}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recovery Events */}
          {dispatchResult.recovery_events.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
                <AlertTriangle size={12} className="text-amber-500" /> Recovery Events
              </h4>
              {dispatchResult.recovery_events.map((r, i) => (
                <div key={i} className="p-3 bg-amber-50/50 rounded-lg border border-amber-100 text-xs text-amber-800 mb-1.5">
                  <span className="font-medium">{r.event_type}:</span> {r.reason}
                </div>
              ))}
            </div>
          )}

          {/* Mobility Alternatives */}
          {dispatchResult.mobility_alternatives.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
                <Truck size={12} className="text-violet-500" /> Alternative Mobility Options
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {dispatchResult.mobility_alternatives.map((alt, i) => (
                  <div key={i} className="p-3 bg-violet-50/50 rounded-lg border border-violet-100">
                    <div className="font-medium text-sm text-violet-800">{alt.name}</div>
                    <div className="text-[11px] text-violet-600 mt-0.5">{alt.details}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fare Summary */}
          <div className="flex items-center justify-between p-3.5 bg-slate-50 rounded-xl text-sm">
            <span className="text-slate-600">
              Total: ₹{dispatchResult.total_fare} · Refund: <strong>{dispatchResult.refund_status}</strong>
            </span>
            <button
              onClick={() => { setStep('zones'); setQuote(null); setDispatchResult(null); }}
              className="px-3 py-1.5 bg-sky-100 text-sky-700 rounded-lg text-xs font-medium hover:bg-sky-200 transition"
            >
              New Request
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
