import { useState, useEffect, useCallback } from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, Polygon, Tooltip as LeafletTooltip } from 'react-leaflet';
import L from 'leaflet';
import { Flame, Clock, Activity, BarChart3 } from 'lucide-react';
import * as api from '../api';
import type { HotZoneMetric, HotZonesResponse, ZoneDetailResponse } from '../types';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

// Fix Leaflet default icon paths (Vite strips them)
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Real Jaipur landmark boundaries for map patches (approximate polygons)
const JAIPUR_PATCHES: { name: string; tag: string; color: string; positions: [number, number][] }[] = [
  {
    name: 'Pink City (Walled Heritage City)',
    tag: 'UNESCO Heritage Hub',
    color: '#e11d48',
    positions: [
      [26.9315, 75.8150], [26.9315, 75.8360],
      [26.9180, 75.8360], [26.9180, 75.8150],
    ],
  },
  {
    name: 'C-Scheme & Civil Lines',
    tag: 'Government & Dining',
    color: '#0284c7',
    positions: [
      [26.9180, 75.7900], [26.9180, 75.8080],
      [26.9040, 75.8080], [26.9040, 75.7900],
    ],
  },
  {
    name: 'Malviya Nagar & Gaurav Tower',
    tag: 'Retail & IT Tech Corridor',
    color: '#7c3aed',
    positions: [
      [26.8640, 75.8080], [26.8640, 75.8360],
      [26.8410, 75.8360], [26.8410, 75.8080],
    ],
  },
  {
    name: 'Mansarovar Colony',
    tag: 'High Density Residential',
    color: '#059669',
    positions: [
      [26.8740, 75.7480], [26.8740, 75.7760],
      [26.8500, 75.7760], [26.8500, 75.7480],
    ],
  },
  {
    name: 'Vaishali Nagar',
    tag: 'Commercial & Western Suburb',
    color: '#d97706',
    positions: [
      [26.9160, 75.7260], [26.9160, 75.7540],
      [26.8960, 75.7540], [26.8960, 75.7260],
    ],
  },
  {
    name: 'Jaipur Junction Station Area',
    tag: 'Interstate Transit Node',
    color: '#ea580c',
    positions: [
      [26.9270, 75.7820], [26.9270, 75.7950],
      [26.9160, 75.7950], [26.9160, 75.7820],
    ],
  },
  {
    name: 'Airport & Sanganer Corridor',
    tag: 'Aviation & Aerotropolis',
    color: '#0284c7',
    positions: [
      [26.8340, 75.8000], [26.8340, 75.8260],
      [26.8140, 75.8260], [26.8140, 75.8000],
    ],
  },
  {
    name: 'Raja Park Promenade',
    tag: 'Bustling Shopping District',
    color: '#db2777',
    positions: [
      [26.8960, 75.8280], [26.8960, 75.8440],
      [26.8830, 75.8440], [26.8830, 75.8280],
    ],
  },
];

// Key Jaipur tourist & emergency landmarks
const JAIPUR_LANDMARKS: { name: string; type: string; icon: string; pos: [number, number] }[] = [
  { name: 'Hawa Mahal', type: 'Heritage', icon: '🏛️', pos: [26.9239, 75.8267] },
  { name: 'City Palace', type: 'Heritage', icon: '🏰', pos: [26.9258, 75.8237] },
  { name: 'Albert Hall Museum', type: 'Culture', icon: '🏛️', pos: [26.9116, 75.8194] },
  { name: 'SMS Medical Hospital', type: 'Hospital', icon: '🏥', pos: [26.8995, 75.8193] },
  { name: 'Jaipur Junction Station', type: 'Transit', icon: '🚆', pos: [26.9215, 75.7873] },
  { name: 'Jaipur Int’l Airport (JAI)', type: 'Transit', icon: '✈️', pos: [26.8241, 75.8122] },
  { name: 'Jal Mahal (Water Palace)', type: 'Heritage', icon: '🌊', pos: [26.9535, 75.8462] },
];

const TIME_WINDOWS = [
  { value: 'now', label: 'Now' },
  { value: 'last_15_mins', label: '15 min' },
  { value: 'last_hour', label: '1 hour' },
  { value: 'today', label: 'Today' },
];

