import React, { useState } from 'react';
import { TestTube2, Check, X, Terminal, FileCode, Copy } from 'lucide-react';

export function TestResultsView({ tests }) {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [copied, setCopied] = useState(false);

  if (!tests) {
    return (
      <div className="p-8 text-center bg-[#0D1117] border border-[#30363D] rounded-[6px] text-[#8B949E] text-xs font-mono">
        No test runner output payload returned.
      </div>
    );
  }

  const testFiles = tests.test_files || [];
  const activeFile = testFiles[selectedIdx] || null;

  const handleCopyCode = (code) => {
    if (!code) return;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Top Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Coverage Card */}
        <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#8B949E] block">
              COVERAGE
            </span>
            <div className="text-xl font-mono font-bold text-[#3FB950] mt-0.5">
              {tests.coverage_percent !== undefined && tests.coverage_percent !== null
                ? `${tests.coverage_percent}%`
                : 'N/A'}
            </div>
          </div>
          <div className="w-9 h-9 rounded-[4px] bg-[#3FB950]/10 border border-[#3FB950]/30 flex items-center justify-center text-[#3FB950]">
            <TestTube2 className="w-5 h-5" />
          </div>
        </div>

        {/* Passed Count */}
        <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#8B949E] block">
              PASSED
            </span>
            <div className="text-xl font-mono font-bold text-[#3FB950] mt-0.5">
              {tests.passed !== undefined && tests.passed !== null ? tests.passed : '0'}
            </div>
          </div>
          <div className="w-9 h-9 rounded-[4px] bg-[#3FB950]/10 border border-[#3FB950]/30 flex items-center justify-center text-[#3FB950]">
            <Check className="w-5 h-5 stroke-[2.5]" />
          </div>
        </div>

        {/* Failed Count */}
        <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] font-mono uppercase tracking-wider text-[#8B949E] block">
              FAILED
            </span>
            <div className={`text-xl font-mono font-bold mt-0.5 ${tests.failed > 0 ? 'text-[#F85149]' : 'text-[#8B949E]'}`}>
              {tests.failed !== undefined && tests.failed !== null ? tests.failed : '0'}
            </div>
          </div>
          <div className={`w-9 h-9 rounded-[4px] border flex items-center justify-center ${
            tests.failed > 0
              ? 'bg-[#F85149]/10 border-[#F85149]/30 text-[#F85149]'
              : 'bg-[#0D1117] border-[#30363D] text-[#545D68]'
          }`}>
            <X className="w-5 h-5 stroke-[2.5]" />
          </div>
        </div>
      </div>

      {/* Main Split View: Test Files Code & Log Output */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Code Explorer */}
        <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363D]">
              <h4 className="text-xs font-semibold text-[#E6EDF3] uppercase tracking-wider flex items-center gap-2">
                <FileCode className="w-4 h-4 text-[#58A6FF]" />
                Generated Test Files ({testFiles.length})
              </h4>
            </div>

            {testFiles.length === 0 ? (
              <p className="text-xs font-mono text-[#8B949E] py-8 text-center">No test files available.</p>
            ) : (
              <div>
                <div className="flex flex-wrap gap-2 mb-3">
                  {testFiles.map((tf, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedIdx(idx)}
                      className={`px-2.5 py-1 rounded-[4px] text-xs font-mono transition-fast ${
                        selectedIdx === idx
                          ? 'bg-[#1C2129] border border-[#58A6FF] text-[#58A6FF] font-semibold'
                          : 'bg-[#0D1117] border border-[#30363D] text-[#8B949E] hover:text-[#E6EDF3]'
                      }`}
                    >
                      {tf.file || `test_${idx + 1}`}
                    </button>
                  ))}
                </div>

                {activeFile && (
                  <div className="bg-[#0D1117] border border-[#30363D] rounded-[4px] overflow-hidden">
                    <div className="flex items-center justify-between px-3 py-1.5 bg-[#161B22] border-b border-[#30363D]">
                      <code className="text-xs font-mono text-[#58A6FF]">{activeFile.file}</code>
                      <button
                        onClick={() => handleCopyCode(activeFile.source)}
                        className="flex items-center gap-1 text-[11px] text-[#8B949E] hover:text-[#E6EDF3] font-mono"
                      >
                        <Copy className="w-3 h-3" />
                        <span>{copied ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>

                    <pre className="p-3 text-xs font-mono text-[#E6EDF3] overflow-x-auto max-h-[340px] leading-relaxed">
                      <code>{activeFile.source}</code>
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Terminal Execution Log */}
        <div className="bg-[#161B22] border border-[#30363D] rounded-[6px] p-4 flex flex-col">
          <div className="flex items-center justify-between pb-2 mb-3 border-b border-[#30363D]">
            <h4 className="text-xs font-semibold text-[#E6EDF3] uppercase tracking-wider flex items-center gap-2">
              <Terminal className="w-4 h-4 text-[#3FB950]" />
              Execution Output Log
            </h4>
            <span className="text-[10px] font-mono text-[#8B949E]">PYTEST / STDOUT</span>
          </div>

          <div className="flex-1 bg-[#0D1117] border border-[#30363D] rounded-[4px] p-3 font-mono text-xs text-[#E6EDF3] overflow-x-auto max-h-[380px] whitespace-pre-wrap leading-relaxed">
            {tests.log ? (
              tests.log
            ) : (
              <span className="text-[#545D68] italic">No execution logs captured.</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
