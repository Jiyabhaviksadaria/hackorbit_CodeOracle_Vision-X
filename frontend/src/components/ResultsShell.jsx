import React, { useState } from 'react';
import { ProgressRail } from './ProgressRail';
import { TruckLoader } from './TruckLoader';
import { ExplanationTab } from './ExplanationTab';
import { GraphTab } from './GraphTab';
import { TestsTab } from './TestsTab';
import { RefactorTab } from './RefactorTab';
import { AlertTriangle, Layers, GitGraph, TestTube2, GitPullRequest, ArrowLeft } from 'lucide-react';

const TABS = [
  { id: 'explanation', label: 'Explanation 🧠', icon: Layers },
  { id: 'graph', label: 'Dependency Graph 🕸️', icon: GitGraph },
  { id: 'tests', label: 'Tests 🧪', icon: TestTube2 },
  { id: 'refactor', label: 'Refactored Code 🚀', icon: GitPullRequest }
];

export function ResultsShell({ jobId, status, progress, error, resultData, onReset, themeMode }) {
  const [activeTabId, setActiveTabId] = useState('explanation');

  const isDone = status === 'done';
  const isFun = themeMode === 'fun';

  const isSectionMissing = (tabId) => {
    if (!resultData) return false;
    if (tabId === 'explanation') {
      const exp = resultData.explanation;
      return !exp || (!exp.modules?.length && !exp.functions?.length);
    }
    if (tabId === 'graph') {
      const g = resultData.dependency_graph;
      return !g || !g.nodes?.length;
    }
    if (tabId === 'tests') {
      const t = resultData.tests;
      return !t || (!t.test_files?.length && t.coverage_percent === undefined);
    }
    if (tabId === 'refactor') {
      const r = resultData.refactor;
      return !r || !r.files?.length;
    }
    return false;
  };

  return (
    <div className="w-full min-h-[calc(100vh-3.5rem)] flex flex-col">
      {/* Prominent Full-Width Progress Rail */}
      <ProgressRail
        jobId={jobId}
        status={status}
        progress={progress}
        error={error}
        themeMode={themeMode}
      />

      {/* Main View Area */}
      <div className="flex-1 max-w-[1400px] w-full mx-auto px-4 sm:px-6 py-6 space-y-6">
        {status === 'expired' ? (
          <div className={`rounded-[6px] p-8 shadow-xl border-2 text-center max-w-lg mx-auto space-y-4 my-8 ${
            isFun ? 'bg-[#FFFFFF] border-[#212121] shadow-[4px_4px_0px_#E53935]' : 'bg-[#161B22] border-[#30363D]'
          }`}>
            <div className={`w-12 h-12 rounded-[6px] flex items-center justify-center mx-auto border-2 ${
              isFun ? 'bg-[#FEF3C7] text-[#E53935] border-[#212121]' : 'bg-[#D29922]/10 border-[#D29922]/30 text-[#D29922]'
            }`}>
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className={`text-base font-bold ${isFun ? 'text-[#212121]' : 'text-[#E6EDF3]'}`}>
              Analysis Session Expired
            </h3>
            <p className={`text-xs leading-relaxed ${isFun ? 'text-[#374151]' : 'text-[#8B949E]'}`}>
              {error || 'Your previous analysis session has expired or is no longer available on the server. Please start a new analysis.'}
            </p>
            <button
              onClick={onReset}
              className={`flex items-center gap-1.5 mx-auto px-4 py-2 text-xs font-bold rounded-[4px] border-2 transition-fast cursor-pointer ${
                isFun
                  ? 'bg-[#E53935] text-white border-[#212121] shadow-[2px_2px_0px_#212121]'
                  : 'bg-[#58A6FF] text-[#0D1117] border-transparent hover:bg-[#58A6FF]/80 font-mono'
              }`}
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Analyze Another Repository</span>
            </button>
          </div>
        ) : !isDone ? (
          <div className="space-y-6">
            <div className={`rounded-[6px] p-6 shadow-xl border-2 ${
              isFun ? 'bg-[#FFFFFF] border-[#212121] shadow-[4px_4px_0px_#E53935]' : 'bg-[#161B22] border-[#30363D]'
            }`}>
              <TruckLoader text={isFun ? "🚚 Code Delivery Truck in Action! 🔥" : "Your code is loading..."} />
            </div>

            <div className="space-y-6 opacity-60 pointer-events-none select-none">
              <div className={`p-2 rounded-[6px] flex items-center justify-between border-2 ${
                isFun ? 'bg-[#FEF3C7] border-[#212121]' : 'bg-[#161B22] border-[#30363D]'
              }`}>
                <div className="flex items-center gap-2">
                  {TABS.map((tab) => (
                    <div
                      key={tab.id}
                      className={`flex items-center gap-2 px-3 py-1.5 rounded-[4px] border-2 text-xs font-mono font-bold ${
                        isFun ? 'bg-[#FFFFFF] border-[#212121] text-[#212121]' : 'bg-[#0D1117] border-[#30363D] text-[#8B949E]'
                      }`}
                    >
                      <tab.icon className="w-3.5 h-3.5" />
                      <span>{tab.label}</span>
                    </div>
                  ))}
                </div>
                <span className={`text-[11px] font-mono font-black px-2 py-1 rounded-[4px] border-2 ${
                  isFun ? 'bg-[#E53935] text-white border-[#212121]' : 'bg-[#0D1117] text-[#8B949E] border-[#30363D]'
                }`}>
                  PIPELINE IN PROGRESS
                </span>
              </div>

              <div className={`rounded-[6px] p-6 space-y-4 animate-pulse border-2 ${
                isFun ? 'bg-[#FFFFFF] border-[#212121]' : 'bg-[#161B22] border-[#30363D]'
              }`}>
                <div className={`h-4 w-48 rounded-[4px] ${isFun ? 'bg-[#FEF3C7]' : 'bg-[#30363D]'}`} />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  <div className={`h-32 rounded-[6px] p-4 space-y-2 border-2 ${
                    isFun ? 'bg-[#FEF3C7] border-[#212121]' : 'bg-[#0D1117] border-[#30363D]'
                  }`}>
                    <div className={`h-3 w-3/4 rounded-[4px] ${isFun ? 'bg-[#E53935]' : 'bg-[#30363D]'}`} />
                    <div className={`h-3 w-1/2 rounded-[4px] ${isFun ? 'bg-[#212121]' : 'bg-[#30363D]'}`} />
                  </div>
                  <div className={`h-32 rounded-[6px] p-4 space-y-2 border-2 ${
                    isFun ? 'bg-[#FEF3C7] border-[#212121]' : 'bg-[#0D1117] border-[#30363D]'
                  }`}>
                    <div className={`h-3 w-2/3 rounded-[4px] ${isFun ? 'bg-[#E53935]' : 'bg-[#30363D]'}`} />
                    <div className={`h-3 w-1/3 rounded-[4px] ${isFun ? 'bg-[#212121]' : 'bg-[#30363D]'}`} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Sticky Tab Bar */}
            <div className={`sticky top-14 z-40 rounded-[6px] p-1.5 flex flex-wrap items-center justify-between gap-4 shadow-lg border-2 ${
              isFun ? 'bg-[#FDD835] border-[#212121] shadow-[3px_3px_0px_#212121]' : 'bg-[#161B22] border-[#30363D]'
            }`}>
              <div className="flex items-center gap-1 relative">
                {TABS.map((tab) => {
                  const IconComp = tab.icon;
                  const isActive = activeTabId === tab.id;
                  const missing = isSectionMissing(tab.id);

                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTabId(tab.id)}
                      className={`relative flex items-center gap-2 px-4 py-2 rounded-[4px] text-xs font-bold transition-fast cursor-pointer ${
                        isActive
                          ? isFun
                            ? 'text-white bg-[#E53935] border-2 border-[#212121] shadow-[2px_2px_0px_#212121]'
                            : 'text-[#E6EDF3] bg-[#1C2129]'
                          : isFun
                            ? 'text-[#212121] hover:text-[#E53935] bg-transparent'
                            : 'text-[#8B949E] hover:text-[#E6EDF3] bg-transparent'
                      }`}
                    >
                      <IconComp className={`w-3.5 h-3.5 ${
                        isActive ? (isFun ? 'text-[#FDD835]' : 'text-[#58A6FF]') : (isFun ? 'text-[#212121]' : 'text-[#8B949E]')
                      }`} />
                      <span>{tab.label}</span>

                      {missing && (
                        <span
                          className={`w-2 h-2 rounded-full ${isFun ? 'bg-[#E53935] animate-ping' : 'bg-[#D29922]'}`}
                          title="Section incomplete or missing data"
                        />
                      )}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={onReset}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold rounded-[4px] border-2 transition-fast cursor-pointer ${
                  isFun
                    ? 'bg-[#E53935] text-white border-[#212121] shadow-[2px_2px_0px_#212121]'
                    : 'bg-[#0D1117] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3] border-[#30363D]'
                }`}
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Upload Another Repo</span>
              </button>
            </div>

            {/* Tab Body Container */}
            <div className={`rounded-[6px] p-6 border-2 ${
              isFun ? 'bg-[#FFFFFF] border-[#212121] shadow-[4px_4px_0px_#212121]' : 'bg-[#161B22] border-[#30363D]'
            }`}>
              {isSectionMissing(activeTabId) ? (
                <div className="py-12 px-4 text-center max-w-md mx-auto space-y-3">
                  <div className={`w-10 h-10 rounded-[6px] flex items-center justify-center mx-auto border-2 ${
                    isFun ? 'bg-[#FEF3C7] text-[#E53935] border-[#212121]' : 'bg-[#D29922]/10 border-[#D29922]/30 text-[#D29922]'
                  }`}>
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <h4 className={`text-sm font-bold ${isFun ? 'text-[#212121]' : 'text-[#E6EDF3]'}`}>
                    This section didn't complete
                  </h4>
                  <p className={`text-xs leading-relaxed ${isFun ? 'text-[#374151]' : 'text-[#8B949E]'}`}>
                    The analysis pipeline finished, but data for this specific section was missing or errored during execution. Other sections remain fully accessible.
                  </p>
                </div>
              ) : (
                <>
                  {activeTabId === 'explanation' && (
                    <ExplanationTab explanation={resultData?.explanation} themeMode={themeMode} />
                  )}

                  {activeTabId === 'graph' && (
                    <GraphTab depGraph={resultData?.dependency_graph} themeMode={themeMode} />
                  )}

                  {activeTabId === 'tests' && (
                    <TestsTab tests={resultData?.tests} themeMode={themeMode} />
                  )}

                  {activeTabId === 'refactor' && (
                    <RefactorTab refactor={resultData?.refactor} themeMode={themeMode} />
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
