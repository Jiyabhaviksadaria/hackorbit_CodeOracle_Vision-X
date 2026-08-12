import React, { useState, useId } from 'react';
import { Upload, ArrowRight, FileCheck, AlertCircle } from 'lucide-react';
import { TruckLoader } from './TruckLoader';

function GithubIcon({ className = "w-4 h-4" }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
    </svg>
  );
}

const GITHUB_URL_REGEX = /^https?:\/\/(www\.)?github\.com\/[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+\/?$/;

export function UploadSection({ onUploadSubmit, isSubmitting, isMock, themeMode }) {
  const [activeSegment, setActiveSegment] = useState('zip');
  const [selectedFile, setSelectedFile] = useState(null);
  const [githubUrl, setGithubUrl] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [zipError, setZipError] = useState('');
  const [urlError, setUrlError] = useState('');
  const [hasInteractedUrl, setHasInteractedUrl] = useState(false);
  const fileInputId = useId();

  const isFun = themeMode === 'fun';

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    setZipError('');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileSelect = (e) => {
    setZipError('');
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const validateAndSetFile = (file) => {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      setSelectedFile(null);
      setZipError('Invalid file format: Only .zip repository archives are supported.');
      return;
    }
    if (file.size === 0) {
      setSelectedFile(null);
      setZipError('Corrupt archive: Selected file is 0 bytes.');
      return;
    }
    setSelectedFile(file);
    setZipError('');
  };

  const handleUrlChange = (val) => {
    setGithubUrl(val);
    setHasInteractedUrl(true);
    if (!val.trim()) {
      setUrlError('');
      return;
    }
    if (!GITHUB_URL_REGEX.test(val.trim())) {
      setUrlError('Invalid GitHub repository URL pattern (e.g. https://github.com/owner/repository).');
    } else {
      setUrlError('');
    }
  };

  const isValid = activeSegment === 'zip'
    ? Boolean(selectedFile || isMock)
    : Boolean(githubUrl.trim() && !urlError);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!isValid || isSubmitting) return;

    if (activeSegment === 'zip') {
      onUploadSubmit({ zipFile: selectedFile, githubUrl: null });
    } else {
      onUploadSubmit({ zipFile: null, githubUrl: githubUrl.trim() });
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex flex-col justify-center items-center px-4 py-12">
      <div className="w-full max-w-2xl mx-auto space-y-8">
        {/* Header Typography Section */}
        <div className="text-center space-y-3">
          <span className={`text-[11px] font-mono uppercase tracking-[0.1em] block ${
            isFun ? 'text-[#E53935] font-black flex items-center justify-center gap-1' : 'text-[#8B949E]'
          }`}>
            {isFun ? '🔥 LEGACY CODE STUDIO 🔥' : 'LEGACY CODE, EXPLAINED'}
          </span>
          <h1 className={`text-[28px] font-bold tracking-tight leading-snug ${
            isFun ? 'text-[#212121] font-black' : 'text-[#E6EDF3]'
          }`}>
            {isFun ? 'Understand & Modernize Code With Superpowers 🚀' : 'Understand and modernize your legacy codebase'}
          </h1>
          <p className={`text-sm max-w-lg mx-auto leading-normal ${
            isFun ? 'text-[#374151] font-semibold' : 'text-[#8B949E]'
          }`}>
            Explains module architecture, maps dependency graphs, generates test suites, and proposes modernized code implementations.
          </p>
        </div>

        {/* Upload Container Card */}
        <div className={`rounded-[6px] p-6 space-y-6 relative overflow-hidden transition-all ${
          isFun
            ? 'bg-[#FFFFFF] border-3 border-[#212121] shadow-[6px_6px_0px_#E53935]'
            : 'bg-[#161B22] border border-[#30363D]'
        }`}>
          {isSubmitting ? (
            <div className="py-8 animate-fade-in">
              <TruckLoader text={isFun ? "🚚 Code Delivery Truck in Action! 🔥" : "Your code is loading..."} />
            </div>
          ) : (
            <>
              {/* Segmented Control Switcher */}
              <div className={`flex p-1 rounded-[4px] border-2 ${
                isFun ? 'bg-[#FEF3C7] border-[#212121]' : 'bg-[#0D1117] border-[#30363D]'
              }`}>
                <button
                  type="button"
                  onClick={() => setActiveSegment('zip')}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-[4px] transition-fast cursor-pointer ${
                    activeSegment === 'zip'
                      ? isFun
                        ? 'bg-[#E53935] text-white border-2 border-[#212121] shadow-[2px_2px_0px_#212121]'
                        : 'bg-[#1C2129] text-[#E6EDF3] border border-[#30363D]'
                      : isFun
                        ? 'text-[#212121] hover:text-[#E53935]'
                        : 'text-[#8B949E] hover:text-[#E6EDF3]'
                  }`}
                >
                  📁 Upload ZIP
                </button>
                <button
                  type="button"
                  onClick={() => setActiveSegment('github')}
                  className={`flex-1 py-1.5 text-xs font-bold rounded-[4px] transition-fast cursor-pointer ${
                    activeSegment === 'github'
                      ? isFun
                        ? 'bg-[#E53935] text-white border-2 border-[#212121] shadow-[2px_2px_0px_#212121]'
                        : 'bg-[#1C2129] text-[#E6EDF3] border border-[#30363D]'
                      : isFun
                        ? 'text-[#212121] hover:text-[#E53935]'
                        : 'text-[#8B949E] hover:text-[#E6EDF3]'
                  }`}
                >
                  🐙 GitHub URL
                </button>
              </div>

              {/* Form Actions */}
              <form onSubmit={handleSubmit} className="space-y-4">
                {activeSegment === 'zip' ? (
                  <div className="space-y-2">
                    <div
                      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={handleFileDrop}
                      className={`relative border-2 border-dashed rounded-[6px] p-8 text-center transition-fast cursor-pointer ${
                        dragOver
                          ? isFun ? 'border-[#E53935] bg-[#FEF3C7]' : 'border-[#58A6FF] bg-[#1C2129]'
                          : selectedFile
                          ? isFun ? 'border-[#10B981] bg-emerald-50' : 'border-[#3FB950] bg-[#161B22]'
                          : isFun ? 'border-[#212121] bg-[#FEF3C7]' : 'border-[#30363D] hover:border-[#8B949E] bg-[#0D1117]'
                      }`}
                    >
                      <label htmlFor={fileInputId} className="cursor-pointer block w-full h-full">
                        <input
                          id={fileInputId}
                          type="file"
                          accept=".zip"
                          onChange={handleFileSelect}
                          className="hidden"
                        />

                        {selectedFile ? (
                          <div className="flex flex-col items-center gap-2">
                            <div className={`w-8 h-8 rounded-[4px] flex items-center justify-center ${
                              isFun ? 'bg-[#10B981] text-white border-2 border-[#212121]' : 'bg-[#3FB950]/10 border border-[#3FB950]/30 text-[#3FB950]'
                            }`}>
                              <FileCheck className="w-4 h-4" />
                            </div>
                            <span className={`text-xs font-mono font-bold ${isFun ? 'text-[#212121]' : 'text-[#E6EDF3]'}`}>
                              {selectedFile.name}
                            </span>
                            <span className={`text-[11px] font-mono ${isFun ? 'text-[#374151]' : 'text-[#8B949E]'}`}>
                              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                            </span>
                          </div>
                        ) : (
                          <div className="flex flex-col items-center gap-2">
                            <Upload className={`w-6 h-6 ${isFun ? 'text-[#E53935]' : 'text-[#8B949E]'}`} />
                            <div>
                              <p className={`text-xs font-bold ${isFun ? 'text-[#212121]' : 'text-[#E6EDF3]'}`}>
                                Drop repository archive here or <span className={isFun ? 'text-[#E53935] font-extrabold' : 'text-[#58A6FF]'}>browse</span>
                              </p>
                              <p className={`text-[11px] font-mono mt-1 ${isFun ? 'text-[#E53935] font-black' : 'text-[#8B949E]'}`}>
                                {isFun ? '🔥 ZIP up to 10,000 lines of code' : 'ZIP up to 10,000 lines of code'}
                              </p>
                            </div>
                          </div>
                        )}
                      </label>
                    </div>

                    {zipError && (
                      <div className="flex items-center gap-1.5 text-xs font-mono text-[#E53935]">
                        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                        <span>{zipError}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="relative">
                      <div className={`absolute left-3 top-2.5 ${isFun ? 'text-[#E53935]' : 'text-[#8B949E]'}`}>
                        <GithubIcon className="w-4 h-4" />
                      </div>
                      <input
                        type="url"
                        value={githubUrl}
                        onChange={(e) => handleUrlChange(e.target.value)}
                        placeholder="https://github.com/username/repository"
                        className={`w-full rounded-[4px] pl-9 pr-3 py-2 text-xs font-mono border-2 focus:outline-none ${
                          isFun
                            ? 'bg-[#FEF3C7] border-[#212121] text-[#212121] focus:border-[#E53935]'
                            : 'bg-[#0D1117] border-[#30363D] text-[#E6EDF3] focus:border-[#58A6FF]'
                        }`}
                      />
                    </div>

                    {urlError && hasInteractedUrl && (
                      <div className="flex items-center gap-1.5 text-xs font-mono text-[#E53935]">
                        <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                        <span>{urlError}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Primary Action Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={!isValid || isSubmitting}
                    className={`w-full flex items-center justify-center gap-2 py-2.5 font-black text-xs rounded-[4px] transition-all cursor-pointer disabled:opacity-50 ${
                      isFun
                        ? 'bg-[#E53935] hover:bg-[#FDD835] hover:text-[#212121] text-white border-2 border-[#212121] shadow-[3px_3px_0px_#212121]'
                        : 'bg-[#58A6FF] hover:bg-[#79B8FF] disabled:bg-[#30363D] text-[#0D1117] disabled:text-[#545D68]'
                    }`}
                  >
                    <span>{isFun ? '🔥 Run Code Oracle' : 'Analyze codebase'}</span>
                    <ArrowRight className="w-4 h-4 stroke-[3]" />
                  </button>
                </div>
              </form>

              <p className={`text-center text-[11px] font-mono ${isFun ? 'text-[#E53935] font-extrabold' : 'text-[#8B949E]'}`}>
                {isFun ? '⚡ Python required · Java, JavaScript, or C++ optional · instant magic' : 'Python required · Java, JavaScript, or C++ optional · results in minutes'}
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
