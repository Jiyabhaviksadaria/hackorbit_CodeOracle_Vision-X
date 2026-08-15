import React from 'react';
import { Check, Loader2, AlertCircle } from 'lucide-react';

const STAGES = [
  { id: 'parsing', label: 'Parsing AST 🧩' },
  { id: 'explaining', label: 'Explaining 🧠' },
  { id: 'testing', label: 'Testing 🧪' },
  { id: 'refactoring', label: 'Refactoring 🚀' }
];

export function ProgressRail({ jobId, status, progress, error, themeMode }) {
  const currentStageIndex = STAGES.findIndex((s) => s.id === status);
  const isDone = status === 'done';
  const isError = status === 'error';
  const isExpired = status === 'expired';
  const isFun = themeMode === 'fun';

  return (
    <div className={`w-full px-4 sm:px-6 py-3 border-b-2 transition-colors ${
      isFun
        ? 'bg-[#FEF3C7] border-[#212121]'
        : 'bg-[#161B22] border-[#30363D]'
    }`}>
      <div className="max-w-[1400px] mx-auto flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Left: Job Meta */}
        <div className="flex items-center gap-3">
          <span className={`text-[11px] font-mono uppercase tracking-wider font-extrabold ${
            isFun ? 'text-[#E53935]' : 'text-[#8B949E]'
          }`}>
            {isFun ? '🔥 JOB TRACKER:' : 'JOB ID:'}
          </span>
          <code className={`text-xs font-mono font-bold px-2 py-0.5 rounded-[4px] border-2 ${
            isFun
              ? 'bg-[#FFFFFF] text-[#212121] border-[#212121] shadow-[2px_2px_0px_#E53935]'
              : 'bg-[#0D1117] text-[#58A6FF] border-[#30363D]'
          }`}>
            {jobId || 'job_initializing'}
          </code>
          {isError && (
            <span className="flex items-center gap-1 text-xs font-bold text-white bg-[#E53935] px-2 py-0.5 rounded-full border-2 border-[#212121] shadow-[2px_2px_0px_#212121]">
              <AlertCircle className="w-3.5 h-3.5" />
              Pipeline Error
            </span>
          )}
          {isExpired && (
            <span className="flex items-center gap-1 text-xs font-bold text-white bg-[#D97706] px-2 py-0.5 rounded-full border-2 border-[#212121] shadow-[2px_2px_0px_#212121]">
              <AlertCircle className="w-3.5 h-3.5" />
              Session Expired
            </span>
          )}
        </div>

        {/* Center: Stage Stepper Rail */}
        <div className="flex-1 max-w-2xl mx-auto flex items-center justify-between gap-1 sm:gap-2">
          {STAGES.map((stage, idx) => {
            const isCompleted = isDone || (currentStageIndex > -1 && idx < currentStageIndex);
            const isActive = !isDone && !isError && currentStageIndex === idx;

            return (
              <React.Fragment key={stage.id}>
                <div className="flex items-center gap-1.5 py-1">
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-mono font-extrabold transition-all border-2 ${
                      isCompleted
                        ? isFun
                          ? 'bg-[#10B981] text-white border-[#212121] shadow-[2px_2px_0px_#212121]'
                          : 'bg-[#3FB950] text-[#0D1117] border-transparent'
                        : isActive
                        ? isFun
                          ? 'bg-[#E53935] text-white border-[#212121] shadow-[2px_2px_0px_#212121] animate-bounce'
                          : 'bg-[#58A6FF] text-[#0D1117] border-transparent ring-2 ring-[#58A6FF]/30'
                        : isFun
                          ? 'bg-[#FDD835] text-[#212121] border-[#212121]'
                          : 'bg-[#0D1117] border-[#30363D] text-[#545D68]'
                    }`}
                  >
                    {isCompleted ? (
                      <Check className="w-3.5 h-3.5 stroke-[3]" />
                    ) : isActive ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin stroke-[3]" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <span
                    className={`text-xs font-bold transition-all ${
                      isCompleted
                        ? isFun
                          ? 'text-[#212121]'
                          : 'text-[#E6EDF3]'
                        : isActive
                        ? isFun
                          ? 'text-[#E53935] font-black'
                          : 'text-[#58A6FF] font-semibold'
                        : isFun
                          ? 'text-slate-600'
                          : 'text-[#545D68]'
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>

                {idx < STAGES.length - 1 && (
                  <div className={`flex-1 h-[3px] overflow-hidden rounded-full border ${
                    isFun ? 'bg-[#FDD835] border-[#212121]' : 'bg-[#30363D] border-transparent'
                  }`}>
                    <div
                      className={`h-full transition-all ${
                        isCompleted
                          ? isFun
                            ? 'bg-[#10B981]'
                            : 'bg-[#3FB950]'
                          : isActive
                          ? isFun
                            ? 'bg-[#E53935] animate-pulse'
                            : 'bg-[#58A6FF] animate-pulse'
                          : 'bg-transparent'
                      }`}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Right: Percentage */}
        <div className="flex items-center gap-2">
          <div className={`w-24 h-2.5 rounded-full overflow-hidden border-2 ${
            isFun ? 'bg-[#FFFFFF] border-[#212121]' : 'bg-[#0D1117] border-[#30363D]'
          }`}>
            <div
              className={`h-full transition-all duration-300 ${
                isError
                  ? 'bg-[#E53935]'
                  : isDone
                  ? isFun
                    ? 'bg-gradient-to-r from-[#E53935] via-[#FDD835] to-[#10B981]'
                    : 'bg-[#3FB950]'
                  : isFun
                    ? 'bg-[#E53935]'
                    : 'bg-[#58A6FF]'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, progress || 0))}%` }}
            />
          </div>
          <span className={`text-xs font-mono font-black w-10 text-right ${
            isFun ? 'text-[#212121]' : 'text-[#E6EDF3]'
          }`}>
            {progress || 0}%
          </span>
        </div>
      </div>

      {error && (
        <div className="mt-2 text-xs font-mono text-white bg-[#E53935] p-2 rounded-[4px] border-2 border-[#212121]">
          Error: {error}
        </div>
      )}
    </div>
  );
}
