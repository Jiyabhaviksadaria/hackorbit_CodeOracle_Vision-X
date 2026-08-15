import { MOCK_JOB_RESULT } from './mockData';

// API Client managing standard REST communication with the CodeOracle Vision-X backend.
// Enforces strict adherence to backend contract.

// Default API Base URL:
// In Local Dev (import.meta.env.DEV): http://localhost:8000
// In Production: https://hackorbit-codeoracle-vision-x.onrender.com (or VITE_API_URL if configured)
export const DEFAULT_API_BASE_URL = 
  (import.meta.env.VITE_API_URL || '').trim() || 
  (import.meta.env.DEV ? 'http://localhost:8000' : 'https://hackorbit-codeoracle-vision-x.onrender.com');

export class CodeOracleAPI {
  constructor(baseUrl = DEFAULT_API_BASE_URL) {
    const raw = (baseUrl || DEFAULT_API_BASE_URL).trim();
    this.baseUrl = raw.replace(/\/+$/, '');
    this.useMock = false;
  }

  setUseMock(value) {
    this.useMock = Boolean(value);
  }

  setBaseUrl(url) {
    const raw = (url || DEFAULT_API_BASE_URL).trim();
    this.baseUrl = raw.replace(/\/+$/, '');
  }

  /**
   * Upload code via ZIP file OR GitHub repo URL
   * Contract: POST /api/upload
   * Body: multipart ZIP OR { github_url }
   * Returns: { job_id }
   */
  async uploadCode({ zipFile, githubUrl }) {
    if (this.useMock) {
      // Simulate network delay for upload
      await new Promise((resolve) => setTimeout(resolve, 800));
      return { job_id: `job_${Date.now()}_mock` };
    }

    const endpoint = `${this.baseUrl}/api/upload`;
    let response;

    if (zipFile) {
      const formData = new FormData();
      formData.append('file', zipFile);

      response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });
    } else if (githubUrl) {
      response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ github_url: githubUrl }),
      });
    } else {
      throw new Error('Please provide either a ZIP file or GitHub repository URL.');
    }

    if (!response.ok) {
      let errMsg = `Upload failed with status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.error || errorJson.detail) {
          errMsg = errorJson.error || errorJson.detail;
        }
      } catch (e) {
        // Fallback to text
      }
      throw new Error(errMsg);
    }

    const data = await response.json();
    if (!data || !data.job_id) {
      throw new Error('Invalid response format: Missing job_id from server');
    }
    return data; // { job_id }
  }

  /**
   * Fetch current job status
   * Contract: GET /api/jobs/{id}/status
   * Returns: { status: "queued"|"parsing"|"explaining"|"testing"|"refactoring"|"done"|"error", progress: 0-100, error?: string }
   */
  async getJobStatus(jobId, mockStepIndex = 0, signal = null) {
    if (this.useMock) {
      // Mock progress simulation sequence
      const steps = [
        { status: 'queued', progress: 10 },
        { status: 'parsing', progress: 30 },
        { status: 'explaining', progress: 55 },
        { status: 'testing', progress: 75 },
        { status: 'refactoring', progress: 90 },
        { status: 'done', progress: 100 },
      ];

      const current = steps[Math.min(mockStepIndex, steps.length - 1)];
      return current;
    }

    const endpoint = `${this.baseUrl}/api/jobs/${encodeURIComponent(jobId)}/status`;
    let response;
    try {
      response = await fetch(endpoint, {
        headers: { 'Accept': 'application/json' },
        signal: signal || undefined
      });
    } catch (networkErr) {
      if (networkErr.name === 'AbortError' || (signal && signal.aborted)) {
        const abortErr = new Error('Request aborted');
        abortErr.isAborted = true;
        throw abortErr;
      }
      const err = new Error('Unable to connect to the CodeOracle backend.');
      err.isNetworkError = true;
      throw err;
    }

    if (!response.ok) {
      let detailMsg = null;
      try {
        const errorJson = await response.json();
        detailMsg = errorJson.detail || errorJson.error;
      } catch (e) {}

      const msg = detailMsg || (response.status === 404
        ? 'Your previous analysis session has expired or is no longer available on the server. Please start a new analysis.'
        : `Failed to fetch status (HTTP ${response.status})`);

      const err = new Error(msg);
      err.status = response.status;
      if (response.status === 404) {
        err.isExpired = true;
      }
      throw err;
    }

    const data = await response.json();
    return data;
  }

  /**
   * Fetch final job analysis results
   * Contract: GET /api/jobs/{id}/result
   * Returns: { explanation, dependency_graph, tests, refactor }
   */
  async getJobResult(jobId, signal = null) {
    if (this.useMock) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      return MOCK_JOB_RESULT;
    }

    const endpoint = `${this.baseUrl}/api/jobs/${encodeURIComponent(jobId)}/result`;
    let response;
    try {
      response = await fetch(endpoint, {
        headers: { 'Accept': 'application/json' },
        signal: signal || undefined
      });
    } catch (networkErr) {
      if (networkErr.name === 'AbortError' || (signal && signal.aborted)) {
        const abortErr = new Error('Request aborted');
        abortErr.isAborted = true;
        throw abortErr;
      }
      const err = new Error('Unable to connect to the CodeOracle backend.');
      err.isNetworkError = true;
      throw err;
    }

    if (!response.ok) {
      let detailMsg = null;
      try {
        const errorJson = await response.json();
        detailMsg = errorJson.detail || errorJson.error;
      } catch (e) {}

      const msg = detailMsg || (response.status === 404
        ? 'Your previous analysis session has expired or is no longer available on the server. Please start a new analysis.'
        : `Failed to fetch job results (HTTP ${response.status})`);

      const err = new Error(msg);
      err.status = response.status;
      if (response.status === 404) {
        err.isExpired = true;
      }
      throw err;
    }

    const data = await response.json();
    return data;
  }
}

export const apiService = new CodeOracleAPI(DEFAULT_API_BASE_URL);
