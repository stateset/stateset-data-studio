import axios from 'axios';

export const createQAJob = async (
  projectId,
  inputFile,
  qaType = 'qa',
  numPairs = 25
) => {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('input_file', inputFile);
  formData.append('qa_type', qaType);
  formData.append('num_pairs', numPairs);

  const { data } = await axios.post('/jobs/create', formData);
  return data;
};

export const createCurateJob = async (
  projectId,
  inputFile,
  threshold = 7.0,
  batchSize = 8
) => {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('input_file', inputFile);
  formData.append('threshold', threshold);
  formData.append('batch_size', batchSize);

  const { data } = await axios.post('/jobs/curate', formData);
  return data;
};

export const createSaveJob = async (
  projectId,
  inputFile,
  format = 'jsonl',
  storage = 'local'
) => {
  const formData = new FormData();
  formData.append('project_id', projectId);
  formData.append('input_file', inputFile);
  formData.append('format', format);
  formData.append('storage', storage);

  const { data } = await axios.post('/jobs/save-as', formData);
  return data;
}; 