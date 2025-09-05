// api/index.js - API Service
const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

// Helper function to handle CORS issues
const fetchWithCORS = async (url, options = {}) => {
  // Add CORS headers to request
  const headers = {
    ...options.headers,
    'Accept': 'application/json',
  };
  
  // Only set Content-Type if not using FormData (browser will set it with boundary)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }
  
  try {
    // Log request details
    console.log(`Making fetch request to: ${url}`);
    console.log('Request options:', {
      ...options,
      headers,
      mode: 'cors',
      credentials: 'omit'
    });
    
    const response = await fetch(url, {
      ...options,
      headers,
      mode: 'cors',
      credentials: 'omit', // Use 'omit' instead of 'include' to avoid cookies
    });
    
    // Log response details
    console.log(`Response status: ${response.status} ${response.statusText}`);
    
    if (!response.ok) {
      console.warn(`HTTP error ${response.status}: ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    console.error('CORS Error:', error);
    throw error;
  }
};

export const api = {
  // Test endpoints
  corsTest: async () => {
    console.log('Testing CORS with endpoint:', `${API_URL}/cors-test`);
    
    // Try with multiple endpoints to diagnose the issue
    const corsEndpoints = [
      `${API_URL}/cors-test`,  // Primary API endpoint
      'http://localhost:8002/cors-test', // CORS test server
    ];
    
    let successResponse = null;
    let allErrors = [];
    
    // Try each endpoint
    for (const endpoint of corsEndpoints) {
      try {
        console.log(`Trying CORS test with endpoint: ${endpoint}`);
        
        // Try with our wrapper
        const response = await fetchWithCORS(endpoint);
        const data = await response.json();
        console.log(`CORS test successful with ${endpoint}:`, data);
        
        // If we get here, we found a working endpoint
        successResponse = data;
        break;
      } catch (error) {
        console.error(`CORS test failed with ${endpoint}:`, error);
        allErrors.push({ endpoint, error: error.toString() });
        
        // Try direct fetch as fallback for this endpoint
        try {
          console.log(`Trying direct fetch with ${endpoint}`);
          const directResponse = await fetch(endpoint, {
            method: 'GET',
            headers: { 'Accept': 'application/json' },
            mode: 'cors',
            credentials: 'omit',
          });
          const directData = await directResponse.json();
          console.log(`CORS test successful with direct fetch to ${endpoint}:`, directData);
          
          // If we get here, we found a working endpoint
          successResponse = directData;
          break;
        } catch (directError) {
          console.error(`Direct fetch also failed with ${endpoint}:`, directError);
          allErrors.push({ endpoint, error: `Direct: ${directError.toString()}` });
        }
      }
    }
    
    if (successResponse) {
      return successResponse;
    } else {
      console.error('All CORS endpoints failed:', allErrors);
      throw new Error(`CORS test failed on all endpoints: ${JSON.stringify(allErrors)}`);
    }
  },
  
  // System endpoints
  systemCheck: async () => {
    const response = await fetchWithCORS(`${API_URL}/system/check`);
    return response.json();
  },
  
  getSystemConfig: async () => {
    const response = await fetchWithCORS(`${API_URL}/system/config`);
    return response.json();
  },
  
  updateSystemConfig: async (config) => {
    const response = await fetchWithCORS(`${API_URL}/system/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });
    return response.json();
  },
  
  // Server logs
  get: async (url, params = {}) => {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        queryParams.append(key, value);
      }
    });
    
    const queryString = queryParams.toString();
    const fullUrl = queryString ? `${API_URL}${url}?${queryString}` : `${API_URL}${url}`;
    
    const response = await fetchWithCORS(fullUrl);
    return response.json();
  },
  
  getLogs: async (params = {}) => {
    // Directly use the generic get method to fetch logs
    try {
      return await api.get('/system/logs', params);
    } catch (error) {
      console.error('Error in getLogs:', error);
      // Return an empty logs array as fallback
      return { logs: [], total: 0 };
    }
  },
  
  // Project endpoints
  createProject: async (projectData) => {
    const response = await fetchWithCORS(`${API_URL}/projects`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(projectData),
    });
    return response.json();
  },
  
  listProjects: async () => {
    const response = await fetchWithCORS(`${API_URL}/projects`);
    return response.json();
  },
  
  getProject: async (projectId) => {
    const response = await fetchWithCORS(`${API_URL}/projects/${projectId}`);
    return response.json();
  },
  
  // Job endpoints
  createIngestJob: async (projectId, file) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file', file);
    
    // Use the extensions/process-file endpoint which has proper multipart form handling
    const response = await fetchWithCORS(`${API_URL}/extensions/process-file`, {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type with boundary for FormData
    });
    return response.json();
  },
  
  createIngestUrlJob: async (projectId, url, config = null) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('url', url);
    if (config) {
      formData.append('config', JSON.stringify(config));
    }
    
    const response = await fetchWithCORS(`${API_URL}/jobs/ingest/url`, {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type with boundary for FormData
    });
    return response.json();
  },
  
  createQAJob: async (projectId, inputFile, qaType = 'qa', numPairs = null, config = null) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('background', 'true');
    
    // Ensure the input_file path is properly formatted
    let normalizedPath = inputFile;
    
    // Handle various path prefixes consistently
    if (normalizedPath.startsWith('backend/')) {
      normalizedPath = normalizedPath.substring('backend/'.length);
      console.log(`Removed 'backend/' prefix, now using: ${normalizedPath}`);
    }
    
    // Handle absolute paths by converting to relative paths
    const projectRoot = '/home/dom/synthetic-data-studio/';
    if (normalizedPath.startsWith(projectRoot)) {
      normalizedPath = normalizedPath.substring(projectRoot.length);
      console.log(`Converted absolute path to relative: ${normalizedPath}`);
      
      // Further remove backend/ if present after converting from absolute
      if (normalizedPath.startsWith('backend/')) {
        normalizedPath = normalizedPath.substring('backend/'.length);
        console.log(`Removed 'backend/' prefix from converted path, now using: ${normalizedPath}`);
      }
    }
    
    formData.append('input_file', normalizedPath);
    formData.append('qa_type', qaType);
    
    // Convert null to proper types for FastAPI
    if (numPairs !== null) {
      formData.append('num_pairs', numPairs.toString());
    }
    
    console.log(`Creating QA job with project_id=${projectId}, input_file=${normalizedPath}, qa_type=${qaType}, num_pairs=${numPairs}`);
    
    // Try all possible endpoints in sequence until one works
    const endpoints = [
      '/synthdata/no-deps/create-qa',  // Endpoint with no dependencies
      '/jobs/create',              // Primary API endpoint from backend/api/jobs.py 
      '/api/jobs/create',          // Possible mount path
      '/synthdata/create-qa'       // Original endpoint from synthdata.py
    ];
    
    let lastError = null;
    
    for (const endpoint of endpoints) {
      try {
        console.log(`Trying endpoint: ${endpoint}`);
        
        // Make the request without query parameters
        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          body: formData,
          mode: 'cors',
          credentials: 'omit',
          headers: {
            'Accept': 'application/json'
          }
        });
        
        // If successful, return the result
        if (response.ok) {
          console.log(`Success with endpoint: ${endpoint}`);
          return response.json();
        }
        
        // If not successful, try to get error details
        const errorText = await response.text();
        console.error(`API Error with ${endpoint} (${response.status}): ${errorText}`);
        lastError = new Error(`API Error with ${endpoint}: ${response.status} ${response.statusText}`);
      } catch (err) {
        console.error(`Error with endpoint ${endpoint}:`, err);
        lastError = err;
      }
    }
    
    // If all endpoints failed, throw the last error
    throw lastError || new Error('All API endpoints failed');
  },
  
  createCurateJob: async (projectId, inputFile, threshold = null, config = null) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    
    // Ensure the input_file path is properly formatted
    let normalizedPath = inputFile;
    // If the path includes data/ but not backend/data/, add the backend/ prefix
    if (inputFile.startsWith('data/') && !inputFile.startsWith('backend/data/')) {
      normalizedPath = `backend/${inputFile}`;
      console.log(`Adjusted input file path: ${inputFile} → ${normalizedPath}`);
    }
    
    // Add the normalized input_file to form data
    formData.append('input_file', normalizedPath);
    
    if (threshold) {
      formData.append('threshold', threshold);
    }
    if (config) {
      formData.append('config', JSON.stringify(config));
    }
    
    // Try all possible endpoints in sequence until one works
    const endpoints = [
      '/synthdata/no-deps/curate-qa',  // Endpoint with no dependencies
      '/jobs/curate',                  // Primary API endpoint from backend/api/jobs.py 
      '/api/jobs/curate',              // Possible mount path
      '/synthdata/curate-qa'           // Original endpoint from synthdata.py
    ];
    
    let lastError = null;
    
    for (const endpoint of endpoints) {
      try {
        console.log(`Trying endpoint: ${endpoint}`);
        
        // Make the request without query parameters
        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          body: formData,
          mode: 'cors',
          credentials: 'omit',
          headers: {
            'Accept': 'application/json'
          }
        });
        
        // If successful, return the result
        if (response.ok) {
          console.log(`Success with endpoint: ${endpoint}`);
          return response.json();
        }
        
        // If not successful, try to get error details
        const errorText = await response.text();
        console.error(`API Error with ${endpoint} (${response.status}): ${errorText}`);
        lastError = new Error(`API Error with ${endpoint}: ${response.status} ${response.statusText}`);
      } catch (err) {
        console.error(`Error with endpoint ${endpoint}:`, err);
        lastError = err;
      }
    }
    
    // If all endpoints failed, throw the last error
    throw lastError || new Error('All API endpoints failed');
  },
  
  createSaveJob: async (projectId, inputFile, format = 'jsonl', storage = null, config = null) => {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('input_file', inputFile);
    formData.append('format', format);
    if (storage) {
      formData.append('storage', storage);
    }
    if (config) {
      formData.append('config', JSON.stringify(config));
    }
    
    // Try all possible endpoints in sequence until one works
    const endpoints = [
      '/synthdata/no-deps/convert-format',  // Endpoint with no dependencies
      '/jobs/save-as',                 // Primary API endpoint from backend/api/jobs.py 
      '/api/jobs/save-as',             // Possible mount path
      '/synthdata/convert-format'      // Original endpoint from synthdata.py
    ];
    
    let lastError = null;
    
    for (const endpoint of endpoints) {
      try {
        console.log(`Trying endpoint: ${endpoint}`);
        
        // Make the request without query parameters
        const response = await fetch(`${API_URL}${endpoint}`, {
          method: 'POST',
          body: formData,
          mode: 'cors',
          credentials: 'omit',
          headers: {
            'Accept': 'application/json'
          }
        });
        
        // If successful, return the result
        if (response.ok) {
          console.log(`Success with endpoint: ${endpoint}`);
          return response.json();
        }
        
        // If not successful, try to get error details
        const errorText = await response.text();
        console.error(`API Error with ${endpoint} (${response.status}): ${errorText}`);
        lastError = new Error(`API Error with ${endpoint}: ${response.status} ${response.statusText}`);
      } catch (err) {
        console.error(`Error with endpoint ${endpoint}:`, err);
        lastError = err;
      }
    }
    
    // If all endpoints failed, throw the last error
    throw lastError || new Error('All API endpoints failed');
  },
  
  listJobs: async (filters = {}) => {
    const queryParams = new URLSearchParams();
    if (filters.projectId) queryParams.append('project_id', filters.projectId);
    if (filters.status) queryParams.append('status_param', filters.status);
    if (filters.jobType) queryParams.append('job_type', filters.jobType);
    if (filters.skip) queryParams.append('skip', filters.skip);
    if (filters.limit) queryParams.append('limit', filters.limit);
    
    console.log(`Fetching jobs with URL: ${API_URL}/jobs?${queryParams.toString()}`);
    
    try {
      // Try with our custom CORS wrapper first
      const response = await fetchWithCORS(`${API_URL}/jobs?${queryParams.toString()}`);
      const data = await response.json();
      console.log('Jobs fetched successfully:', data);
      return data;
    } catch (error) {
      console.error('Failed to fetch jobs with wrapper:', error);
      
      // Fallback to direct fetch with simpler settings
      console.log('Trying direct fetch for jobs...');
      try {
        const directResponse = await fetch(`${API_URL}/jobs?${queryParams.toString()}`, {
          method: 'GET',
          headers: { 'Accept': 'application/json' },
          mode: 'cors',
          credentials: 'omit',
        });
        
        if (!directResponse.ok) {
          throw new Error(`HTTP error ${directResponse.status}: ${directResponse.statusText}`);
        }
        
        const directData = await directResponse.json();
        console.log('Jobs fetched successfully with direct fetch:', directData);
        return directData;
      } catch (directError) {
        console.error('Direct fetch also failed:', directError);
        throw directError;
      }
    }
  },
  
  getJob: async (jobId) => {
    const response = await fetchWithCORS(`${API_URL}/jobs/${jobId}`);
    return response.json();
  },
  
  downloadJobResult: async (jobId) => {
    // Try all possible endpoints in sequence until one works
    const endpoints = [
      `/direct/${jobId}/download`,    // Direct endpoint (no dependencies)
      `/jobs/${jobId}/download`,      // Primary API endpoint from backend/api/jobs.py
      `/api/jobs/${jobId}/download`,  // Possible mount path
    ];
    
    let lastError = null;
    
    for (const endpoint of endpoints) {
      try {
        console.log(`Trying download endpoint: ${endpoint}`);
        
        // Use our CORS-friendly fetch wrapper
        const response = await fetchWithCORS(`${API_URL}${endpoint}`);
        
        // If successful, return the result
        if (response.ok) {
          console.log(`Success with endpoint: ${endpoint}`);
          return response.json();
        }
        
        // If not successful, try to get error details
        const errorText = await response.text();
        console.error(`API Error with ${endpoint} (${response.status}): ${errorText}`);
        lastError = new Error(`API Error with ${endpoint}: ${response.status} ${response.statusText}`);
      } catch (err) {
        console.error(`Error with endpoint ${endpoint}:`, err);
        lastError = err;
      }
    }
    
    // If all endpoints failed, throw the last error
    throw lastError || new Error('All download endpoints failed');
  },
  
  listProcessedFiles: async (fileType) => {
    const validTypes = ["output", "generated", "cleaned", "final"];
    if (!validTypes.includes(fileType)) {
      throw new Error(`Invalid file type. Must be one of: ${validTypes.join(', ')}`);
    }
    
    const response = await fetchWithCORS(`${API_URL}/synthdata/list-files/${fileType}`);
    return response.json();
  },
};