const METRICS = [
  { value: 'zone_score', label: 'Zone Score' },
  { value: 'availability', label: 'Availability' },
  { value: 'driver_cancels', label: 'Driver Cancels' },
  { value: 'passenger_cancels', label: 'Pax Cancels' },
  { value: 'demand', label: 'Demand' },
];

function getHeatColor(score: number) {
  if (score >= 70) return '#ef4444';
  if (score >= 50) return '#f59e0b';
  if (score >= 30) return '#10b981';
  return '#6366f1';
}

function getHeatOpacity(score: number) {
  return 0.25 + (score / 100) * 0.55;
}

function TagBadge({ tag }: { tag: string }) {
  const colors: Record<string, string> = {
    'Hot Zone': 'bg-red-50 text-red-700 border-red-200',
    'High Availability': 'bg-emerald-50 text-emerald-700 border-emerald-200',
    'High Demand': 'bg-amber-50 text-amber-700 border-amber-200',
    'Driver Cancel Hotspot': 'bg-rose-50 text-rose-700 border-rose-200',
    'Priority Zone': 'bg-violet-50 text-violet-700 border-violet-200',
    'Cancellation Hotspot': 'bg-orange-50 text-orange-700 border-orange-200',
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium border ${colors[tag] || 'bg-slate-50 text-slate-600 border-slate-200'}`}>
      {tag}
    </span>
  );
}

// Fit map to zones
function MapBounds({ zones }: { zones: HotZoneMetric[] }) {
  const map = useMap();
  useEffect(() => {
    if (zones.length > 0) {
      const bounds = zones.map(z => [z.center_lat, z.center_lng] as [number, number]);
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 14 });
    }
  }, [zones, map]);
  return null;
}

function ZoneDetailPanel({ zoneId, onClose }: { zoneId: string; onClose: () => void }) {
  const [data, setData] = useState<ZoneDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getZoneDetail(zoneId).then(setData).finally(() => setLoading(false));
  }, [zoneId]);

  if (loading) return <div className="p-6 text-center text-sm text-slate-500">Loading zone details…</div>;
  if (!data) return null;

  const z = data.zone;
  return (
    <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 flex items-center gap-2">
          <Flame size={16} className="text-amber-500" />
          {z.zone_name}
        </h3>
        <button onClick={onClose} className="text-xs text-slate-400 hover:text-slate-600 px-2 py-1 rounded bg-slate-50">Close</button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Zone Score', value: z.zone_score.toFixed(1), color: getHeatColor(z.zone_score) },
          { label: 'Available', value: z.available_ride_count, color: '#10b981' },
          { label: 'Demand', value: z.demand_estimate ?? '—', color: '#f59e0b' },
        ].map((s, i) => (
          <div key={i} className="text-center p-3 rounded-xl bg-slate-50">
            <div className="text-2xl font-bold" style={{ color: s.color }}>{s.value}</div>
            <div className="text-[11px] text-slate-500 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Cancellation Rates */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Driver Cancel', value: z.driver_cancel_rate, count: z.driver_cancel_count },
          { label: 'Pax Cancel', value: z.passenger_cancel_rate, count: z.passenger_cancel_count },
          { label: 'Provider Cancel', value: z.provider_cancel_rate, count: z.provider_cancel_count },
        ].map((s, i) => (
          <div key={i} className="p-2.5 rounded-lg bg-slate-50 text-center">
            <div className="text-sm font-bold text-slate-800">{s.value != null ? `${(s.value * 100).toFixed(1)}%` : 'N/A'}</div>
            <div className="text-[10px] text-slate-500">{s.label} ({s.count})</div>
          </div>
        ))}
      </div>

      {/* Time Series Chart */}
      {data.time_series.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1">
            <BarChart3 size={12} /> Time Series
          </h4>
          <div className="h-44">
            <ResponsiveContainer>
              <AreaChart data={data.time_series}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                <Area type="monotone" dataKey="available_rides" stroke="#0ea5e9" fill="#0ea5e940" name="Available" />
                <Area type="monotone" dataKey="driver_cancels" stroke="#ef4444" fill="#ef444420" name="Driver Cancels" />
                <Area type="monotone" dataKey="zone_score" stroke="#8b5cf6" fill="#8b5cf620" name="Zone Score" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Provider Breakdown */}
      {data.provider_breakdown.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-slate-700 mb-2">Provider Breakdown</h4>
          <div className="h-36">
            <ResponsiveContainer>
              <BarChart data={data.provider_breakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="provider_name" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                <Bar dataKey="estimated_available_cabs" fill="#0ea5e9" name="Cabs" radius={[4,4,0,0]} />
                <Bar dataKey="avg_pickup_eta" fill="#f59e0b" name="Avg ETA" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5">
        {z.tags.map((t, i) => <TagBadge key={i} tag={t} />)}
      </div>
    </div>
  );
}

export default function HotZoneMap() {
  const [timeWindow, setTimeWindow] = useState('last_hour');
  const [metric, setMetric] = useState('zone_score');
  const [data, setData] = useState<HotZonesResponse | null>(null);
  const [selectedZone, setSelectedZone] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showPatches, setShowPatches] = useState(true);
  const [showLandmarks, setShowLandmarks] = useState(true);

  const fetchZones = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getHotZones('Jaipur', timeWindow, metric);
      setData(result);
    } finally {
      setLoading(false);
    }
  }, [timeWindow, metric]);

  useEffect(() => { fetchZones(); }, [fetchZones]);

  const zones = data?.zones || [];

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-4 shadow-sm">
        <div className="flex items-center gap-2 mb-3">
          <Flame className="text-amber-500" size={20} />
          <h2 className="text-lg font-bold text-slate-900">Hot Zone Map · Jaipur Real Patches</h2>
          {loading && <Activity size={14} className="animate-spin text-sky-500 ml-2" />}
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Time Window Toggle */}
          <div className="flex items-center gap-1 bg-slate-50 rounded-lg p-0.5">
            {TIME_WINDOWS.map(tw => (
              <button
                key={tw.value}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  timeWindow === tw.value ? 'bg-white text-sky-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
                onClick={() => setTimeWindow(tw.value)}
              >
                <Clock size={11} /> {tw.label}
              </button>
            ))}
          </div>

          {/* Metric Toggle */}
          <div className="flex items-center gap-1 bg-slate-50 rounded-lg p-0.5">
            {METRICS.map(m => (
              <button
                key={m.value}
                className={`px-2.5 py-1.5 rounded-md text-[11px] font-medium transition-all ${
                  metric === m.value ? 'bg-white text-amber-700 shadow-sm' : 'text-slate-500 hover:text-slate-700'
                }`}
                onClick={() => setMetric(m.value)}
              >
                {m.label}
              </button>
            ))}
          </div>

          {/* Map Layer Toggles */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={() => setShowPatches(!showPatches)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                showPatches
                  ? 'bg-sky-50 text-sky-700 border-sky-200'
                  : 'bg-white text-slate-400 border-slate-200 hover:text-slate-600'
              }`}
            >
              🗺️ {showPatches ? 'Hide Patches' : 'Show Patches'}
            </button>
            <button
              onClick={() => setShowLandmarks(!showLandmarks)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                showLandmarks
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-white text-slate-400 border-slate-200 hover:text-slate-600'
              }`}
            >
              📍 {showLandmarks ? 'Hide Landmarks' : 'Show Landmarks'}
            </button>
          </div>
        </div>
      </div>

      {/* Map + Zone List */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
        {/* Map */}
        <div className="lg:col-span-3 bg-white rounded-2xl border border-slate-200/80 overflow-hidden shadow-sm" style={{ height: 440 }}>
          <MapContainer
            center={[26.9124, 75.7873]}
            zoom={13}
            style={{ width: '100%', height: '100%' }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {/* Real Jaipur neighborhood patches */}
            {showPatches && JAIPUR_PATCHES.map(patch => (
              <Polygon
                key={patch.name}
                positions={patch.positions}
                pathOptions={{
                  color: patch.color,
                  fillColor: patch.color,
                  fillOpacity: 0.12,
                  weight: 1.5,
                  dashArray: '6 4',
                }}
              >
                <LeafletTooltip sticky>{patch.name} ({patch.tag})</LeafletTooltip>
              </Polygon>
            ))}

            {/* Real Jaipur iconic landmarks */}
            {showLandmarks && JAIPUR_LANDMARKS.map(lm => (
              <CircleMarker
                key={lm.name}
                center={lm.pos}
                radius={6}
                pathOptions={{
                  color: '#1e293b',
                  fillColor: '#38bdf8',
                  fillOpacity: 0.9,
                  weight: 1.5,
                }}
              >
                <LeafletTooltip direction="top" offset={[0, -6]} opacity={0.95}>
                  <span>{lm.icon} <strong>{lm.name}</strong> ({lm.type})</span>
                </LeafletTooltip>
                <Popup>
                  <div className="text-xs space-y-1">
                    <div className="font-bold text-sm">{lm.icon} {lm.name}</div>
                    <div className="text-slate-500">Category: {lm.type}</div>
                    <div className="text-slate-400 text-[10px]">Lat: {lm.pos[0]}, Lng: {lm.pos[1]}</div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
            <MapBounds zones={zones} />
            {zones.map(z => (
              <CircleMarker
                key={z.zone_id}
                center={[z.center_lat, z.center_lng]}
                radius={14 + (z.zone_score / 10)}
                pathOptions={{
                  color: getHeatColor(z.zone_score),
                  fillColor: getHeatColor(z.zone_score),
                  fillOpacity: getHeatOpacity(z.zone_score),
                  weight: 2,
                }}
                eventHandlers={{ click: () => setSelectedZone(z.zone_id) }}
              >
                <Popup>
                  <div className="text-xs space-y-1 min-w-[180px]">
                    <div className="font-bold text-sm">{z.zone_name}</div>
                    <div>Score: <strong style={{ color: getHeatColor(z.zone_score) }}>{z.zone_score.toFixed(1)}</strong></div>
                    <div>Available: <strong>{z.available_ride_count}</strong></div>
                    <div>Demand: <strong>{z.demand_estimate ?? 'N/A'}</strong></div>
                    <div>Driver Cancels: <strong>{z.driver_cancel_count}</strong></div>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {z.tags.map((t, i) => <span key={i} className="px-1.5 py-0.5 bg-slate-100 rounded text-[10px]">{t}</span>)}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>

        {/* Zone List */}
        <div className="lg:col-span-2 space-y-3 max-h-[440px] overflow-y-auto pr-1">
          {zones.map((z, i) => (
            <div
              key={z.zone_id}
              className={`bg-white rounded-xl border p-3.5 cursor-pointer transition-all hover:shadow-md ${
                selectedZone === z.zone_id ? 'border-sky-300 ring-2 ring-sky-100' : 'border-slate-200/80'
              }`}
              onClick={() => setSelectedZone(selectedZone === z.zone_id ? null : z.zone_id)}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg flex items-center justify-center text-[11px] font-bold text-white"
                    style={{ background: getHeatColor(z.zone_score) }}>
                    {i + 1}
                  </div>
                  <div>
                    <div className="font-medium text-sm text-slate-900">{z.zone_name}</div>
                    <div className="text-[10px] text-slate-400">{z.time_window_label}</div>
                  </div>
                </div>
                <div className="text-lg font-bold" style={{ color: getHeatColor(z.zone_score) }}>
                  {z.zone_score.toFixed(1)}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="text-center p-1.5 bg-slate-50 rounded">
                  <div className="font-semibold text-slate-800">{z.available_ride_count}</div>
                  <div className="text-slate-500">Avail</div>
                </div>
                <div className="text-center p-1.5 bg-slate-50 rounded">
                  <div className="font-semibold text-slate-800">{z.demand_estimate ?? '—'}</div>
                  <div className="text-slate-500">Demand</div>
                </div>
                <div className="text-center p-1.5 bg-slate-50 rounded">
                  <div className="font-semibold text-rose-600">{z.driver_cancel_count}</div>
                  <div className="text-slate-500">D.Cancel</div>
                </div>
              </div>

              <div className="flex flex-wrap gap-1 mt-2">
                {z.tags.slice(0, 3).map((t, i) => <TagBadge key={i} tag={t} />)}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Zone Detail Panel */}
      {selectedZone && (
        <ZoneDetailPanel zoneId={selectedZone} onClose={() => setSelectedZone(null)} />
      )}
    </div>
  );
}
