import React, { useState } from 'react';
import { GitPullRequest, AlertTriangle, CheckCircle2, FileCode, Copy } from 'lucide-react';

export function RefactorView({ refactor }) {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!refactor) {
    return (
      <div className="p-8 text-center bg-[#0D1117] border border-[#30363D] rounded-[6px] text-[#8B949E] text-xs font-mono">
        No refactoring payload returned from server.
      </div>
    );
  }

  const files = refactor.files || [];
  const activeItem = files[selectedIdx] || null;

  const handleCopyCode = (code) => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-[#30363D]">
        <div className="flex items-center gap-2">
          <GitPullRequest className="w-4 h-4 text-[#58A6FF]" />
          <h3 className="text-sm font-semibold text-[#E6EDF3]">
            Refactor Proposals ({files.length} files)
          </h3>
        </div>

        {/* File selector navigation */}
        {files.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {files.map((f, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedIdx(idx)}
                className={`px-2.5 py-1 rounded-[4px] text-xs font-mono transition-fast ${
                  selectedIdx === idx
                    ? 'bg-[#1C2129] border border-[#58A6FF] text-[#58A6FF] font-semibold'
                    : 'bg-[#0D1117] border border-[#30363D] text-[#8B949E] hover:text-[#E6EDF3]'
                }`}
              >
                {f.original_file || `file_${idx + 1}`}
              </button>
            ))}
          </div>
        )}
      </div>

      {files.length === 0 ? (
        <div className="p-8 text-center bg-[#0D1117] border border-[#30363D] rounded-[6px] text-[#8B949E] text-xs font-mono">
          No refactored files provided in payload.
        </div>
      ) : activeItem ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Refactored Code Viewer (2 cols) */}
          <div className="lg:col-span-2 bg-[#161B22] border border-[#30363D] rounded-[6px] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between px-3 py-2 bg-[#0D1117] border-b border-[#30363D]">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-[#58A6FF]" />
                <code className="text-xs font-mono font-bold text-[#E6EDF3]">
                  {activeItem.original_file || 'Target File'}
                </code>
              </div>

              <button
                onClick={() => handleCopyCode(activeItem.refactored_source)}
                className="flex items-center gap-1 text-[11px] text-[#8B949E] hover:text-[#E6EDF3] font-mono"
              >
                <Copy className="w-3.5 h-3.5" />
                <span>{copied ? 'Copied' : 'Copy Code'}</span>
              </button>
            </div>

            <div className="p-4 bg-[#0D1117] font-mono text-xs text-[#E6EDF3] overflow-x-auto max-h-[480px] leading-relaxed">
              <pre>
                <code>{activeItem.refactored_source || '// No refactored source available.'}</code>
              </pre>
            </div>
          </div>

          {/* Breaking Changes Itemized Panel (1 col) */}
          <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363D]">
                <h4 className="text-xs font-semibold text-[#E6EDF3] uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-[#D29922]" />
                  Breaking Changes
                </h4>
                <span className="text-[10px] font-mono text-[#8B949E]">
                  {activeItem.breaking_changes?.length || 0} ITEMS
                </span>
              </div>

              {activeItem.breaking_changes && activeItem.breaking_changes.length > 0 ? (
                <div className="space-y-2.5">
                  {activeItem.breaking_changes.map((change, cIdx) => (
                    <div
                      key={cIdx}
                      className="p-3 rounded-[4px] bg-[#D29922]/10 border border-[#D29922]/30 text-[#D29922] text-xs flex items-start gap-2"
                    >
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span className="leading-relaxed font-sans">{change}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center bg-[#0D1117] border border-[#30363D] rounded-[4px]">
                  <CheckCircle2 className="w-6 h-6 text-[#3FB950] mx-auto mb-2" />
                  <p className="text-xs font-semibold text-[#E6EDF3]">No Breaking Changes</p>
                  <p className="text-[11px] text-[#8B949E] mt-1">
                    Backward-compatible signature preservation verified.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
