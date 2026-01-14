
import React from 'react';
import { 
  LayoutDashboard, 
  Monitor, 
  ShieldCheck, 
  Settings, 
  Moon, 
  Sun,
  ChevronRight,
  LogOut
} from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: any) => void;
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, setActiveTab, theme, toggleTheme }) => {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white dark:bg-[#1e293b] border-r border-gray-200 dark:border-gray-800 flex flex-col transition-colors">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <ShieldCheck className="text-white w-6 h-6" />
            </div>
            <h1 className="font-bold text-xl tracking-tight text-gray-900 dark:text-white">NetConnect<span className="text-indigo-500">Pro</span></h1>
          </div>

          <nav className="space-y-1">
            <NavItem 
              icon={<LayoutDashboard className="w-5 h-5" />} 
              label="Dashboard" 
              active={activeTab === 'dashboard'} 
              onClick={() => setActiveTab('dashboard')} 
            />
            <NavItem 
              icon={<Monitor className="w-5 h-5" />} 
              label="RDP Connections" 
              active={activeTab === 'rdp'} 
              onClick={() => setActiveTab('rdp')} 
            />
            <NavItem 
              icon={<ShieldCheck className="w-5 h-5" />} 
              label="VPN Clients" 
              active={activeTab === 'vpn'} 
              onClick={() => setActiveTab('vpn')} 
            />
          </nav>
        </div>

        <div className="mt-auto p-6 space-y-4">
          <div className="p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-2xl border border-indigo-100 dark:border-indigo-800/50">
            <p className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-2">Support</p>
            <p className="text-sm text-indigo-900/70 dark:text-indigo-200/70 leading-relaxed">Need help with your connections? Ask Gemini AI.</p>
          </div>

          <div className="flex items-center justify-between border-t border-gray-200 dark:border-gray-800 pt-6">
            <button 
              onClick={toggleTheme}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg text-gray-500 dark:text-gray-400 transition-colors"
            >
              {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
            </button>
            <button className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-gray-500 dark:text-red-400 transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto bg-gray-50 dark:bg-[#0f172a] p-8">
        <header className="flex justify-between items-center mb-8">
          <div>
            <h2 className="text-2xl font-bold dark:text-white capitalize">{activeTab}</h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm mt-1">Manage and monitor your secure network infrastructure.</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative group">
               <img src="https://picsum.photos/seed/user1/40/40" className="w-10 h-10 rounded-full border-2 border-white dark:border-gray-800 shadow-sm" alt="User" />
               <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-900 rounded-full"></div>
            </div>
          </div>
        </header>
        {children}
      </main>
    </div>
  );
};

const NavItem: React.FC<{ icon: React.ReactNode, label: string, active: boolean, onClick: () => void }> = ({ icon, label, active, onClick }) => (
  <button 
    onClick={onClick}
    className={`w-full flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 ${
      active 
        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' 
        : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
    }`}
  >
    <div className="flex items-center gap-3">
      {icon}
      <span className="font-medium">{label}</span>
    </div>
    {active && <ChevronRight className="w-4 h-4 opacity-50" />}
  </button>
);
