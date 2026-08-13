import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { AlertTriangle, CheckCircle2, FileCode, Copy, Check } from 'lucide-react';
import { EmptyState } from './EmptyState';
import { CodeCard } from './CodeCard';

export function RefactorTab({ refactor, themeMode }) {
  const [selectedFileIdx, setSelectedFileIdx] = useState(0);
  const [copied, setCopied] = useState(false);

  const isFun = themeMode === 'fun';

  const files = refactor?.files || [];

  if (!files.length) {
    return (
      <EmptyState
        title="No refactored files available"
        message="The refactoring engine returned no modernized files for this job."
      />
    );
  }

  const selectedItem = files[selectedFileIdx] || files[0];
  const breakingChanges = selectedItem.breaking_changes || [];
  const hasBreaking = breakingChanges.length > 0;

  const handleCopyCode = (sourceCode) => {
    navigator.clipboard.writeText(sourceCode || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col md:flex-row gap-6">
      {/* Left Column: File Selector List */}
      <div className="w-full md:w-64 shrink-0 space-y-2">
        <h4 className={`text-xs font-mono font-black uppercase tracking-wider ${
          isFun ? 'text-[#050505]' : 'text-[#8B949E]'
        }`}>
          Refactored Files ({files.length})
        </h4>

        <div className="flex md:flex-col overflow-x-auto md:overflow-x-visible gap-2 pb-2 md:pb-0">
          {files.map((fileObj, idx) => {
            const isSelected = selectedFileIdx === idx;
            const bCount = (fileObj.breaking_changes || []).length;

            return (
              <button
                key={idx}
                onClick={() => setSelectedFileIdx(idx)}
                className={`w-full text-left p-3 rounded-[6px] transition-fast cursor-pointer flex flex-col gap-1 shrink-0 md:shrink border ${
                  isSelected
                    ? isFun
                      ? 'bg-[#ff3e00] text-white border-2 border-[#000000] shadow-[3px_3px_0px_#000000]'
                      : 'bg-[#1C2129] border-[#58A6FF] text-[#E6EDF3]'
                    : isFun
                      ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] hover:bg-[#FEF3C7] shadow-[2px_2px_0px_#000000]'
                      : 'bg-[#0D1117] border-[#30363D] text-[#8B949E] hover:text-[#E6EDF3]'
                }`}
              >
                <div className="flex items-center gap-2 font-mono text-xs font-bold">
                  <FileCode className="w-3.5 h-3.5 stroke-[2.5]" />
                  <span className="truncate">{fileObj.original_file}</span>
                </div>

                {bCount > 0 ? (
                  <span className={`text-[10px] font-mono font-extrabold ${
                    isSelected ? (isFun ? 'text-[#FEF3C7]' : 'text-[#D29922]') : (isFun ? 'text-[#ff3e00]' : 'text-[#D29922]')
                  }`}>
                    ⚠️ {bCount} breaking change{bCount > 1 ? 's' : ''}
                  </span>
                ) : (
                  <span className={`text-[10px] font-mono font-bold ${
                    isSelected ? (isFun ? 'text-white' : 'text-[#3FB950]') : (isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]')
                  }`}>
                    ✓ Clean refactor
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Right Column: Code & Breaking Changes Banner */}
      <div className="flex-1 space-y-4">
        {/* Breaking Changes Banner (Itemized line-by-line ABOVE code) */}
        {hasBreaking ? (
          <div className={`p-4 rounded-[6px] space-y-2 border-2 ${
            isFun
              ? 'bg-[#FEF3C7] border-[#000000] text-[#050505] shadow-[4px_4px_0px_#000000]'
              : 'bg-[#D29922]/10 border-[#D29922]/40 text-[#D29922]'
          }`}>
            <div className="flex items-center gap-2 font-mono font-black text-xs uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 stroke-[3] text-[#ff3e00]" />
              <span>{breakingChanges.length} Breaking Changes Detected</span>
            </div>

            <ul className="space-y-1 font-mono text-xs pl-6 list-disc font-semibold">
              {breakingChanges.map((change, cIdx) => (
                <li key={cIdx}>{change}</li>
              ))}
            </ul>
          </div>
        ) : (
          <div className={`p-3 rounded-[6px] flex items-center gap-2 font-mono text-xs font-bold border-2 ${
            isFun
              ? 'bg-[#FFFFFF] border-[#000000] text-[#00e0b0] shadow-[3px_3px_0px_#000000]'
              : 'bg-[#3FB950]/10 border-[#3FB950]/30 text-[#3FB950]'
          }`}>
            <CheckCircle2 className="w-4 h-4 stroke-[3]" />
            <span>No breaking changes detected</span>
          </div>
        )}

        {/* Code Block Container wrapped in terminal card */}
        <CodeCard className={isFun ? 'shadow-[4px_4px_0px_#000000] border-2 border-[#000000]' : ''}>
          {/* Header */}
          <div className={`p-3 flex items-center justify-between border-b-2 ${
            isFun
              ? 'bg-[#ff3e00] border-[#000000] text-white'
              : 'bg-[#1C2129] border-[#30363D] text-[#E6EDF3]'
          }`}>
            <div className="flex items-center gap-2 font-mono text-xs font-extrabold">
              <FileCode className="w-4 h-4 stroke-[2.5]" />
              <span>{selectedItem.original_file}</span>
              <span className={`text-[10px] font-mono font-black px-2 py-0.5 rounded-[4px] border ${
                isFun
                  ? 'bg-[#FFFFFF] text-[#000000] border-[#000000]'
                  : 'text-[#8B949E] bg-[#0D1117] border-[#30363D]'
              }`}>
                showing modernized version
              </span>
            </div>

            <button
              onClick={() => handleCopyCode(selectedItem.refactored_source)}
              className={`flex items-center gap-1.5 px-3 py-1 text-xs font-mono font-extrabold rounded-[4px] border transition-fast cursor-pointer ${
                isFun
                  ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] shadow-[2px_2px_0px_#000000]'
                  : 'bg-[#0D1117] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3] border-[#30363D]'
              }`}
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-[#10B981] stroke-[3]" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 stroke-[2.5]" />
                  <span>Copy Refactored Code</span>
                </>
              )}
            </button>
          </div>

          {/* Monaco Code Viewer */}
          <div className="h-[420px] w-full">
            <Editor
              height="100%"
              defaultLanguage="python"
              theme="vs-dark"
              value={selectedItem.refactored_source || '# Modernized code output'}
              options={{
                readOnly: true,
                minimap: { enabled: false },
                fontSize: 12,
                fontFamily: 'JetBrains Mono',
                scrollBeyondLastLine: false,
                lineNumbers: 'on',
                folding: true,
                domReadOnly: true,
              }}
            />
          </div>
        </CodeCard>
      </div>
    </div>
  );
}
