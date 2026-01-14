import React, { useState } from 'react';
import { Connection, ConnectionType, AppConfig, VPNProtocol } from '../types.ts';
import { Plus, Server, Shield, Globe, Cpu, Laptop, Cloud, X } from 'lucide-react';
import { ConnectionCard } from './ConnectionCard.tsx';

interface ConnectionListProps {
  type: ConnectionType;
  connections: Connection[];
  credentials: any[];
  onConfigUpdate: (config: Partial<AppConfig>) => void;
  fullConfig: AppConfig;
}

export const ConnectionList: React.FC<ConnectionListProps> = ({ type, connections, credentials, onConfigUpdate, fullConfig }) => {
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState<Partial<Connection>>({
    type: type,
    icon: 'server',
    port: type === ConnectionType.RDP ? '3389' : '443',
    protocol: VPNProtocol.OpenVPN
  });

  const handleSave = () => {
    if (!formData.name || !formData.host) return;
    const newConn: Connection = {
      ...formData as Connection,
      id: Date.now().toString(),
    };
    onConfigUpdate({ connections: [...fullConfig.connections, newConn] });
    setShowModal(false);
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-4xl font-black uppercase tracking-tighter text-slate-900 dark:text-white">
          {type} {type === ConnectionType.RDP ? 'Host Manager' : 'VPN Gateways'}
        </h2>
        <button 
          onClick={() => setShowModal(true)}
          className="px-8 py-4 bg-indigo-600 text-white rounded-xl font-black uppercase tracking-widest text-xs hover:bg-indigo-700 shadow-xl transition-all flex items-center gap-2"
        >
          <Plus size={18} /> Create Profile
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {connections.map(conn => (
          <ConnectionCard 
            key={conn.id} 
            connection={conn} 
            onDelete={() => onConfigUpdate({ connections: fullConfig.connections.filter(c => c.id !== conn.id) })}
            onUpdate={(id, up) => onConfigUpdate({ connections: fullConfig.connections.map(c => c.id === id ? {...c, ...up} : c)})}
            credential={credentials.find(c => c.id === conn.credentialId)}
          />
        ))}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-slate-950/90 backdrop-blur-sm">
          <div className="bg-white dark:bg-slate-900 w-full max-w-2xl rounded-2xl border-2 border-black dark:border-slate-700 shadow-[8px_8px_0px_rgba(0,0,0,1)] dark:shadow-none overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="p-8 border-b-2 border-black dark:border-slate-800 flex justify-between items-center bg-indigo-50 dark:bg-slate-800/50">
              <h3 className="text-2xl font-black uppercase text-slate-900 dark:text-white">Setup {type} Connection</h3>
              <button onClick={() => setShowModal(false)} className="hover:rotate-90 transition-transform text-slate-900 dark:text-white"><X size={24} /></button>
            </div>
            
            <div className="p-8 grid grid-cols-2 gap-6 max-h-[60vh] overflow-y-auto">
              <div className="col-span-2">
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">Display Name</label>
                <input 
                  className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 font-bold bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  placeholder="e.g. Primary Work Server"
                  onChange={e => setFormData({...formData, name: e.target.value})}
                />
              </div>
              
              <div className="col-span-1">
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">Host / IP Address</label>
                <input 
                  className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 font-mono bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  placeholder="192.168.1.100"
                  onChange={e => setFormData({...formData, host: e.target.value})}
                />
              </div>

              <div className="col-span-1">
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">Port</label>
                <input 
                  className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 font-mono bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  defaultValue={formData.port}
                  onChange={e => setFormData({...formData, port: e.target.value})}
                />
              </div>

              {type === ConnectionType.RDP ? (
                <div className="col-span-2">
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">Active Directory Domain (Optional)</label>
                  <input 
                    className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    placeholder="CORP.LOCAL"
                    onChange={e => setFormData({...formData, domain: e.target.value})}
                  />
                </div>
              ) : (
                <>
                <div className="col-span-1">
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">VPN Client Protocol</label>
                  <select 
                    className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 font-bold bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    onChange={e => setFormData({...formData, protocol: e.target.value as any})}
                  >
                    {Object.values(VPNProtocol).map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div className="col-span-1">
                  <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">VPN Gateway / Group</label>
                  <input 
                    className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                    placeholder="General_Users"
                    onChange={e => setFormData({...formData, gateway: e.target.value})}
                  />
                </div>
                </>
              )}

              <div className="col-span-2">
                <label className="text-[10px] font-black uppercase tracking-widest block mb-2 text-slate-500">Auto-Link Credentials</label>
                <select 
                  className="w-full p-4 rounded-xl outline-none focus:ring-4 focus:ring-indigo-500/20 font-bold bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white"
                  onChange={e => setFormData({...formData, credentialId: e.target.value})}
                >
                  <option value="">-- Always Ask for Password --</option>
                  {credentials.map(c => <option key={c.id} value={c.id}>{c.name} ({c.username})</option>)}
                </select>
              </div>
            </div>

            <div className="p-8 bg-indigo-50 dark:bg-slate-950/40 flex justify-end gap-4 border-t-2 border-black dark:border-slate-800">
              <button onClick={() => setShowModal(false)} className="px-6 py-2 font-black uppercase text-xs text-slate-600 dark:text-slate-400">Cancel</button>
              <button onClick={handleSave} className="px-12 py-4 bg-indigo-600 text-white rounded-xl font-black uppercase tracking-widest text-sm shadow-lg">Save Profile</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};