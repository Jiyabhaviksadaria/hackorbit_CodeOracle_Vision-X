import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { LandingHero } from './components/LandingHero';
import { UploadSection } from './components/UploadSection';
import { ResultsShell } from './components/ResultsShell';
import { apiService, DEFAULT_API_BASE_URL } from './services/api';
import './App.css';

export default function App() {
  const [showLanding, setShowLanding] = useState(true);
  const [isMock, setIsMock] = useState(false);
  const [themeMode, setThemeMode] = useState('tech'); // 'tech' (dark) | 'fun' (red/yellow/black bold)
  const [baseUrl, setBaseUrl] = useState(DEFAULT_API_BASE_URL);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [jobError, setJobError] = useState(null);
  const [resultData, setResultData] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const mockStepRef = useRef(0);
  const pollTimerRef = useRef(null);
  const activeJobIdRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Sync class on document body for theme CSS variables
  useEffect(() => {
    if (themeMode === 'fun') {
      document.body.classList.add('fun-mode');
    } else {
      document.body.classList.remove('fun-mode');
    }
  }, [themeMode]);

  useEffect(() => {
    apiService.setUseMock(isMock);
  }, [isMock]);

  useEffect(() => {
    apiService.setBaseUrl(baseUrl);
  }, [baseUrl]);

  // Clean up polling timer and in-flight request on component unmount
  useEffect(() => {
    return () => {
      activeJobIdRef.current = null;
      stopPolling();
    };
  }, []);

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearTimeout(pollTimerRef.current);
      pollTimerRef.current = null;
    }
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  };

  const handleReset = () => {
    activeJobIdRef.current = null;
    stopPolling();
    setJobId(null);
    setStatus(null);
    setProgress(0);
    setJobError(null);
    setResultData(null);
    setIsSubmitting(false);
    mockStepRef.current = 0;
  };

  const toggleThemeMode = () => {
    setThemeMode((prev) => (prev === 'tech' ? 'fun' : 'tech'));
  };

  const handleUploadSubmit = async ({ zipFile, githubUrl }) => {
    // Explicitly reset any previous job state & timers before starting a new analysis
    handleReset();

    setIsSubmitting(true);

    try {
      const uploadRes = await apiService.uploadCode({ zipFile, githubUrl });
      const newJobId = uploadRes.job_id;
      setJobId(newJobId);
      setStatus('queued');
      setProgress(5);

      startStatusPolling(newJobId);
    } catch (err) {
      setJobError(err.message || 'Failed to initialize analysis job.');
      setStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const startStatusPolling = (targetJobId) => {
    stopPolling();
    activeJobIdRef.current = targetJobId;

    const pollStep = async () => {
      // Guard 1: Verify targetJobId matches currently active job
      if (!targetJobId || activeJobIdRef.current !== targetJobId) {
        return;
      }

      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      try {
        const statusRes = await apiService.getJobStatus(targetJobId, mockStepRef.current, signal);
        mockStepRef.current += 1;

        // Guard 2: Verify targetJobId is still active after async request completes
        if (activeJobIdRef.current !== targetJobId) {
          return;
        }

        if (statusRes.status) setStatus(statusRes.status);
        if (statusRes.progress !== undefined) setProgress(statusRes.progress);
        if (statusRes.error) setJobError(statusRes.error);

        if (statusRes.status === 'done') {
          activeJobIdRef.current = null;
          stopPolling();
          fetchJobResult(targetJobId);
        } else if (statusRes.status === 'error') {
          activeJobIdRef.current = null;
          stopPolling();
        } else {
          // Schedule next poll tick only if still active
          pollTimerRef.current = setTimeout(pollStep, 1500);
        }
      } catch (err) {
        if (err.isAborted || signal.aborted) {
          return;
        }

        // Terminal error state: clear active job ref and stop polling immediately
        activeJobIdRef.current = null;
        stopPolling();

        if (err.status === 404 || err.isExpired) {
          setStatus('expired');
          setJobError(err.message || 'Your previous analysis session has expired. Please start a new analysis.');
          setResultData(null);
          setProgress(0);
        } else if (err.isNetworkError) {
          setStatus('error');
          setJobError('Unable to connect to the CodeOracle backend.');
        } else {
          setStatus('error');
          setJobError(err.message || 'Error communicating with job status service.');
        }
      }
    };

    pollStep();
  };

  const fetchJobResult = async (completedJobId) => {
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      const res = await apiService.getJobResult(completedJobId, signal);
      setResultData(res);
    } catch (err) {
      if (err.isAborted || signal.aborted) return;
      if (err.status === 404 || err.isExpired) {
        activeJobIdRef.current = null;
        setStatus('expired');
        setJobError(err.message || 'Your previous analysis session has expired. Please start a new analysis.');
        setResultData(null);
        setProgress(0);
      } else {
        setJobError(err.message || 'Failed to fetch final analysis results.');
      }
    }
  };

  return (
    <div className={`min-h-screen font-sans flex flex-col transition-colors duration-200 ${
      themeMode === 'fun' ? 'bg-[#FFFBEB] text-[#111827]' : 'bg-[#0D1117] text-[#E6EDF3]'
    }`}>
      {/* Top Header with Uiverse Toggle Button */}
      <Header
        isMock={isMock}
        onToggleMock={() => {
          const next = !isMock;
          setIsMock(next);
          handleReset();
        }}
        baseUrl={baseUrl}
        onBaseUrlChange={setBaseUrl}
        onReset={handleReset}
        themeMode={themeMode}
        onToggleThemeMode={toggleThemeMode}
      />

      {/* Main Container */}
      <main className="flex-1">
        {showLanding ? (
          <LandingHero
            onEnter={() => setShowLanding(false)}
            themeMode={themeMode}
          />
        ) : !jobId ? (
          <UploadSection
            onUploadSubmit={handleUploadSubmit}
            isSubmitting={isSubmitting}
            isMock={isMock}
            themeMode={themeMode}
          />
        ) : (
          <ResultsShell
            jobId={jobId}
            status={status}
            progress={progress}
            error={jobError}
            resultData={resultData}
            onReset={handleReset}
            themeMode={themeMode}
          />
        )}
      </main>

      {/* Footer */}
      <footer className={`border-t py-4 text-center text-xs transition-colors ${
        themeMode === 'fun'
          ? 'bg-[#FDD835] border-[#212121] text-[#212121] font-bold'
          : 'bg-[#161B22] border-[#30363D] text-[#8B949E]'
      }`}>
        <div className="max-w-[1400px] mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2 font-mono">
          <span>{themeMode === 'fun' ? '🔥 CodeOracle Fun Mode • Red, Yellow & Black Edition' : 'CodeOracle Enterprise Tool • Locked Contract'}</span>
          <span>POST /api/upload • GET /api/jobs/:id/status • GET /api/jobs/:id/result</span>
        </div>
      </footer>
    </div>
  );
}
