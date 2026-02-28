const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const jsonHeaders = {
  Accept: "application/json",
};

const normalizeInputPath = (inputFile) => {
  if (typeof inputFile !== "string") {
    return inputFile;
  }

  let normalized = inputFile.trim();
  if (normalized.startsWith("backend/")) {
    normalized = normalized.slice("backend/".length);
  }

  if (normalized.startsWith("/")) {
    const dataSegment = normalized.indexOf("/data/");
    if (dataSegment !== -1) {
      normalized = normalized.slice(dataSegment + 1);
    }
  }

  return normalized;
};

const readResponseBody = async (response) => {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  const text = await response.text();
  return text ? { detail: text } : {};
};

const request = async (path, options = {}) => {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    mode: "cors",
    credentials: "omit",
  });

  const body = await readResponseBody(response);
  if (!response.ok) {
    const detail =
      (body && (body.detail || body.message || body.error)) ||
      `HTTP ${response.status}`;
    throw new Error(detail);
  }
  return body;
};

export const api = {
  corsTest: async () => request("/system/cors-test"),

  systemCheck: async () => request("/system/check"),

  getSystemConfig: async () => request("/system/config"),

  updateSystemConfig: async (config) =>
    request("/system/config", {
      method: "PUT",
      headers: {
        ...jsonHeaders,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(config),
    }),

  get: async (url, params = {}) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        searchParams.append(key, value);
      }
    });

    const suffix = searchParams.toString();
    const path = suffix ? `${url}?${suffix}` : url;
    return request(path);
  },

  getLogs: async (params = {}) => {
    try {
      return await api.get("/system/logs", params);
    } catch (_error) {
      return { logs: [], total: 0 };
    }
  },

  createProject: async (projectData) =>
    request("/projects", {
      method: "POST",
      headers: {
        ...jsonHeaders,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(projectData),
    }),

  listProjects: async () => request("/projects"),

  getProject: async (projectId) => request(`/projects/${projectId}`),

  createIngestJob: async (projectId, file) => {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("file", file);
    return request("/jobs/ingest", {
      method: "POST",
      headers: jsonHeaders,
      body: formData,
    });
  },

  createIngestUrlJob: async (projectId, url) => {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("url", url);
    return request("/jobs/ingest/url", {
      method: "POST",
      headers: jsonHeaders,
      body: formData,
    });
  },

  createQAJob: async (projectId, inputFile, qaType = "qa", numPairs = null) => {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("input_file", normalizeInputPath(inputFile));
    formData.append("qa_type", qaType);
    if (numPairs !== null) {
      formData.append("num_pairs", String(numPairs));
    }
    return request("/jobs/create", {
      method: "POST",
      headers: jsonHeaders,
      body: formData,
    });
  },

  createCurateJob: async (projectId, inputFile, threshold = null) => {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("input_file", normalizeInputPath(inputFile));
    if (threshold !== null) {
      formData.append("threshold", String(threshold));
    }
    return request("/jobs/curate", {
      method: "POST",
      headers: jsonHeaders,
      body: formData,
    });
  },

  createSaveJob: async (
    projectId,
    inputFile,
    format = "jsonl",
    storage = null
  ) => {
    const formData = new FormData();
    formData.append("project_id", projectId);
    formData.append("input_file", normalizeInputPath(inputFile));
    formData.append("format", format);
    if (storage) {
      formData.append("storage", storage);
    }
    return request("/jobs/save-as", {
      method: "POST",
      headers: jsonHeaders,
      body: formData,
    });
  },

  listJobs: async (filters = {}) => {
    const queryParams = new URLSearchParams();
    if (filters.projectId) {
      queryParams.append("project_id", filters.projectId);
    }
    if (filters.status) {
      queryParams.append("status", filters.status);
    }
    if (filters.jobType) {
      queryParams.append("job_type", filters.jobType);
    }
    if (filters.skip !== undefined) {
      queryParams.append("skip", String(filters.skip));
    }
    if (filters.limit !== undefined) {
      queryParams.append("limit", String(filters.limit));
    }
    const suffix = queryParams.toString();
    const path = suffix ? `/jobs?${suffix}` : "/jobs";
    return request(path);
  },

  getJob: async (jobId) => request(`/jobs/${jobId}`),

  downloadJobResult: async (jobId) => request(`/jobs/${jobId}/download`),

  listProcessedFiles: async (fileType) => {
    const validTypes = ["output", "generated", "cleaned", "final"];
    if (!validTypes.includes(fileType)) {
      throw new Error(`Invalid file type. Must be one of: ${validTypes.join(", ")}`);
    }
    return request(`/extensions/list-files/${fileType}`);
  },
};
