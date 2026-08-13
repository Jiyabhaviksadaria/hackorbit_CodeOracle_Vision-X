import React from 'react';

/**
 * Terminal-style code card wrapper with red/yellow/green traffic light dots.
 * From Uiverse.io by EmmaxPlay — adapted for CodeOracle dark theme.
 */
export function CodeCard({ children, className = '' }) {
  return (
    <div className={`rounded-[8px] overflow-hidden bg-[#011522] border border-[#30363D] ${className}`}>
      {/* Traffic Light Toolbar */}
      <div className="flex items-center gap-[6px] px-3 py-2.5 bg-[#0a1e2e] border-b border-[#30363D]">
        <span className="w-[10px] h-[10px] rounded-full bg-[#ff605c] inline-block" />
        <span className="w-[10px] h-[10px] rounded-full bg-[#ffbd44] inline-block" />
        <span className="w-[10px] h-[10px] rounded-full bg-[#00ca4e] inline-block" />
      </div>
      {/* Code Content Area */}
      <div>{children}</div>
    </div>
  );
}
