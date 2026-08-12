import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, ShieldCheck, Terminal, Copy, Check } from 'lucide-react';
import { EmptyState } from './EmptyState';
import { CodeCard } from './CodeCard';

export function TestsTab({ tests, themeMode }) {
  const [expandedFileIdx, setExpandedFileIdx] = useState(0);
  const [showFullLog, setShowFullLog] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);

  const isFun = themeMode === 'fun';

  if (!tests || (!tests.test_files?.length && tests.coverage_percent === undefined)) {
    return (
      <EmptyState
        title="No test results generated"
        message="The test generation stage was skipped or produced zero output files."
      />
    );
  }

  const coverage = tests.coverage_percent ?? 0;
  const passedCount = tests.passed ?? 0;
  const failedCount = tests.failed ?? 0;
  const testFiles = tests.test_files || [];
  const logContent = tests.log || 'No detailed execution log available.';

  // PS-06 threshold requirement: >= 60% coverage is success
  const isCoverageGood = coverage >= 60;

  const handleCopyCode = (sourceCode, idx) => {
    navigator.clipboard.writeText(sourceCode);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Stat Row: 3 Compact Cards (Neo-Brutalist in Fun Mode) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Stat Card 1: Coverage */}
        <div className={`p-4 rounded-[6px] space-y-3 transition-fast ${
          isFun
            ? 'neo-card'
            : 'bg-[#161B22] border border-[#30363D]'
        }`}>
          {isFun && (
            <div className="neo-title-banner text-xs">
              <span>COVERAGE METRIC</span>
              <span className="neo-tag">PS-06</span>
            </div>
          )}

          <div className={isFun ? 'p-4 space-y-3 bg-[#FFFFFF]' : 'space-y-3'}>
            <div className="flex items-center justify-between">
              <span className={`text-[11px] font-mono uppercase font-black tracking-wider ${
                isFun ? 'text-[#050505]' : 'text-[#8B949E]'
              }`}>
                COVERAGE
              </span>
              <ShieldCheck className={`w-4 h-4 stroke-[2.5] ${
                isCoverageGood ? (isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]') : (isFun ? 'text-[#ff3e00]' : 'text-[#D29922]')
              }`} />
            </div>

            <div className="flex items-baseline gap-2">
              <span className={`text-3xl font-mono font-black ${
                isCoverageGood ? (isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]') : (isFun ? 'text-[#ff3e00]' : 'text-[#D29922]')
              }`}>
                {coverage.toFixed(1)}%
              </span>
            </div>

            {/* Thin Horizontal Progress Bar */}
            <div className={`w-full h-2 rounded-full overflow-hidden border ${
              isFun ? 'bg-[#FEF3C7] border-[#000000] border-2' : 'bg-[#0D1117] border-[#30363D]'
            }`}>
              <div
                className={`h-full transition-all ${
                  isCoverageGood ? (isFun ? 'bg-[#00e0b0]' : 'bg-[#3FB950]') : (isFun ? 'bg-[#ff3e00]' : 'bg-[#D29922]')
                }`}
                style={{ width: `${Math.min(100, Math.max(0, coverage))}%` }}
              />
            </div>

            <p className={`text-[11px] font-mono font-bold ${isFun ? 'text-[#262626]' : 'text-[#8B949E]'}`}>
              {isCoverageGood ? 'Target ≥ 60% satisfied' : 'Target ≥ 60% below threshold'}
            </p>
          </div>
        </div>

        {/* Stat Card 2: Passed */}
        <div className={`p-4 rounded-[6px] space-y-3 transition-fast ${
          isFun
            ? 'neo-card'
            : 'bg-[#161B22] border border-[#30363D]'
        }`}>
          {isFun && (
            <div className="neo-title-banner text-xs !bg-[#00e0b0] !text-[#000000]">
              <span>PASSED SUITE</span>
              <span className="neo-tag">PASSED</span>
            </div>
          )}

          <div className={isFun ? 'p-4 space-y-3 bg-[#FFFFFF]' : 'space-y-3'}>
            <div className="flex items-center justify-between">
              <span className={`text-[11px] font-mono uppercase font-black tracking-wider ${
                isFun ? 'text-[#050505]' : 'text-[#8B949E]'
              }`}>
                PASSED
              </span>
              <CheckCircle2 className={`w-4 h-4 stroke-[2.5] ${isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]'}`} />
            </div>

            <div className="flex items-baseline gap-2">
              <span className={`text-3xl font-mono font-black ${isFun ? 'text-[#00e0b0]' : 'text-[#3FB950]'}`}>
                {passedCount}
              </span>
            </div>

            <p className={`text-[11px] font-mono font-bold ${isFun ? 'text-[#262626]' : 'text-[#8B949E]'}`}>
              Verified test assertions
            </p>
          </div>
        </div>

        {/* Stat Card 3: Failed */}
        <div className={`p-4 rounded-[6px] space-y-3 transition-fast ${
          isFun
            ? 'neo-card'
            : 'bg-[#161B22] border border-[#30363D]'
        }`}>
          {isFun && (
            <div className={`neo-title-banner text-xs ${failedCount > 0 ? '!bg-[#ff3e00]' : '!bg-[#4d61ff]'}`}>
              <span>FAILURES</span>
              <span className="neo-tag">{failedCount > 0 ? 'FAIL' : 'OK'}</span>
            </div>
          )}

          <div className={isFun ? 'p-4 space-y-3 bg-[#FFFFFF]' : 'space-y-3'}>
            <div className="flex items-center justify-between">
              <span className={`text-[11px] font-mono uppercase font-black tracking-wider ${
                isFun ? 'text-[#050505]' : 'text-[#8B949E]'
              }`}>
                FAILED
              </span>
              <XCircle className={`w-4 h-4 stroke-[2.5] ${
                failedCount > 0 ? (isFun ? 'text-[#ff3e00]' : 'text-[#F85149]') : (isFun ? 'text-[#262626]' : 'text-[#8B949E]')
              }`} />
            </div>

            <div className="flex items-baseline gap-2">
              <span className={`text-3xl font-mono font-black ${
                failedCount > 0 ? (isFun ? 'text-[#ff3e00]' : 'text-[#F85149]') : (isFun ? 'text-[#050505]' : 'text-[#8B949E]')
              }`}>
                {failedCount}
              </span>
            </div>

            <p className={`text-[11px] font-mono font-bold ${isFun ? 'text-[#262626]' : 'text-[#8B949E]'}`}>
              {failedCount === 0 ? 'Zero test failures' : 'Failing test cases detected'}
            </p>
          </div>
        </div>
      </div>

      {/* Generated Test Files: Code-Forward List */}
      <div className="space-y-3">
        <h4 className={`text-xs font-mono font-black uppercase tracking-wider ${isFun ? 'text-[#050505]' : 'text-[#8B949E]'}`}>
          Generated Test Files ({testFiles.length})
        </h4>

        {testFiles.map((tf, idx) => {
          const isExpanded = expandedFileIdx === idx;
          const lineCount = (tf.source || '').split('\n').length;

          return (
            <div
              key={idx}
              className={`rounded-[6px] overflow-hidden transition-fast ${
                isFun
                  ? 'neo-card'
                  : 'bg-[#161B22] border border-[#30363D]'
              }`}
            >
              {/* File Row Header */}
              <div
                onClick={() => setExpandedFileIdx(isExpanded ? null : idx)}
                className={`p-3.5 flex items-center justify-between cursor-pointer transition-fast ${
                  isFun
                    ? 'bg-[#FEF3C7] border-b-2 border-[#000000] text-[#050505]'
                    : 'bg-[#161B22] border-b border-[#30363D] hover:bg-[#1C2129]'
                }`}
              >
                <div className="flex items-center gap-2 font-mono text-xs font-bold">
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 stroke-[3]" />
                  ) : (
                    <ChevronRight className="w-4 h-4 stroke-[3]" />
                  )}
                  <span>{tf.file}</span>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`text-[11px] font-mono ${isFun ? 'text-[#050505] font-bold' : 'text-[#8B949E]'}`}>
                    {lineCount} lines
                  </span>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopyCode(tf.source, idx);
                    }}
                    className={`flex items-center gap-1 text-[11px] font-mono font-bold px-2 py-1 rounded-[4px] border transition-fast cursor-pointer ${
                      isFun
                        ? 'bg-[#FFFFFF] text-[#000000] border-2 border-[#000000] shadow-[2px_2px_0px_#000000]'
                        : 'bg-[#0D1117] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3] border-[#30363D]'
                    }`}
                  >
                    {copiedIdx === idx ? (
                      <>
                        <Check className="w-3 h-3 text-[#10B981] stroke-[3]" />
                        <span>Copied</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3 h-3 stroke-[2.5]" />
                        <span>Copy</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Monaco Read-Only Code Viewer */}
              {isExpanded && (
                <CodeCard>
                  <div className="h-[280px] w-full">
                    <Editor
                      height="100%"
                      defaultLanguage="python"
                      theme="vs-dark"
                      value={tf.source}
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
              )}
            </div>
          );
        })}
      </div>

      {/* Raw Execution Log Disclosure */}
      <div className={`rounded-[6px] overflow-hidden transition-fast ${
        isFun ? 'neo-card' : 'bg-[#161B22] border border-[#30363D]'
      }`}>
        <button
          onClick={() => setShowFullLog(!showFullLog)}
          className={`w-full p-3.5 flex items-center justify-between text-xs font-mono font-bold cursor-pointer transition-fast ${
            isFun
              ? 'bg-[#FEF3C7] text-[#050505]'
              : 'bg-[#161B22] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3]'
          }`}
        >
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 stroke-[2.5]" />
            <span>View Full Execution Test Log</span>
          </div>
          {showFullLog ? <ChevronDown className="w-4 h-4 stroke-[3]" /> : <ChevronRight className="w-4 h-4 stroke-[3]" />}
        </button>

        {showFullLog && (
          <div className={`p-4 font-mono text-xs overflow-x-auto border-t leading-relaxed max-h-72 ${
            isFun
              ? 'bg-[#FFFFFF] border-t-2 border-[#000000] text-[#050505]'
              : 'bg-[#0D1117] border-[#30363D] text-[#8B949E]'
          }`}>
            <pre className="whitespace-pre-wrap">{logContent}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
