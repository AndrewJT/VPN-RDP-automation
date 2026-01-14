
import React from 'react';
import { AppConfig } from '../types';
import { Settings as SettingsIcon, Save, RefreshCw, Trash2, ShieldCheck, Database } from 'lucide-react';

interface SettingsViewProps {
  config: AppConfig;
  onUpdate: (updates: Partial<AppConfig>) => void;
  isPython: boolean;
}

export const SettingsView: React.FC<SettingsViewProps> = ({ config, onUpdate, isPython }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-6 duration-500">
      <div className="flex items-center gap-6">
        <div className="p-4 bg-indigo-600 rounded-3xl text-white shadow-2xl">
          <SettingsIcon size={40} />
        </div>
        <div>
          <h1 className="text-4xl font-black text-slate-900 dark:text-white uppercase tracking-tighter">System Settings</h1>
          <p className="text-slate-500 font-bold uppercase text-xs tracking-widest mt-1">Configure global application behavior</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <section className="card-bg p-8 rounded-3xl border space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <RefreshCw className="text-indigo-600" />
            <h3 className="font-black text-lg uppercase tracking-tight">Sync & Performance</h3>
          </div>
          
          <div className="space-y-4">
            <Toggle 
              label="Python Native Sync" 
              sub="Sync configuration with local .netconnect_pro.json file" 
              active={config.pythonSync} 
              disabled={!isPython}
              onToggle={() => onUpdate({ pythonSync: !config.pythonSync })}
            />
            <div className="h-px bg-slate-100 dark:bg-slate-800"></div>
            <div className="flex justify-between items-center opacity-50 pointer-events-none">
              <div>
                <p className="font-bold text-sm">GPU Acceleration</p>
                <p className="text-[10px] text-slate-400 font-bold uppercase">Enhanced rendering performance</p>
              </div>
              <div className="w-12 h-6 bg-indigo-600 rounded-full relative">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full"></div>
              </div>
            </div>
          </div>
        </section>

        <section className="card-bg p-8 rounded-3xl border space-y-6">
          <div className="flex items-center gap-3 mb-2">
            <ShieldCheck className="text-emerald-600" />
            <h3 className="font-black text-lg uppercase tracking-tight">Security</h3>
          </div>
          
          <div className="space-y-4">
            <Toggle label="Encrypt Local Store" sub="AES-256 bits on saved password data" active={true} onToggle={() => {}} />
            <Toggle label="Auto-Lock Vault" sub="Lock identity vault after 30 mins idle" active={false} onToggle={() => {}} />
          </div>
        </section>

        <section className="card-bg p-8 rounded-3xl border space-y-4 col-span-full">
          <div className="flex items-center gap-3 mb-2">
            <Database className="text-amber-600" />
            <h3 className="font-black text-lg uppercase tracking-tight">Storage Management</h3>
          </div>
          <div className="flex flex-wrap gap-4">
            <button className="flex items-center gap-2 px-6 py-3 bg-slate-100 dark:bg-slate-800 rounded-xl font-bold text-xs uppercase text-slate-900 dark:text-white hover:bg-slate-200">
              <RefreshCw size={14} /> Clear UI Cache
            </button>
            <button className="flex items-center gap-2 px-6 py-3 bg-red-50 text-red-600 rounded-xl font-bold text-xs uppercase hover:bg-red-100">
              <Trash2 size={14} /> Factory Reset App
            </button>
          </div>
        </section>
      </div>

      <div className="flex justify-end p-8 border-t border-slate-200 dark:border-slate-800">
        <button className="flex items-center gap-3 px-12 py-4 bg-indigo-600 text-white rounded-2xl font-black uppercase tracking-widest text-sm shadow-2xl shadow-indigo-600/30">
          <Save size={18} /> Apply Changes
        </button>
      </div>
    </div>
  );
};

const Toggle = ({ label, sub, active, onToggle, disabled }: any) => (
  <div className={`flex justify-between items-center ${disabled ? 'opacity-30' : ''}`}>
    <div>
      <p className="font-bold text-sm">{label}</p>
      <p className="text-[10px] text-slate-400 font-bold uppercase tracking-tight">{sub}</p>
    </div>
    <button 
      onClick={onToggle}
      disabled={disabled}
      className={`w-12 h-6 rounded-full relative transition-colors ${active ? 'bg-indigo-600' : 'bg-slate-300 dark:bg-slate-800'}`}
    >
      <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${active ? 'right-1' : 'left-1'}`}></div>
    </button>
  </div>
);
