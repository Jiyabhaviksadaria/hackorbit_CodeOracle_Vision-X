import React, { useState, useEffect } from 'react';
import { FileCode, FunctionSquare, Search, Layers, X, BookOpen, ChevronRight, Info, CheckCircle2, Shield } from 'lucide-react';
import { EmptyState } from './EmptyState';

// Module Detail Pop-Up Modal Component
function ModuleDetailModal({ module, allFunctions, onClose, themeMode }) {
  const isFun = themeMode === 'fun';

  // ESC key handler to close modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!module) return null;

  // Filter functions belonging to this specific module file
  const moduleFunctions = (allFunctions || []).filter(
    (fn) => fn.file === module.file
  );

  return (
    <div
      className="fixed inset-0 bg-[#000000]/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in select-none"
      onClick={onClose}
    >
      <div
        className={`max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden font-sans ${
          isFun
            ? 'bg-[#FFFFFF] border-[3.5px] border-[#000000] rounded-[10px] shadow-[8px_8px_0px_#000000]'
            : 'bg-[#1C2129] border border-[#30363D] rounded-[6px] shadow-2xl'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className={`flex items-center justify-between px-5 py-4 border-b ${
          isFun
            ? 'bg-[#ff3e00] border-[#000000] text-white border-b-[3.5px]'
            : 'bg-[#161B22] border-[#30363D]'
        }`}>
          <div className="flex items-center gap-2.5">
            <div className={`w-8 h-8 rounded-[6px] flex items-center justify-center ${
              isFun ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] shadow-[2px_2px_0px_#000000]' : 'bg-[#58A6FF]/10 border border-[#58A6FF]/30 text-[#58A6FF]'
            }`}>
              <FileCode className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div>
              <span className={`text-[10px] font-mono uppercase tracking-wider font-extrabold ${
                isFun ? 'text-[#FEF3C7]' : 'text-[#8B949E]'
              }`}>
                {isFun ? '★ MODULE DEEP DIVE ★' : 'MODULE EXPLANATION & DEEP DIVE'}
              </span>
              <h3 className={`text-sm font-mono font-bold leading-snug ${
                isFun ? 'text-[#FFFFFF] uppercase' : 'text-[#E6EDF3]'
              }`}>
                {module.file}
              </h3>
            </div>
          </div>

          <button
            onClick={onClose}
            className={`p-1 rounded-[4px] border transition-fast cursor-pointer ${
              isFun
                ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] hover:bg-[#FEF3C7] shadow-[2px_2px_0px_#000000]'
                : 'text-[#8B949E] hover:text-[#E6EDF3] hover:bg-[#0D1117] border-transparent'
            }`}
            title="Close (ESC)"
          >
            <X className="w-4 h-4 stroke-[3]" />
          </button>
        </div>

        {/* Modal Body (Scrollable) */}
        <div className={`p-6 overflow-y-auto space-y-6 text-xs leading-relaxed ${
          isFun ? 'bg-[#FFFBEB]' : 'bg-transparent'
        }`}>
          {/* Section 1: Natural Language Summary */}
          <div className="space-y-2">
            <h4 className={`text-[11px] font-mono font-extrabold uppercase tracking-wider flex items-center gap-1.5 ${
              isFun ? 'text-[#050505]' : 'text-[#8B949E]'
            }`}>
              <BookOpen className={`w-3.5 h-3.5 ${isFun ? 'text-[#ff3e00]' : 'text-[#58A6FF]'}`} />
              Natural Language Summary
            </h4>
            <div className={`p-4 rounded-[6px] text-xs leading-relaxed ${
              isFun
                ? 'bg-[#FFFFFF] border-2 border-[#000000] shadow-[3px_3px_0px_#000000] text-[#050505] font-medium'
                : 'bg-[#0D1117] border border-[#30363D] text-[#E6EDF3]'
            }`}>
              {module.summary || 'No detailed summary provided for this module.'}
            </div>
          </div>

          {/* Section 2: What You Need to Know */}
          <div className="space-y-2">
            <h4 className={`text-[11px] font-mono font-extrabold uppercase tracking-wider flex items-center gap-1.5 ${
              isFun ? 'text-[#050505]' : 'text-[#8B949E]'
            }`}>
              <Info className={`w-3.5 h-3.5 ${isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]'}`} />
              Everything Required to Understand This Code
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className={`p-3 rounded-[6px] space-y-1 ${
                isFun
                  ? 'bg-[#FFFFFF] border-2 border-[#000000] shadow-[3px_3px_0px_#000000]'
                  : 'bg-[#0D1117] border border-[#30363D]'
              }`}>
                <span className={`text-[10px] font-mono uppercase font-black block ${
                  isFun ? 'text-[#ff3e00]' : 'text-[#3FB950]'
                }`}>
                  CORE RESPONSIBILITY
                </span>
                <p className={`text-[11px] ${isFun ? 'text-[#050505] font-semibold' : 'text-[#8B949E]'}`}>
                  Encapsulates domain logic for <code className={isFun ? 'text-[#4d61ff] font-bold' : 'text-[#E6EDF3]'}>{module.file}</code>, keeping external dependencies isolated.
                </p>
              </div>

              <div className={`p-3 rounded-[6px] space-y-1 ${
                isFun
                  ? 'bg-[#FFFFFF] border-2 border-[#000000] shadow-[3px_3px_0px_#000000]'
                  : 'bg-[#0D1117] border border-[#30363D]'
              }`}>
                <span className={`text-[10px] font-mono uppercase font-black block ${
                  isFun ? 'text-[#4d61ff]' : 'text-[#58A6FF]'
                }`}>
                  FUNCTION COUNT
                </span>
                <p className={`text-[11px] ${isFun ? 'text-[#050505] font-semibold' : 'text-[#8B949E]'}`}>
                  Contains <code className={isFun ? 'text-[#ff3e00] font-bold' : 'text-[#E6EDF3]'}>{moduleFunctions.length}</code> explicit function signature(s) exported for system orchestration.
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Functions Defined in This Module */}
          <div className="space-y-3">
            <div className={`flex items-center justify-between pb-1 border-b ${
              isFun ? 'border-[#000000] border-b-2' : 'border-[#30363D]'
            }`}>
              <h4 className={`text-[11px] font-mono font-extrabold uppercase tracking-wider flex items-center gap-1.5 ${
                isFun ? 'text-[#050505]' : 'text-[#8B949E]'
              }`}>
                <FunctionSquare className={`w-3.5 h-3.5 ${isFun ? 'text-[#4d61ff]' : 'text-[#58A6FF]'}`} />
                Module Functions ({moduleFunctions.length})
              </h4>
            </div>

            {moduleFunctions.length === 0 ? (
              <div className={`p-4 text-center rounded-[6px] text-[11px] font-mono ${
                isFun
                  ? 'bg-[#FFFFFF] border-2 border-[#000000] text-[#050505] shadow-[2px_2px_0px_#000000]'
                  : 'bg-[#0D1117] border border-[#30363D] text-[#8B949E]'
              }`}>
                No individual function signatures indexed under this file path.
              </div>
            ) : (
              <div className="space-y-3">
                {moduleFunctions.map((fn, fIdx) => (
                  <div
                    key={fIdx}
                    className={`p-3.5 rounded-[6px] space-y-2 ${
                      isFun
                        ? 'bg-[#FFFFFF] border-2 border-[#000000] shadow-[3px_3px_0px_#000000]'
                        : 'bg-[#0D1117] border border-[#30363D]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5 font-mono">
                        <ChevronRight className={`w-3.5 h-3.5 stroke-[3] ${isFun ? 'text-[#ff3e00]' : 'text-[#58A6FF]'}`} />
                        <code className={`font-bold text-xs ${isFun ? 'text-[#050505]' : 'text-[#E6EDF3]'}`}>{fn.name}</code>
                      </div>
                    </div>

                    <p className={`text-xs ${isFun ? 'text-[#262626] font-medium' : 'text-[#8B949E]'}`}>{fn.summary}</p>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 font-mono text-[11px]">
                      {fn.params !== undefined && fn.params !== null && (
                        <div className={`p-2 rounded-[4px] border ${
                          isFun
                            ? 'bg-[#FEF3C7] border-[#000000] border-2 text-[#050505]'
                            : 'bg-[#161B22] border-[#30363D]'
                        }`}>
                          <span className={`text-[9px] uppercase font-black block mb-0.5 ${
                            isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'
                          }`}>PARAMS</span>
                          <code className={`break-all font-bold ${isFun ? 'text-[#4d61ff]' : 'text-[#58A6FF]'}`}>{fn.params || 'None'}</code>
                        </div>
                      )}

                      {fn.returns !== undefined && fn.returns !== null && (
                        <div className={`p-2 rounded-[4px] border ${
                          isFun
                            ? 'bg-[#FEF3C7] border-[#000000] border-2 text-[#050505]'
                            : 'bg-[#161B22] border-[#30363D]'
                        }`}>
                          <span className={`text-[9px] uppercase font-black block mb-0.5 ${
                            isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'
                          }`}>RETURNS</span>
                          <code className={`break-all font-bold ${isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]'}`}>{fn.returns || 'void'}</code>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className={`px-5 py-3 border-t flex items-center justify-between font-mono text-[11px] ${
          isFun
            ? 'bg-[#FEF3C7] border-[#000000] border-t-2 text-[#050505] font-bold'
            : 'bg-[#161B22] border-[#30363D] text-[#8B949E]'
        }`}>
          <span>Press <code className={isFun ? 'text-[#ff3e00] font-black' : 'text-[#E6EDF3]'}>ESC</code> or click outside to dismiss</span>
          <button
            onClick={onClose}
            className={`px-3 py-1 rounded-[4px] font-bold transition-fast cursor-pointer ${
              isFun
                ? 'bg-[#ff3e00] text-white border-2 border-[#000000] shadow-[2px_2px_0px_#000000] hover:bg-[#ff6d43]'
                : 'bg-[#0D1117] hover:bg-[#1C2129] text-[#E6EDF3] border border-[#30363D]'
            }`}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export function ExplanationView({ explanation, themeMode }) {
  const [activeSubTab, setActiveSubTab] = useState('modules');
  const [search, setSearch] = useState('');
  const [selectedModule, setSelectedModule] = useState(null);

  const isFun = themeMode === 'fun';

  if (!explanation) {
    return (
      <EmptyState
        title="No explanation data"
        message="The analysis pipeline returned no module or function explanations for this codebase."
      />
    );
  }

  const modules = explanation.modules || [];
  const functions = explanation.functions || [];

  const filteredModules = modules.filter(
    (m) =>
      (m.file && m.file.toLowerCase().includes(search.toLowerCase())) ||
      (m.summary && m.summary.toLowerCase().includes(search.toLowerCase()))
  );

  const filteredFunctions = functions.filter(
    (f) =>
      (f.name && f.name.toLowerCase().includes(search.toLowerCase())) ||
      (f.file && f.file.toLowerCase().includes(search.toLowerCase())) ||
      (f.summary && f.summary.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Pop-up Modal */}
      {selectedModule && (
        <ModuleDetailModal
          module={selectedModule}
          allFunctions={functions}
          onClose={() => setSelectedModule(null)}
          themeMode={themeMode}
        />
      )}

      {/* Sub Header & Search Filter */}
      <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b ${
        isFun ? 'border-[#000000] border-b-2' : 'border-[#30363D]'
      }`}>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveSubTab('modules')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-[4px] text-xs font-extrabold border transition-fast cursor-pointer ${
              activeSubTab === 'modules'
                ? isFun
                  ? 'bg-[#ff3e00] text-white border-2 border-[#000000] shadow-[2px_2px_0px_#000000]'
                  : 'bg-[#1C2129] border-[#58A6FF] text-[#58A6FF]'
                : isFun
                  ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] hover:bg-[#FEF3C7]'
                  : 'bg-[#0D1117] border-[#30363D] text-[#8B949E] hover:text-[#E6EDF3]'
            }`}
          >
            <Layers className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Modules ({modules.length})</span>
          </button>

          <button
            onClick={() => setActiveSubTab('functions')}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-[4px] text-xs font-extrabold border transition-fast cursor-pointer ${
              activeSubTab === 'functions'
                ? isFun
                  ? 'bg-[#ff3e00] text-white border-2 border-[#000000] shadow-[2px_2px_0px_#000000]'
                  : 'bg-[#1C2129] border-[#58A6FF] text-[#58A6FF]'
                : isFun
                  ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] hover:bg-[#FEF3C7]'
                  : 'bg-[#0D1117] border-[#30363D] text-[#8B949E] hover:text-[#E6EDF3]'
            }`}
          >
            <FunctionSquare className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>Functions ({functions.length})</span>
          </button>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className={`w-3.5 h-3.5 absolute left-3 top-2.5 ${isFun ? 'text-[#000000]' : 'text-[#8B949E]'}`} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={`Filter ${activeSubTab}...`}
            className={`w-full rounded-[4px] pl-8 pr-3 py-1.5 text-xs font-mono font-bold border focus:outline-none ${
              isFun
                ? 'bg-[#FFFFFF] border-2 border-[#000000] text-[#050505] focus:border-[#ff3e00] shadow-[2px_2px_0px_#000000]'
                : 'bg-[#0D1117] border-[#30363D] text-[#E6EDF3] focus:border-[#58A6FF]'
            }`}
          />
        </div>
      </div>

      {/* Modules List View (Neo-Brutalist Uiverse Style in Fun Mode) */}
      {activeSubTab === 'modules' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredModules.length === 0 ? (
            <div className="col-span-2">
              <EmptyState
                title="No matching module summaries"
                message={`No module explanations found matching "${search}".`}
              />
            </div>
          ) : (
            filteredModules.map((mod, idx) => (
              <div
                key={idx}
                onClick={() => setSelectedModule(mod)}
                className={`flex flex-col justify-between transition-fast cursor-pointer group ${
                  isFun
                    ? 'neo-card'
                    : 'bg-[#161B22] border border-[#30363D] hover:border-[#58A6FF] rounded-[6px] p-4'
                }`}
              >
                {isFun ? (
                  /* Uiverse Neo-Brutalist Card Layout */
                  <>
                    <div className="neo-title-banner">
                      <div className="flex items-center gap-2 font-mono text-xs font-extrabold text-white">
                        <FileCode className="w-4 h-4 stroke-[2.5]" />
                        <span>{mod.file || 'module'}</span>
                      </div>
                      <span className="neo-tag">MODULE</span>
                    </div>

                    <div className="p-4 flex-1 flex flex-col justify-between space-y-3 bg-[#FFFFFF]">
                      <p className="text-xs text-[#050505] font-medium leading-relaxed line-clamp-3">
                        {mod.summary}
                      </p>

                      <div className="pt-2 border-t-2 border-dashed border-[#000000]/20 flex items-center justify-between text-[11px] text-[#ff3e00] font-mono font-extrabold">
                        <span>Click for simple explanation & details</span>
                        <ChevronRight className="w-4 h-4 stroke-[3] group-hover:translate-x-1 transition-transform" />
                      </div>
                    </div>
                  </>
                ) : (
                  /* Standard Dark Tech Mode Layout */
                  <>
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex items-center gap-2">
                        <FileCode className="w-4 h-4 text-[#58A6FF] shrink-0 group-hover:text-[#79B8FF]" />
                        <code className="text-xs font-mono font-semibold text-[#E6EDF3] group-hover:text-[#58A6FF]">
                          {mod.file || 'module'}
                        </code>
                      </div>
                      <span className="text-[10px] font-mono uppercase text-[#8B949E] px-1.5 py-0.5 bg-[#0D1117] border border-[#30363D] rounded-[4px] group-hover:border-[#58A6FF]/40">
                        MODULE
                      </span>
                    </div>
                    <p className="text-xs text-[#8B949E] leading-relaxed mt-1 line-clamp-3">
                      {mod.summary}
                    </p>

                    <div className="mt-3 pt-2 border-t border-[#30363D]/60 flex items-center justify-between text-[11px] text-[#58A6FF] font-mono">
                      <span>Click for simple explanation & details</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {/* Functions List View */}
      {activeSubTab === 'functions' && (
        <div className="space-y-3">
          {filteredFunctions.length === 0 ? (
            <EmptyState
              title="No matching function summaries"
              message={`No function explanations found matching "${search}".`}
            />
          ) : (
            filteredFunctions.map((fn, idx) => (
              <div
                key={idx}
                className={`p-4 space-y-3 ${
                  isFun
                    ? 'neo-card'
                    : 'bg-[#161B22] border border-[#30363D] rounded-[6px]'
                }`}
              >
                <div className={`flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b ${
                  isFun ? 'border-[#000000] border-b-2' : 'border-[#30363D]'
                }`}>
                  <div className="flex items-center gap-2">
                    <FunctionSquare className={`w-4 h-4 stroke-[2.5] ${isFun ? 'text-[#ff3e00]' : 'text-[#58A6FF]'}`} />
                    <code className={`text-xs font-mono font-extrabold ${isFun ? 'text-[#050505]' : 'text-[#E6EDF3]'}`}>{fn.name || 'fn'}</code>
                  </div>
                  {fn.file && (
                    <code className={`text-[11px] font-mono px-2 py-0.5 rounded-[4px] border ${
                      isFun
                        ? 'bg-[#FEF3C7] text-[#000000] border-2 border-[#000000] font-bold shadow-[2px_2px_0px_#000000]'
                        : 'text-[#8B949E] bg-[#0D1117] border-[#30363D]'
                    }`}>
                      {fn.file}
                    </code>
                  )}
                </div>

                <p className={`text-xs leading-relaxed ${isFun ? 'text-[#050505] font-medium' : 'text-[#E6EDF3]'}`}>{fn.summary}</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                  {fn.params !== undefined && fn.params !== null && (
                    <div className={`p-2 rounded-[4px] border ${
                      isFun
                        ? 'bg-[#FEF3C7] border-2 border-[#000000] text-[#050505]'
                        : 'bg-[#0D1117] border-[#30363D]'
                    }`}>
                      <span className={`text-[10px] uppercase font-mono font-black block mb-0.5 ${
                        isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'
                      }`}>
                        PARAMETERS
                      </span>
                      <code className={`text-xs font-mono break-all font-bold ${isFun ? 'text-[#4d61ff]' : 'text-[#58A6FF]'}`}>
                        {fn.params || 'None'}
                      </code>
                    </div>
                  )}

                  {fn.returns !== undefined && fn.returns !== null && (
                    <div className={`p-2 rounded-[4px] border ${
                      isFun
                        ? 'bg-[#FEF3C7] border-2 border-[#000000] text-[#050505]'
                        : 'bg-[#0D1117] border-[#30363D]'
                    }`}>
                      <span className={`text-[10px] uppercase font-mono font-black block mb-0.5 ${
                        isFun ? 'text-[#ff3e00]' : 'text-[#8B949E]'
                      }`}>
                        RETURN TYPE
                      </span>
                      <code className={`text-xs font-mono break-all font-bold ${isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]'}`}>
                        {fn.returns || 'void'}
                      </code>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
