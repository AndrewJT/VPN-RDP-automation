import React from 'react';
import { Connection, ConnectionType, CredentialProfile } from '../types.ts';
import { ConnectionCard } from './ConnectionCard.tsx';
import { 
  Zap, 
  Activity, 
  Clock,
  ShieldCheck
} from 'lucide-react';

interface DashboardProps {
  connections: Connection[];
  credentials: CredentialProfile[];
  onUpdate: (id: string, updates: Partial<Connection>) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ connections, onUpdate, credentials }) => {
  const activeCount = connections.length;
  const rdpCount = connections.filter(c => c.type === ConnectionType.RDP).length;
  const vpnCount = connections.filter(c => c.type === ConnectionType.VPN).length;

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={<Activity className="text-blue-600" />} label="Total Profiles" value={activeCount.toString()} sub="Network endpoints" />
        <StatCard icon={<Zap className="text-amber-600" />} label="RDP Hosts" value={rdpCount.toString()} sub="Remote desktop" />
        <StatCard icon={<ShieldCheck className="text-emerald-600" />} label="VPN Tunnels" value={vpnCount.toString()} sub="Secure gateways" />
        <StatCard icon={<Clock className="text-indigo-600" />} label="Uptime" value="100%" sub="Service status" />
      </div>

      <section>
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100">Quick Access</h3>
          <button className="text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider hover:underline">Manage All</button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {connections.slice(0, 3).map(conn => (
            <ConnectionCard 
              key={conn.id} 
              connection={conn} 
              onUpdate={onUpdate} 
              credential={credentials.find(c => c.id === conn.credentialId)}
            />
          ))}
          {connections.length === 0 && (
            <div className="col-span-full py-16 text-center card-bg rounded-3xl border border-dashed">
              <p className="text-slate-400 font-medium">No connection profiles saved. Create your first RDP or VPN endpoint.</p>
            </div>
          )}
        </div>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="card-bg p-6 rounded-3xl shadow-sm border">
          <h3 className="text-lg font-bold mb-6 text-slate-800 dark:text-slate-100">Live Traffic</h3>
          <div className="space-y-4">
             <SessionItem name="Global-VPN-Cluster" duration="2h 14m" user="System_Auto" type="VPN" />
             <SessionItem name="RDP-Win11-Dev" duration="15m" user="Admin_Local" type="RDP" />
          </div>
        </div>
        
        <div className="bg-slate-900 dark:bg-indigo-900/30 p-8 rounded-3xl shadow-xl text-white relative overflow-hidden border border-slate-800">
          <div className="relative z-10">
            <h3 className="text-2xl font-bold mb-2">Python OS Bridge</h3>
            <p className="text-slate-400 dark:text-indigo-200 mb-6 max-w-sm leading-relaxed text-sm">
              The application logic is currently tied to your local Python runtime. All network calls are executed natively for maximum performance.
            </p>
            <div className="flex gap-3">
              <div className="px-3 py-1 bg-white/10 rounded-lg text-[10px] font-bold border border-white/10 uppercase">v2.4.0 Engine</div>
              <div className="px-3 py-1 bg-green-500/20 rounded-lg text-[10px] font-bold border border-green-500/30 text-green-400 uppercase">Secure Boot</div>
            </div>
          </div>
          <div className="absolute -bottom-10 -right-10 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl"></div>
        </div>
      </div>
    </div>
  );
};

const StatCard: React.FC<{ icon: React.ReactNode, label: string, value: string, sub: string }> = ({ icon, label, value, sub }) => (
  <div className="card-bg p-6 rounded-3xl shadow-sm border hover:shadow-lg transition-all">
    <div className="flex items-center gap-4 mb-3">
      <div className="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl">{icon}</div>
      <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-widest">{label}</span>
    </div>
    <div className="flex flex-col">
      <span className="text-3xl font-bold text-slate-900 dark:text-white">{value}</span>
      <span className="text-[10px] text-slate-400 font-bold uppercase mt-1">{sub}</span>
    </div>
  </div>
);

const SessionItem: React.FC<{ name: string, duration: string, user: string, type: string }> = ({ name, duration, user, type }) => (
  <div className="flex items-center justify-between p-4 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-2xl transition-colors border border-transparent hover:border-slate-200 dark:hover:border-slate-700">
    <div className="flex items-center gap-4">
      <div className={`w-3 h-3 rounded-full animate-pulse ${type === 'RDP' ? 'bg-blue-500' : 'bg-emerald-500'}`}></div>
      <div>
        <p className="font-bold text-sm text-slate-800 dark:text-slate-100">{name}</p>
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">{user}</p>
      </div>
    </div>
    <div className="text-right">
      <p className="text-xs font-bold text-slate-600 dark:text-slate-300">{duration}</p>
      <p className="text-[10px] text-indigo-600 font-bold uppercase tracking-widest">{type}</p>
    </div>
  </div>
);