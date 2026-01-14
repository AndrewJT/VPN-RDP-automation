import React, { useState } from 'react';
import { Connection, ConnectionType, CredentialProfile } from '../types.ts';
import { 
  Monitor, 
  Shield, 
  MoreVertical, 
  Trash2, 
  Download, 
  ExternalLink,
  BrainCircuit,
  Loader2,
  CheckCircle2,
  Lock,
  Globe,
  Cpu,
  Laptop,
  Cloud,
  Terminal
} from 'lucide-react';
import { generateRdpFile, getSmartConfigHelp } from '../services/geminiService.ts';

const ICONS: Record<string, React.ReactNode> = {
  server: <Monitor size={20} />,
  shield: <Shield size={20} />,
  globe: <Globe size={20} />,
  cpu: <Cpu size={20} />,
  laptop: <Laptop size={20} />,
  cloud: <Cloud size={20} />
};

interface ConnectionCardProps {
  connection: Connection;
  onDelete?: () => void;
  onUpdate: (id: string, updates: Partial<Connection>) => void;
  credential?: CredentialProfile;
}

export const ConnectionCard: React.FC<ConnectionCardProps> = ({ connection, onDelete, onUpdate, credential }) => {
  const [showMenu, setShowMenu] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiAdvice, setAiAdvice] = useState<string | null>(null);
  const [status, setStatus] = useState<'idle' | 'connecting' | 'connected'>('idle');

  const handleConnect = () => {
    setStatus('connecting');
    if ((window as any).pywebview) {
      if (connection.type === ConnectionType.RDP) {
        (window as any).pywebview.api.launch_rdp(
          connection.host, 
          credential?.username || 'Admin',
          credential?.password || ''
        );
      } else {
        (window as any).pywebview.api.toggle_vpn(connection.protocol, connection.host, false);
      }
    }
    setTimeout(() => {
      setStatus('connected');
      onUpdate(connection.id, { lastConnected: Date.now() });
      if (connection.type === ConnectionType.RDP && !(window as any).pywebview) {
        generateRdpFile(connection, credential?.username);
      }
      setTimeout(() => setStatus('idle'), 4000);
    }, 1200);
  };

  const askAi = async () => {
    setAiLoading(true);
    setAiAdvice(null);
    const advice = await getSmartConfigHelp(connection);
    setAiAdvice(advice || "No advice found.");
    setAiLoading(false);
    setShowMenu(false);
  };

  return (
    <div className="group relative card-bg p-6 rounded-3xl shadow-md border hover:shadow-2xl hover:border-indigo-500/30 dark:hover:border-indigo-400/20 transition-all duration-300 overflow-hidden">
      <div className="flex justify-between items-start mb-6">
        <div className={`p-4 rounded-2xl shadow-sm ${connection.type === ConnectionType.RDP ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'}`}>
          {ICONS[connection.icon] || (connection.type === ConnectionType.RDP ? <Monitor size={20} /> : <Shield size={20} />)}
        </div>
        <div className="relative">
          <button onClick={() => setShowMenu(!showMenu)} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl text-slate-400 transition-colors">
            <MoreVertical size={18} />
          </button>
          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)}></div>
              <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 z-20 py-2 animate-in fade-in slide-in-from-top-2">
                <MenuOption onClick={() => { generateRdpFile(connection, credential?.username); setShowMenu(false); }} icon={<Download size={16} />} label="Export Config" />
                <MenuOption onClick={askAi} icon={<BrainCircuit size={16} />} label="AI Troubleshoot" highlight />
                <div className="h-px bg-slate-100 dark:bg-slate-800 my-2 mx-2"></div>
                <MenuOption onClick={() => { onDelete?.(); setShowMenu(false); }} icon={<Trash2 size={16} />} label="Delete Profile" danger />
              </div>
            </>
          )}
        </div>
      </div>

      <div className="space-y-1 mb-8">
        <div className="flex items-center gap-2">
          <h4 className="text-lg font-bold text-slate-900 dark:text-white truncate flex-1" title={connection.name}>{connection.name}</h4>
          {credential && <Lock size={12} className="text-slate-400" />}
        </div>
        <p className="text-xs text-slate-500 dark:text-slate-400 font-bold font-mono tracking-tight uppercase">{connection.host}</p>
        <div className="flex gap-2 mt-3">
          <span className="text-[9px] font-black bg-slate-100 dark:bg-slate-800 text-slate-500 px-2 py-0.5 rounded uppercase tracking-widest border border-slate-200 dark:border-slate-700">
            {connection.type}
          </span>
          {connection.protocol && (
            <span className="text-[9px] font-black bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 px-2 py-0.5 rounded uppercase tracking-widest border border-indigo-100 dark:border-indigo-800">
              {connection.protocol}
            </span>
          )}
        </div>
      </div>

      <button onClick={handleConnect} disabled={status === 'connecting'} className={`w-full flex items-center justify-center gap-2 py-4 rounded-2xl font-black text-xs uppercase tracking-widest transition-all ${status === 'connected' ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800' : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-600/30 active:scale-[0.98]'}`}>
        {status === 'connecting' ? <Loader2 size={16} className="animate-spin" /> : 
         status === 'connected' ? <CheckCircle2 size={16} /> : <Terminal size={16} />}
        <span>{status === 'connecting' ? 'Launching...' : status === 'connected' ? 'Active' : `Launch ${connection.type}`}</span>
      </button>

      <div className="mt-5 flex items-center justify-between text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-tighter">
        <span className="flex items-center gap-1"><ExternalLink size={10} /> {credential?.username || 'Manual Login'}</span>
        <span>{connection.lastConnected ? `Last: ${new Date(connection.lastConnected).toLocaleDateString()}` : 'Untested'}</span>
      </div>

      {aiAdvice && (
        <div className="mt-4 p-5 bg-indigo-600 rounded-2xl text-white shadow-inner animate-in slide-in-from-top-4 duration-300 relative">
           <div className="flex items-center gap-2 mb-3 text-[10px] font-black uppercase tracking-[2px]">
             <BrainCircuit size={14} /> AI Recommendation
           </div>
           <p className="text-xs leading-relaxed font-medium text-indigo-50">{aiAdvice}</p>
           <button onClick={() => setAiAdvice(null)} className="mt-4 text-[9px] font-black underline uppercase opacity-70 hover:opacity-100">Dismiss</button>
        </div>
      )}
      {aiLoading && (
        <div className="absolute inset-0 bg-white/80 dark:bg-slate-900/90 flex flex-col items-center justify-center z-30 p-8 text-center backdrop-blur-sm">
           <Loader2 size={32} className="text-indigo-600 animate-spin mb-4" />
           <p className="text-sm font-bold text-slate-800 dark:text-white uppercase tracking-widest">Consulting Gemini AI...</p>
        </div>
      )}
    </div>
  );
};

const MenuOption = ({ onClick, icon, label, danger, highlight }: any) => (
  <button onClick={onClick} className={`w-full text-left px-4 py-3 text-xs font-bold flex items-center gap-3 transition-colors ${danger ? 'text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20' : highlight ? 'text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20' : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'}`}>
    {icon} {label}
  </button>
);