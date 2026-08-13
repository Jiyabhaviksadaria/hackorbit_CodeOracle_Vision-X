import React from 'react';
import { CheckCircle2, AlertTriangle, Loader2, Cpu, FileText, Sparkles, TestTube2, GitBranch } from 'lucide-react';

const STAGES = [
  { id: 'queued', label: 'Queued', icon: Cpu, desc: 'Job initialized' },
  { id: 'parsing', label: 'Parsing AST', icon: FileText, desc: 'Extracting symbols' },
  { id: 'explaining', label: 'Explaining', icon: Sparkles, desc: 'Generating summaries' },
  { id: 'testing', label: 'Testing', icon: TestTube2, desc: 'Running test runner' },
  { id: 'refactoring', label: 'Refactoring', icon: GitBranch, desc: 'Proposing diffs' },
  { id: 'done', label: 'Done', icon: CheckCircle2, desc: 'Analysis complete' }
];

export function ProgressTracker({ jobId, status, progress, error }) {
  const currentStageIndex = STAGES.findIndex((s) => s.id === status);
  const activeIndex = currentStageIndex !== -1 ? currentStageIndex : 0;

  return (
    <div className="max-w-4xl mx-auto mt-8 px-4">
      <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-2xl backdrop-blur-sm">
        {/* Header Job Info */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
          <div>
            <span className="text-[11px] font-mono text-cyan-400 uppercase tracking-widest">Active Analysis Pipeline</span>
            <div className="flex items-center gap-2 mt-1">
              <h3 className="text-lg font-bold text-white">Job ID:</h3>
              <code className="px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-cyan-300">
                {jobId || 'Initializing...'}
              </code>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {status === 'error' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-950 border border-rose-800 text-rose-300 text-xs font-semibold">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                Pipeline Failure
              </span>
            ) : status === 'done' ? (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300 text-xs font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                Completed 100%
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950 border border-cyan-800 text-cyan-300 text-xs font-semibold">
                <Loader2 className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                Status: {status ? status.toUpperCase() : 'QUEUED'}
              </span>
            )}
          </div>
        </div>

        {/* Progress Bar Display */}
        <div className="mb-8">
          <div className="flex items-center justify-between text-xs font-medium mb-2">
            <span className="text-slate-400">Total Pipeline Progress</span>
            <span className="text-cyan-400 font-mono font-bold">{progress || 0}%</span>
          </div>
          <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800 p-0.5">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                status === 'error'
                  ? 'bg-rose-500'
                  : status === 'done'
                  ? 'bg-gradient-to-r from-cyan-400 via-indigo-500 to-emerald-400'
                  : 'bg-gradient-to-r from-cyan-500 to-indigo-500 animate-pulse'
              }`}
              style={{ width: `${Math.min(100, Math.max(0, progress || 0))}%` }}
            />
          </div>
        </div>

        {/* Stepper Pipeline Stage Nodes */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {STAGES.map((stage, idx) => {
            const IconComponent = stage.icon;
            const isCompleted = idx < activeIndex || status === 'done';
            const isCurrent = idx === activeIndex && status !== 'done' && status !== 'error';

            return (
              <div
                key={stage.id}
                className={`relative flex flex-col items-center p-3 rounded-xl border text-center transition-all ${
                  isCompleted
                    ? 'bg-slate-950/80 border-emerald-900/60 text-emerald-400'
                    : isCurrent
                    ? 'bg-cyan-950/40 border-cyan-500/80 text-cyan-300 shadow-md shadow-cyan-500/10'
                    : 'bg-slate-950/30 border-slate-850 text-slate-600'
                }`}
              >
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center mb-2 ${
                    isCompleted
                      ? 'bg-emerald-950 border border-emerald-800 text-emerald-400'
                      : isCurrent
                      ? 'bg-cyan-950 border border-cyan-600 text-cyan-400 animate-bounce'
                      : 'bg-slate-900 border border-slate-800 text-slate-600'
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4" />
                  ) : (
                    <IconComponent className="w-4 h-4" />
                  )}
                </div>
                <span className="text-xs font-semibold tracking-tight">{stage.label}</span>
                <span className="text-[10px] text-slate-500 mt-0.5">{stage.desc}</span>
              </div>
            );
          })}
        </div>

        {/* Error Banner Handler */}
        {error && (
          <div className="mt-6 p-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-rose-300">Pipeline Execution Error</h4>
                <p className="mt-1 font-mono text-[11px] text-rose-200 bg-rose-950/90 p-2 rounded border border-rose-900/80">
                  {error}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
