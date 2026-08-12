import React from 'react';
import { AlertCircle } from 'lucide-react';

export function EmptyState({ icon: Icon = AlertCircle, title, message, action }) {
  return (
    <div className="py-12 px-4 text-center max-w-md mx-auto space-y-3 select-none">
      <div className="w-10 h-10 rounded-[6px] bg-[#1C2129] border border-[#30363D] text-[#8B949E] flex items-center justify-center mx-auto">
        <Icon className="w-5 h-5" />
      </div>
      <h4 className="text-sm font-semibold text-[#E6EDF3]">{title}</h4>
      <p className="text-xs text-[#8B949E] leading-relaxed">{message}</p>
      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}
