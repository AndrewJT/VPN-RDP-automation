
import React, { useState } from 'react';
import { CredentialProfile } from '../types';
import { Key, Plus, Trash2, ShieldCheck, Lock, X } from 'lucide-react';

interface VaultManagerProps {
  credentials: CredentialProfile[];
  onUpdate: (creds: CredentialProfile[]) => void;
}

export const VaultManager: React.FC<VaultManagerProps> = ({ credentials, onUpdate }) => {
  const [showAdd, setShowAdd] = useState(false);
  const [newCred, setNewCred] = useState<Partial<CredentialProfile>>({});

  const handleAdd = () => {
    if (!newCred.name || !newCred.username) return;
    onUpdate([...credentials, { ...newCred, id: Date.now().toString() } as CredentialProfile]);
    setShowAdd(false);
    setNewCred({});
  };

  const remove = (id: string) => onUpdate(credentials.filter(c => c.id !== id));

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center gap-6 p-10 bg-black text-white rounded-3xl shadow-2xl">
        <div className="p-5 bg-indigo-600 rounded-2xl">
          <Lock className="w-12 h-12" />
        </div>
        <div className="flex-1">
          <h2 className="text-4xl font-black uppercase tracking-tighter">Secure Vault</h2>
          <p className="text-indigo-200 font-bold uppercase text-[10px] tracking-widest mt-1">Encrypted Credential Storage</p>
        </div>
        <button 
          onClick={() => setShowAdd(true)}
          className="px-8 py-4 bg-white text-black rounded-xl font-black uppercase tracking-widest text-xs hover:bg-indigo-400 transition-all flex items-center gap-2"
        >
          <Plus size={18} /> New Identity
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {credentials.map(c => (
          <div key={c.id} className="card-bg p-8 rounded-2xl group relative">
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-indigo-50 dark:bg-slate-800 rounded-xl text-indigo-600">
                  <ShieldCheck size={24} />
                </div>
                <h4 className="text-xl font-black uppercase tracking-tight">{c.name}</h4>
              </div>
              <button 
                onClick={() => remove(c.id)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-all"
              >
                <Trash2 size={20} />
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
               <div>
                 <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Username</p>
                 <p className="font-bold font-mono">{c.username}</p>
               </div>
               <div>
                 <p className="text-[10px] font-black uppercase text-slate-400 tracking-widest mb-1">Domain</p>
                 <p className="font-bold font-mono">{c.domain || 'N/A'}</p>
               </div>
            </div>
          </div>
        ))}
      </div>

      {showAdd && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/95 backdrop-blur-sm">
           <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-2xl border-4 border-black shadow-[10px_10px_0px_rgba(0,0,0,1)] overflow-hidden">
             <div className="p-8 border-b-4 border-black flex justify-between items-center bg-indigo-600 text-white">
               <h3 className="text-xl font-black uppercase tracking-tighter">New Secure Identity</h3>
               <button onClick={() => setShowAdd(false)}><X size={24} /></button>
             </div>
             
             <div className="p-8 space-y-6">
               <div>
                 <label className="text-[10px] font-black uppercase tracking-widest block mb-2">Identity Label</label>
                 <input 
                  placeholder="e.g. Domain Admin"
                  className="w-full p-4 rounded-xl font-bold"
                  onChange={e => setNewCred({...newCred, name: e.target.value})}
                 />
               </div>
               <div>
                 <label className="text-[10px] font-black uppercase tracking-widest block mb-2">Username</label>
                 <input 
                  placeholder="admin_user"
                  className="w-full p-4 rounded-xl font-bold"
                  onChange={e => setNewCred({...newCred, username: e.target.value})}
                 />
               </div>
               <div>
                 <label className="text-[10px] font-black uppercase tracking-widest block mb-2">Domain (Optional)</label>
                 <input 
                  placeholder="INTERNAL"
                  className="w-full p-4 rounded-xl font-bold"
                  onChange={e => setNewCred({...newCred, domain: e.target.value})}
                 />
               </div>
               <div>
                 <label className="text-[10px] font-black uppercase tracking-widest block mb-2">Secret Key / Password</label>
                 <input 
                  type="password"
                  placeholder="••••••••••••"
                  className="w-full p-4 rounded-xl font-bold"
                  onChange={e => setNewCred({...newCred, password: e.target.value})}
                 />
               </div>
             </div>
             
             <div className="p-8 flex justify-end gap-4 bg-slate-50 dark:bg-slate-950/40">
               <button onClick={() => setShowAdd(false)} className="font-bold uppercase text-xs">Abort</button>
               <button onClick={handleAdd} className="px-10 py-4 bg-black text-white rounded-xl font-black uppercase tracking-widest text-xs">Secure Entry</button>
             </div>
           </div>
        </div>
      )}
    </div>
  );
};
