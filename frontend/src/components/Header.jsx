import React, { useState } from 'react';
import { Terminal, Server, RefreshCw, Sparkles } from 'lucide-react';

export function Header({ isMock, onToggleMock, baseUrl, onBaseUrlChange, onReset, themeMode, onToggleThemeMode }) {
  const [showConfig, setShowConfig] = useState(false);
  const isFun = themeMode === 'fun';

  return (
    <header className={`border-b sticky top-0 z-50 transition-colors ${
      isFun
        ? 'bg-[#FDD835] border-[#212121] shadow-md'
        : 'bg-[#161B22] border-[#30363D]'
    }`}>
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand & Context */}
        <div className="flex items-center gap-4 cursor-pointer" onClick={onReset}>
          <div className="flex items-center gap-2">
            <div className={`w-8 h-8 rounded-[6px] flex items-center justify-center border-2 transition-fast ${
              isFun
                ? 'bg-[#E53935] border-[#212121] text-[#FDD835] shadow-[2px_2px_0px_#212121]'
                : 'bg-[#0D1117] border-[#30363D] text-[#58A6FF]'
            }`}>
              <Terminal className="w-4 h-4 stroke-[2.5]" />
            </div>
            <div className="flex items-center gap-2">
              <span className={`font-extrabold text-[16px] tracking-tight ${
                isFun ? 'text-[#212121] uppercase font-black' : 'text-[#E6EDF3]'
              }`}>
                CodeOracle
              </span>
              <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-[4px] border-2 font-black ${
                isFun
                  ? 'bg-[#E53935] text-[#FFFFFF] border-[#212121] shadow-[2px_2px_0px_#212121]'
                  : 'text-[#8B949E] bg-[#0D1117] border-[#30363D]'
              }`}>
                {isFun ? '🔥 FUN MODE' : 'ENTERPRISE'}
              </span>
            </div>
          </div>
        </div>

        {/* Action Controls & Uiverse Toggle Button */}
        <div className="flex items-center gap-3">
          {/* Uiverse.io Toggle Button by barisdogansutcu */}
          <button
            onClick={onToggleThemeMode}
            className="fun-toggle-btn"
            title="Click to toggle Fun Mode / Tech Mode"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 36 36"
              width="26px"
              height="26px"
            >
              <rect width="36" height="36" x="0" y="0" fill="#fdd835"></rect>
              <path
                fill="#e53935"
                d="M38.67,42H11.52C11.27,40.62,11,38.57,11,36c0-5,0-11,0-11s1.44-7.39,3.22-9.59 c1.67-2.06,2.76-3.48,6.78-4.41c3-0.7,7.13-0.23,9,1c2.15,1.42,3.37,6.67,3.81,11.29c1.49-0.3,5.21,0.2,5.5,1.28 C40.89,30.29,39.48,38.31,38.67,42z"
              ></path>
              <path
                fill="#b71c1c"
                d="M39.02,42H11.99c-0.22-2.67-0.48-7.05-0.49-12.72c0.83,4.18,1.63,9.59,6.98,9.79 c3.48,0.12,8.27,0.55,9.83-2.45c1.57-3,3.72-8.95,3.51-15.62c-0.19-5.84-1.75-8.2-2.13-8.7c0.59,0.66,3.74,4.49,4.01,11.7 c0.03,0.83,0.06,1.72,0.08,2.66c4.21-0.15,5.93,1.5,6.07,2.35C40.68,33.85,39.8,38.9,39.02,42z"
              ></path>
              <path
                fill="#212121"
                d="M35,27.17c0,3.67-0.28,11.2-0.42,14.83h-2C32.72,38.42,33,30.83,33,27.17 c0-5.54-1.46-12.65-3.55-14.02c-1.65-1.08-5.49-1.48-8.23-0.85c-3.62,0.83-4.57,1.99-6.14,3.92L15,16.32 c-1.31,1.6-2.59,6.92-3,8.96v10.8c0,2.58,0.28,4.61,0.54,5.92H10.5c-0.25-1.41-0.5-3.42-0.5-5.92l0.02-11.09 c0.15-0.77,1.55-7.63,3.43-9.94l0.08-0.09c1.65-2.03,2.96-3.63,7.25-4.61c3.28-0.76,7.67-0.25,9.77,1.13 C33.79,13.6,35,22.23,35,27.17z"
              ></path>
              <path
                fill="#01579b"
                d="M17.165,17.283c5.217-0.055,9.391,0.283,9,6.011c-0.391,5.728-8.478,5.533-9.391,5.337 c-0.913-0.196-7.826-0.043-7.696-5.337C9.209,18,13.645,17.32,17.165,17.283z"
              ></path>
              <path
                fill="#212121"
                d="M40.739,37.38c-0.28,1.99-0.69,3.53-1.22,4.62h-2.43c0.25-0.19,1.13-1.11,1.67-4.9 c0.57-4-0.23-11.79-0.93-12.78c-0.4-0.4-2.63-0.8-4.37-0.89l0.1-1.99c1.04,0.05,4.53,0.31,5.71,1.49 C40.689,24.36,41.289,33.53,40.739,37.38z"
              ></path>
              <path
                fill="#81d4fa"
                d="M10.154,20.201c0.261,2.059-0.196,3.351,2.543,3.546s8.076,1.022,9.402-0.554 c1.326-1.576,1.75-4.365-0.891-5.267C19.336,17.287,12.959,16.251,10.154,20.201z"
              ></path>
              <path
                fill="#212121"
                d="M17.615,29.677c-0.502,0-0.873-0.03-1.052-0.069c-0.086-0.019-0.236-0.035-0.434-0.06 c-5.344-0.679-8.053-2.784-8.052-6.255c0.001-2.698,1.17-7.238,8.986-7.32l0.181-0.002c3.444-0.038,6.414-0.068,8.272,1.818 c1.173,1.191,1.712,3,1.647,5.53c-0.044,1.688-0.785,3.147-2.144,4.217C22.785,29.296,19.388,29.677,17.615,29.677z M17.086,17.973 c-7.006,0.074-7.008,4.023-7.008,5.321c-0.001,3.109,3.598,3.926,6.305,4.27c0.273,0.035,0.48,0.063,0.601,0.089 c0.563,0.101,4.68,0.035,6.855-1.732c0.865-0.702,1.299-1.57,1.326-2.653c0.051-1.958-0.301-3.291-1.073-4.075 c-1.262-1.281-3.834-1.255-6.825-1.222L17.086,17.973z"
              ></path>
              <path
                fill="#e1f5fe"
                d="M15.078,19.043c1.957-0.326,5.122-0.529,4.435,1.304c-0.489,1.304-7.185,2.185-7.185,0.652 C12.328,19.467,15.078,19.043,15.078,19.043z"
              ></path>
            </svg>
            <span className="now">NOW!</span>
            <span className="play">{isFun ? 'FUN!' : 'TECH'}</span>
          </button>

          {/* New Analysis Reset */}
          <button
            onClick={onReset}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-bold rounded-[4px] border-2 transition-fast cursor-pointer ${
              isFun
                ? 'bg-[#E53935] text-white border-[#212121] shadow-[2px_2px_0px_#212121] hover:bg-[#b71c1c]'
                : 'bg-[#0D1117] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3] border-[#30363D]'
            }`}
            title="Start New Analysis"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Job</span>
          </button>

          {/* Demo Sandbox Mode Toggle */}
          <button
            onClick={onToggleMock}
            className={`flex items-center gap-2 px-2.5 py-1.5 text-xs font-bold rounded-[4px] border-2 transition-fast cursor-pointer ${
              isMock
                ? isFun
                  ? 'bg-[#212121] text-[#FDD835] border-[#212121] shadow-[2px_2px_0px_#E53935]'
                  : 'bg-[#1C2129] border-[#58A6FF] text-[#58A6FF]'
                : isFun
                  ? 'bg-[#FFFFFF] text-[#212121] border-[#212121]'
                  : 'bg-[#0D1117] border-[#30363D] text-[#8B949E] hover:text-[#E6EDF3]'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isMock ? (isFun ? '🔥 Sandbox Magic' : 'Demo Sandbox') : 'Live API'}</span>
          </button>

          {/* Server Config Popover Button */}
          <div className="relative">
            <button
              onClick={() => setShowConfig(!showConfig)}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-bold rounded-[4px] border-2 transition-fast cursor-pointer ${
                isFun
                  ? 'bg-[#FFFFFF] text-[#212121] border-[#212121] shadow-[2px_2px_0px_#212121]'
                  : 'bg-[#0D1117] hover:bg-[#1C2129] text-[#8B949E] hover:text-[#E6EDF3] border-[#30363D]'
              }`}
            >
              <Server className={`w-3.5 h-3.5 ${isFun ? 'text-[#E53935]' : 'text-[#58A6FF]'}`} />
              <span className="hidden sm:inline">Endpoint</span>
            </button>

            {showConfig && (
              <div className={`absolute right-0 mt-2 w-80 rounded-[6px] p-4 shadow-2xl z-50 border-2 ${
                isFun
                  ? 'bg-[#FFFFFF] border-[#212121] text-[#212121] shadow-[4px_4px_0px_#E53935]'
                  : 'bg-[#1C2129] border-[#30363D] text-[#E6EDF3]'
              }`}>
                <div className="flex items-center justify-between mb-3 pb-2 border-b-2 border-[#212121] dark:border-[#30363D]">
                  <h4 className="text-xs font-bold flex items-center gap-1.5">
                    <Server className="w-3.5 h-3.5 text-[#E53935]" /> Target API Endpoint
                  </h4>
                  <span className="text-[10px] font-mono text-slate-500 font-bold">LOCKED CONTRACT</span>
                </div>
                <input
                  type="text"
                  value={baseUrl}
                  onChange={(e) => onBaseUrlChange(e.target.value)}
                  placeholder="https://hackorbit-codeoracle-vision-x.onrender.com"
                  className={`w-full rounded-[4px] px-3 py-1.5 text-xs font-mono border-2 focus:outline-none ${
                    isFun
                      ? 'bg-[#FEF3C7] border-[#212121] text-[#212121] focus:border-[#E53935]'
                      : 'bg-[#0D1117] border-[#30363D] text-[#E6EDF3] focus:border-[#58A6FF]'
                  }`}
                />
                <div className="mt-3 pt-2 border-t-2 border-[#212121] dark:border-[#30363D] font-mono text-[11px] text-slate-600 space-y-1 font-bold">
                  <p><span className="text-[#E53935]">POST</span> /api/upload</p>
                  <p><span className="text-[#01579B]">GET</span> /api/jobs/:id/status</p>
                  <p><span className="text-[#212121]">GET</span> /api/jobs/:id/result</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
