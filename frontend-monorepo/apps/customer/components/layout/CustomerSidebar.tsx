'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useWorkspaceStore } from '@/store/workspace';
import { 
  LayoutDashboard, 
  UserCheck, 
  Wrench, 
  BookOpen, 
  FileText, 
  PhoneCall, 
  CreditCard 
} from 'lucide-react';

export function CustomerSidebar() {
  const pathname = usePathname();
  const { activeBusinessId } = useWorkspaceStore();

  const navItems = [
    { name: 'Overview', href: `/${activeBusinessId}`, icon: LayoutDashboard },
    { name: 'Persona', href: `/${activeBusinessId}/persona`, icon: UserCheck },
    { name: 'Tools', href: `/${activeBusinessId}/tools`, icon: Wrench },
    { name: 'Knowledge', href: `/${activeBusinessId}/knowledge`, icon: BookOpen },
    { name: 'Logs', href: `/${activeBusinessId}/logs`, icon: FileText },
    { name: 'Channels', href: `/${activeBusinessId}/channels`, icon: PhoneCall },
    { name: 'Billing', href: `/${activeBusinessId}/billing`, icon: CreditCard },
  ];

  return (
    <aside className="bg-ink text-paper w-full md:w-20 md:min-h-screen flex md:flex-col items-center justify-between p-4 border-t md:border-t-0 md:border-r border-slate-custom shrink-0">
      <div className="flex md:flex-col items-center gap-6 w-full justify-around md:justify-start">
        <div className="hidden md:flex h-10 w-10 items-center justify-center rounded-xl bg-confirm-green font-serif font-bold text-lg text-paper">
          V
        </div>
        <nav className="flex md:flex-col gap-3 w-full justify-around md:justify-start">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = item.href === `/${activeBusinessId}`
              ? pathname === item.href
              : pathname.startsWith(item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                title={item.name}
                className={`p-3 rounded-xl flex items-center justify-center transition-all ${
                  isActive 
                    ? 'bg-paper text-ink shadow-md' 
                    : 'text-slate hover:text-paper hover:bg-white/10'
                }`}
              >
                <Icon className="w-5 h-5" />
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}