// pages/ProjectDetail.js
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api';
import { Card, Button, Table, Tag, Space, Tabs, Upload, Form, Input, Select, InputNumber, Alert, Modal, Spin, Typography } from 'antd';
import { UploadOutlined, LinkOutlined, FileTextOutlined, AppstoreOutlined, FilterOutlined, SaveOutlined, DownloadOutlined } from '@ant-design/icons';
import toast from 'react-hot-toast';

const { TabPane } = Tabs;
const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const ProjectDetail = () => {
  const { projectId } = useParams();
  const [project, setProject] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('1');
  const [fileList, setFileList] = useState([]);
  const [urlInput, setUrlInput] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [qaType, setQaType] = useState('qa');
  const [numPairs, setNumPairs] = useState(25);
  const [threshold, setThreshold] = useState(7.0);
  const [format, setFormat] = useState('alpaca');
  const [storage, setStorage] = useState('jsonl');
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [fileSelectModalVisible, setFileSelectModalVisible] = useState(false);
  const [availableFiles, setAvailableFiles] = useState([]);
  const [fileListLoading, setFileListLoading] = useState(false);
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const [projectData, jobsData] = await Promise.all([
        api.getProject(projectId),
        api.listJobs({ projectId }),
      ]);
      
      setProject(projectData);
      setJobs(jobsData);
    } catch (err) {
      setError('Failed to load project data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchData();
  }, [projectId]);
  
  const refreshJobs = async () => {
    try {
      const jobsData = await api.listJobs({ projectId });
      setJobs(jobsData);
    } catch (err) {
      console.error(err);
    }
  };
  
  const jobColumns = [
    {
      title: 'Type',
      dataIndex: 'job_type',
      key: 'job_type',
      render: (text) => {
        const colorMap = {
          ingest: 'blue',
          create: 'green',
          curate: 'orange',
          'save-as': 'purple',
        };
        return <Tag color={colorMap[text] || 'default'}>{text}</Tag>;
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (text) => {
        const colorMap = {
          pending: 'default',
          running: 'processing',
          completed: 'success',
          failed: 'error',
        };
        return <Tag color={colorMap[text] || 'default'}>{text}</Tag>;
      },
    },
    {
      title: 'Input File',
      dataIndex: 'input_file',
      key: 'input_file',
      ellipsis: true,
      render: (text) => text ? text.split('/').pop() : '',
    },
    {
      title: 'Output File',
      dataIndex: 'output_file',
      key: 'output_file',
      ellipsis: true,
      render: (text) => text ? text.split('/').pop() : '',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          {record.status === 'completed' && record.output_file && (
            <Button 
              type="text"
              icon={<DownloadOutlined />}
              size="small"
              onClick={() => handlePreview(record.id)}
            >
              Download
            </Button>
          )}
          {record.status === 'completed' && record.output_file && record.job_type === 'ingest' && (
            <Button
              type="primary"
              size="small"
              ghost
              onClick={() => handleSelectOutputFile(record.output_file)}
            >
              Use for QA
            </Button>
          )}
          {record.status === 'completed' && record.output_file && record.job_type === 'create' && (
            <Button
              type="primary"
              size="small"
              ghost
              onClick={() => handleSelectOutputFile(record.output_file)}
            >
              Use for Curation
            </Button>
          )}
          {record.status === 'completed' && record.output_file && record.job_type === 'curate' && (
            <Button
              type="primary"
              size="small"
              ghost
              onClick={() => handleSelectOutputFile(record.output_file)}
            >
              Use for Export
            </Button>
          )}
        </Space>
      ),
    },
  ];
  
  const handleUploadChange = ({ fileList }) => {
    setFileList(fileList);
  };
  
  const handleUrlChange = (e) => {
    setUrlInput(e.target.value);
  };
  
  const handleIngestFile = async () => {
    if (fileList.length === 0) {
      toast.error('Please select a file to ingest');
      return;
    }
    
    try {
      const file = fileList[0].originFileObj;
      await api.createIngestJob(projectId, file);
      toast.success('Ingest job created successfully');
      setFileList([]);
      refreshJobs();
    } catch (err) {
      toast.error('Failed to create ingest job');
      console.error(err);
    }
  };
  
  const handleIngestUrl = async () => {
    if (!urlInput) {
      toast.error('Please enter a URL to ingest');
      return;
    }
    
    try {
      await api.createIngestUrlJob(projectId, urlInput);
      toast.success('Ingest job created successfully');
      setUrlInput('');
      refreshJobs();
    } catch (err) {
      toast.error('Failed to create ingest job');
      console.error(err);
    }
  };
  
  const handleSelectOutputFile = (filePath) => {
    setSelectedFile(filePath);
    const nextTab = filePath.includes('output') ? '2' : 
                   filePath.includes('generated') ? '3' : 
                   filePath.includes('cleaned') ? '4' : '1';
    setActiveTab(nextTab);
  };
  
  const openFileSelector = async (fileType = 'output') => {
    setFileListLoading(true);
    setFileSelectModalVisible(true);
    
    try {
      // For now, hardcode some sample files if API fails
      try {
        const result = await api.listProcessedFiles(fileType);
        setAvailableFiles(result.files || []);
      } catch (apiErr) {
        console.error('API error:', apiErr);
        
        // Fallback: manually get available files from jobs
        const availableFilesFromJobs = jobs
          .filter(job => job.status === 'completed' && job.output_file)
          .filter(job => {
            if (fileType === 'output') return job.job_type === 'ingest';
            if (fileType === 'generated') return job.job_type === 'create';
            if (fileType === 'cleaned') return job.job_type === 'curate';
            return true;
          })
          .map(job => ({
            filename: job.output_file ? job.output_file.split('/').pop() : '',
            path: job.output_file,
            type: job.job_type === 'ingest' ? 'Text file' : 
                  job.job_type === 'create' ? 'QA pairs' : 
                  job.job_type === 'curate' ? 'Curated QA pairs' : 'Unknown',
            modified: new Date(job.updated_at).getTime() / 1000,
            size: 0
          }));
        
        setAvailableFiles(availableFilesFromJobs);
      }
    } catch (err) {
      toast.error('Failed to load available files');
      console.error(err);
    } finally {
      setFileListLoading(false);
    }
  };
  
  const handleCreateQA = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }
    
    try {
      console.log(`Creating QA job for project ${projectId} with file ${selectedFile}, type ${qaType}, pairs ${numPairs}`);
      
      let result;
      try {
        // Try the normal API call first
        result = await api.createQAJob(projectId, selectedFile, qaType, numPairs);
        console.log('QA job creation result:', result);
      } catch (firstError) {
        console.error('First attempt at creating QA job failed:', firstError);
        
        // Try with a modified file path if the first attempt failed
        let modifiedPath = selectedFile;
        
        // If the path starts with 'backend/', remove it
        if (modifiedPath.startsWith('backend/')) {
          modifiedPath = modifiedPath.substring('backend/'.length);
        } 
        // Otherwise, add 'backend/' prefix if it doesn't have it
        else if (!modifiedPath.includes('backend/')) {
          modifiedPath = `backend/${modifiedPath}`;
        }
        
        console.log(`Retrying with modified path: ${modifiedPath}`);
        result = await api.createQAJob(projectId, modifiedPath, qaType, numPairs);
        console.log('QA job creation retry result:', result);
      }
      
      toast.success('QA generation job created successfully');
      refreshJobs();
    } catch (err) {
      toast.error('Failed to create QA generation job');
      console.error('Error creating QA job:', err);
    }
  };
  
  const handleCurate = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }
    
    try {
      await api.createCurateJob(projectId, selectedFile, threshold);
      toast.success('Curation job created successfully');
      refreshJobs();
    } catch (err) {
      toast.error('Failed to create curation job');
      console.error(err);
    }
  };
  
  const handleSaveAs = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }
    
    try {
      await api.createSaveJob(projectId, selectedFile, format, storage);
      toast.success('Save job created successfully');
      refreshJobs();
    } catch (err) {
      toast.error('Failed to create save job');
      console.error(err);
    }
  };
  
  const handlePreview = async (jobId) => {
    setPreviewModalVisible(true);
    setPreviewLoading(true);
    
    try {
      const result = await api.downloadJobResult(jobId);
      setPreviewContent(result);
    } catch (err) {
      setPreviewContent({ error: 'Failed to load preview' });
      console.error(err);
    } finally {
      setPreviewLoading(false);
    }
  };
  
  const renderPreviewContent = () => {
    if (!previewContent) return null;
    
    if (previewContent.error) {
      return <Alert message={previewContent.error} type="error" />;
    }
    
    try {
      // Try to parse as JSON
      const jsonData = typeof previewContent.content === 'string' 
        ? JSON.parse(previewContent.content) 
        : previewContent.content;
      
      return (
        <div className="max-h-96 overflow-auto">
          <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(jsonData, null, 2)}</pre>
        </div>
      );
    } catch (err) {
      // Not JSON, display as text
      return (
        <div className="max-h-96 overflow-auto">
          <pre className="text-sm whitespace-pre-wrap">{previewContent.content}</pre>
        </div>
      );
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }
  
  if (error) {
    return <Alert message={error} type="error" showIcon />;
  }
  
  if (!project) {
    return <Alert message="Project not found" type="error" showIcon />;
  }
  
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <Title level={2}>{project.name}</Title>
          {project.description && <Text type="secondary">{project.description}</Text>}
        </div>
        <div>
          <Button type="primary" onClick={refreshJobs}>Refresh Jobs</Button>
        </div>
      </div>
      
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={
              <span>
                <UploadOutlined />
                Ingest
              </span>
            } 
            key="1"
          >
            <div className="space-y-8">
              <div>
                <Title level={4}>Upload Files</Title>
                <Text type="secondary">Upload files to extract text for synthetic data generation</Text>
                <div className="mt-4">
                  <Upload 
                    fileList={fileList}
                    onChange={handleUploadChange}
                    beforeUpload={() => false}
                    maxCount={1}
                  >
                    <Button icon={<UploadOutlined />}>Select File</Button>
                  </Upload>
                  <div className="mt-4">
                    <Button type="primary" onClick={handleIngestFile} disabled={fileList.length === 0}>
                      Ingest File
                    </Button>
                  </div>
                </div>
              </div>
              
              <div>
                <Title level={4}>Ingest from URL</Title>
                <Text type="secondary">Extract text from YouTube videos or web pages</Text>
                <div className="mt-4">
                  <Input 
                    placeholder="Enter URL (YouTube video or web page)" 
                    value={urlInput}
                    onChange={handleUrlChange}
                    prefix={<LinkOutlined />}
                  />
                  <div className="mt-4">
                    <Button type="primary" onClick={handleIngestUrl} disabled={!urlInput}>
                      Ingest from URL
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <FileTextOutlined />
                Create QA Pairs
              </span>
            } 
            key="2"
          >
            <div className="space-y-6">
              <div>
                <Title level={4}>Generate QA Pairs</Title>
                <Text type="secondary">Create question-answer pairs from ingested text</Text>
              </div>
              
              <Form layout="vertical">
                <Form.Item label="Input File">
                  <Input 
                    value={selectedFile}
                    placeholder="Select an output file from Ingest step"
                    readOnly
                    addonAfter={
                      <Button type="link" size="small" onClick={() => openFileSelector('output')}>
                        Select File
                      </Button>
                    }
                  />
                </Form.Item>
                
                <Form.Item label="Generation Type">
                  <Select value={qaType} onChange={setQaType}>
                    <Option value="qa">Question-Answer Pairs</Option>
                    <Option value="cot">Chain of Thought Reasoning</Option>
                  </Select>
                </Form.Item>
                
                <Form.Item label="Number of Pairs">
                  <InputNumber 
                    min={1} 
                    max={100} 
                    value={numPairs} 
                    onChange={setNumPairs} 
                  />
                </Form.Item>
                
                <Form.Item>
                  <Button 
                    type="primary" 
                    onClick={handleCreateQA}
                    disabled={!selectedFile}
                  >
                    Generate QA Pairs
                  </Button>
                </Form.Item>
              </Form>
            </div>
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <FilterOutlined />
                Curate
              </span>
            } 
            key="3"
          >
            <div className="space-y-6">
              <div>
                <Title level={4}>Curate Generated Data</Title>
                <Text type="secondary">Filter and improve generated QA pairs</Text>
              </div>
              
              <Form layout="vertical">
                <Form.Item label="Input File">
                  <Input 
                    value={selectedFile}
                    placeholder="Select an output file from Create step"
                    readOnly
                    addonAfter={
                      <Button type="link" size="small" onClick={() => openFileSelector('generated')}>
                        Select File
                      </Button>
                    }
                  />
                </Form.Item>
                
                <Form.Item label="Quality Threshold (0-10)">
                  <InputNumber 
                    min={0} 
                    max={10} 
                    step={0.1}
                    value={threshold} 
                    onChange={setThreshold} 
                  />
                </Form.Item>
                
                <Form.Item>
                  <Button 
                    type="primary" 
                    onClick={handleCurate}
                    disabled={!selectedFile}
                  >
                    Curate Data
                  </Button>
                </Form.Item>
              </Form>
            </div>
          </TabPane>
          
          <TabPane 
            tab={
              <span>
                <SaveOutlined />
                Export
              </span>
            } 
            key="4"
          >
            <div className="space-y-6">
              <div>
                <Title level={4}>Export Dataset</Title>
                <Text type="secondary">Save curated data in fine-tuning format</Text>
              </div>
              
              <Form layout="vertical">
                <Form.Item label="Input File">
                  <Input 
                    value={selectedFile}
                    placeholder="Select an output file from Curate step"
                    readOnly
                    addonAfter={
                      <Button type="link" size="small" onClick={() => openFileSelector('cleaned')}>
                        Select File
                      </Button>
                    }
                  />
                </Form.Item>
                
                <Form.Item label="Format">
                  <Select value={format} onChange={setFormat}>
                    <Option value="alpaca">Alpaca</Option>
                    <Option value="ft">OpenAI Fine-tuning</Option>
                    <Option value="chatml">ChatML</Option>
                    <Option value="jsonl">JSONL</Option>
                  </Select>
                </Form.Item>
                
                <Form.Item label="Storage">
                  <Select value={storage} onChange={setStorage}>
                    <Option value="jsonl">JSONL File</Option>
                    <Option value="hf">Hugging Face Dataset</Option>
                  </Select>
                </Form.Item>
                
                <Form.Item>
                  <Button 
                    type="primary" 
                    onClick={handleSaveAs}
                    disabled={!selectedFile}
                  >
                    Export Dataset
                  </Button>
                </Form.Item>
              </Form>
            </div>
          </TabPane>
        </Tabs>
      </Card>
      
      <Card title="Project Jobs">
        <Table 
          dataSource={jobs} 
          columns={jobColumns} 
          rowKey="id"
          locale={{ emptyText: 'No jobs found' }}
        />
      </Card>
      
      <Modal
        title={previewContent?.filename || 'Download'}
        visible={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            Close
          </Button>
        ]}
      >
        {previewLoading ? (
          <div className="flex justify-center items-center h-64">
            <Spin />
          </div>
        ) : (
          renderPreviewContent()
        )}
      </Modal>
      
      {/* File Selection Modal */}
      <Modal
        title="Select Input File"
        visible={fileSelectModalVisible}
        onCancel={() => setFileSelectModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setFileSelectModalVisible(false)}>
            Cancel
          </Button>
        ]}
      >
        {fileListLoading ? (
          <div className="flex justify-center items-center h-64">
            <Spin />
          </div>
        ) : (
          <div>
            {availableFiles.length === 0 ? (
              <div className="text-center p-6">
                <Text type="secondary">No files found. Please run an ingest job first.</Text>
              </div>
            ) : (
              <Table
                dataSource={availableFiles}
                rowKey="path"
                pagination={false}
                scroll={{ y: 400 }}
                onRow={(record) => ({
                  onClick: () => {
                    setSelectedFile(record.path);
                    setFileSelectModalVisible(false);
                  },
                  style: { cursor: 'pointer' }
                })}
                columns={[
                  {
                    title: 'File Name',
                    dataIndex: 'filename',
                    key: 'filename',
                    ellipsis: true,
                  },
                  {
                    title: 'Type',
                    dataIndex: 'type',
                    key: 'type',
                    ellipsis: true,
                    width: 200,
                  },
                  {
                    title: 'Preview',
                    dataIndex: 'preview',
                    key: 'preview',
                    ellipsis: true,
                  },
                  {
                    title: 'Modified',
                    dataIndex: 'modified',
                    key: 'modified',
                    width: 180,
                    render: (text) => new Date(text * 1000).toLocaleString(),
                  },
                  {
                    title: 'Actions',
                    key: 'actions',
                    width: 120,
                    render: (_, record) => (
                      <Button 
                        type="primary" 
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFile(record.path);
                          setFileSelectModalVisible(false);
                        }}
                      >
                        Select
                      </Button>
                    ),
                  },
                ]}
              />
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default ProjectDetail;

// pages/NewProject.js
import React, { useState } from 'react';
import { Form, Input, Button, Card, Alert } from 'antd';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import toast from 'react-hot-toast';

const { TextArea } = Input;

const NewProject = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const onFinish = async (values) => {
    setLoading(true);
    setError(null);
    
    try {
      const project = await api.createProject(values);
      toast.success('Project created successfully');
      navigate(`/projects/${project.id}`);
    } catch (err) {
      setError('Failed to create project');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="max-w-2xl mx-auto">
      <Card title="Create New Project">
        {error && <Alert message={error} type="error" className="mb-4" />}
        
        <Form layout="vertical" onFinish={onFinish}>
          <Form.Item 
            label="Project Name" 
            name="name"
            rules={[{ required: true, message: 'Please enter a project name' }]}
          >
            <Input placeholder="Enter project name" />
          </Form.Item>
          
          <Form.Item 
            label="Description" 
            name="description"
          >
            <TextArea 
              placeholder="Enter a description of your project (optional)" 
              autoSize={{ minRows: 3, maxRows: 6 }}
            />
          </Form.Item>
          
          <Form.Item>
            <div className="flex justify-end">
              <Button type="primary" htmlType="submit" loading={loading}>
                Create Project
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default NewProject;

// pages/SystemSettings.js
import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Alert, Spin, Divider, Typography, Space } from 'antd';
import { api } from '../api';
import toast from 'react-hot-toast';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const SystemSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState({ status: 'unknown' });
  
  useEffect(() => {
    const fetchConfig = async () => {
      setLoading(true);
      try {
        const [config, status] = await Promise.all([
          api.getSystemConfig(),
          api.systemCheck().catch(() => ({ status: 'error', message: 'Could not connect to vLLM server' })),
        ]);
        
        form.setFieldsValue({
          vllm_api_base: config.vllm.api_base,
          vllm_model: config.vllm.model,
        });
        
        setSystemStatus(status);
      } catch (err) {
        setError('Failed to load system configuration');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchConfig();
  }, [form]);
  
  const onFinish = async (values) => {
    setSaving(true);
    setError(null);
    
    try {
      await api.updateSystemConfig({
        vllm_api_base: values.vllm_api_base,
        vllm_model: values.vllm_model,
      });
      
      toast.success('System configuration updated');
      
      // Check system status after update
      const status = await api.systemCheck().catch(() => ({ 
        status: 'error', 
        message: 'Could not connect to vLLM server' 
      }));
      setSystemStatus(status);
    } catch (err) {
      setError('Failed to update system configuration');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }
  
  return (
    <div className="max-w-3xl mx-auto">
      <Title level={2}>System Settings</Title>
      
      <Card className="mb-8">
        <Title level={4}>Server Status</Title>
        <div className="flex items-center mb-4">
          <span className="font-medium mr-2">vLLM Server:</span>
          {systemStatus.status === 'ok' ? (
            <Text type="success"><CheckCircleOutlined /> Connected</Text>
          ) : (
            <Text type="danger"><CloseCircleOutlined /> Disconnected</Text>
          )}
        </div>
        
        {systemStatus.status !== 'ok' && (
          <Alert 
            message="vLLM Server Not Connected" 
            description={
              <div>
                <Paragraph>
                  The vLLM server is required for synthetic data generation. Please start the server with:
                </Paragraph>
                <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-md">
                  vllm serve meta-llama/Llama-3.3-70B-Instruct --port 8000
                </pre>
                <Paragraph className="mt-2">
                  Note: You may need to provide a Hugging Face Authentication token. Check the README for details.
                </Paragraph>
              </div>
            }
            type="warning" 
            showIcon 
          />
        )}
      </Card>
      
      <Card title="vLLM Configuration">
        {error && <Alert message={error} type="error" className="mb-4" />}
        
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item 
            label="vLLM API Base URL" 
            name="vllm_api_base"
            rules={[{ required: true, message: 'Please enter the vLLM API base URL' }]}
          >
            <Input placeholder="http://localhost:8000/v1" />
          </Form.Item>
          
          <Form.Item 
            label="Model Name" 
            name="vllm_model"
            rules={[{ required: true, message: 'Please enter the model name' }]}
          >
            <Input placeholder="meta-llama/Llama-3.3-70B-Instruct" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={saving}>
              Save Configuration
            </Button>
          </Form.Item>
        </Form>
      </Card>
      
      <Card title="Optional Configuration" className="mt-8">
        <Paragraph>
          The following configuration options can be customized by editing the <code>configs/config.yaml</code> file directly:
        </Paragraph>
        
        <Divider orientation="left">Generation Settings</Divider>
        <ul className="list-disc pl-6">
          <li><Text strong>temperature:</Text> Controls randomness in generation (default: 0.7)</li>
          <li><Text strong>chunk_size:</Text> Size of text chunks for processing (default: 4000)</li>
          <li><Text strong>num_pairs:</Text> Default number of QA pairs to generate (default: 25)</li>
        </ul>
        
        <Divider orientation="left">Curation Settings</Divider>
        <ul className="list-disc pl-6">
          <li><Text strong>threshold:</Text> Quality threshold for filtering examples (default: 7.0)</li>
          <li><Text strong>batch_size:</Text> Number of examples to process in each batch (default: 8)</li>
        </ul>
        
        <Divider orientation="left">Custom Prompts</Divider>
        <Paragraph>
          You can also customize the prompts used for generation by editing the prompts section in the configuration file.
        </Paragraph>
      </Card>
    </div>
  );
};

export default SystemSettings;

// pages/JobDetail.js
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Descriptions, Alert, Spin, Button, Tag, Typography, Divider, Collapse } from 'antd';
import { api } from '../api';
import { ArrowLeftOutlined, DownloadOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

const JobDetail = () => {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jobConfig, setJobConfig] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [contentLoading, setContentLoading] = useState(false);
  
  const fetchJob = async () => {
    setLoading(true);
    try {
      const jobData = await api.getJob(jobId);
      setJob(jobData);
      
      if (jobData.config) {
        try {
          setJobConfig(JSON.parse(jobData.config));
        } catch (e) {
          console.error('Failed to parse job config', e);
        }
      }
    } catch (err) {
      setError('Failed to load job data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchJob();
    
    // Poll for job status updates if job is running
    const intervalId = setInterval(() => {
      if (job && job.status === 'running') {
        fetchJob();
      }
    }, 5000);
    
    return () => clearInterval(intervalId);
  }, [jobId, job?.status]);
  
  const handleViewOutput = async () => {
    if (!job || !job.output_file) return;
    
    setContentLoading(true);
    try {
      const result = await api.downloadJobResult(jobId);
      setFileContent(result);
    } catch (err) {
      console.error('Failed to load file content', err);
    } finally {
      setContentLoading(false);
    }
  };
  
  const renderJobStatus = () => {
    if (!job) return null;
    
    const statusMap = {
      pending: { color: 'default', icon: <SyncOutlined spin /> },
      running: { color: 'processing', icon: <SyncOutlined spin /> },
      completed: { color: 'success', icon: <CheckCircleOutlined /> },
      failed: { color: 'error', icon: <CloseCircleOutlined /> },
    };
    
    const status = statusMap[job.status] || statusMap.default;
    
    return (
      <Tag color={status.color} icon={status.icon}>
        {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
      </Tag>
    );
  };
  
  const renderFileContent = () => {
    if (!fileContent) return null;
    
    try {
      // Try to parse as JSON
      const jsonData = typeof fileContent.content === 'string' 
        ? JSON.parse(fileContent.content) 
        : fileContent.content;
      
      return (
        <div className="mt-4">
          <Card title={fileContent.filename}>
            <div className="max-h-96 overflow-auto">
              <pre className="text-sm whitespace-pre-wrap">{JSON.stringify(jsonData, null, 2)}</pre>
            </div>
          </Card>
        </div>
      );
    } catch (err) {
      // Not JSON, display as text
      return (
        <div className="mt-4">
          <Card title={fileContent.filename}>
            <div className="max-h-96 overflow-auto">
              <pre className="text-sm whitespace-pre-wrap">{fileContent.content}</pre>
            </div>
          </Card>
        </div>
      );
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spin size="large" />
      </div>
    );
  }
  
  if (error) {
    return <Alert message={error} type="error" showIcon />;
  }
  
  if (!job) {
    return <Alert message="Job not found" type="error" showIcon />;
  }
  
  return (
    <div className="space-y-6">
      <div>
        <Link to={`/projects/${job.project_id}`}>
          <Button type="link" icon={<ArrowLeftOutlined />} className="p-0">
            Back to Project
          </Button>
        </Link>
      </div>
      
      <div className="flex justify-between items-center">
        <Title level={2}>Job Details {renderJobStatus()}</Title>
        <Button type="primary" onClick={fetchJob}>Refresh</Button>
      </div>
      
      <Card>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Job ID">{job.id}</Descriptions.Item>
          <Descriptions.Item label="Job Type">
            <Tag color={
              job.job_type === 'ingest' ? 'blue' :
              job.job_type === 'create' ? 'green' :
              job.job_type === 'curate' ? 'orange' :
              job.job_type === 'save-as' ? 'purple' : 'default'
            }>
              {job.job_type}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Status">{renderJobStatus()}</Descriptions.Item>
          <Descriptions.Item label="Created At">{new Date(job.created_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Updated At">{new Date(job.updated_at).toLocaleString()}</Descriptions.Item>
          <Descriptions.Item label="Input File">{job.input_file || 'N/A'}</Descriptions.Item>
          <Descriptions.Item label="Output File">
            {job.output_file ? (
              <div className="flex items-center">
                <span>{job.output_file}</span>
                {job.status === 'completed' && (
                  <Button 
                    type="link" 
                    icon={<DownloadOutlined />} 
                    onClick={handleViewOutput}
                    loading={contentLoading}
                  >
                    View
                  </Button>
                )}
              </div>
            ) : 'N/A'}
          </Descriptions.Item>
        </Descriptions>
        
        {job.error && (
          <div className="mt-6">
            <Alert 
              message="Error Details" 
              description={
                <pre className="mt-2 whitespace-pre-wrap text-sm bg-gray-100 dark:bg-gray-800 p-2 rounded-md">
                  {job.error}
                </pre>
              }
              type="error" 
              showIcon 
            />
          </div>
        )}
        
        {jobConfig && (
          <div className="mt-6">
            <Collapse>
              <Panel header="Job Configuration" key="1">
                <pre className="whitespace-pre-wrap text-sm">
                  {JSON.stringify(jobConfig, null, 2)}
                </pre>
              </Panel>
            </Collapse>
          </div>
        )}
        
        {contentLoading ? (
          <div className="flex justify-center items-center h-32 mt-4">
            <Spin />
          </div>
        ) : (
          renderFileContent()
        )}
      </Card>
    </div>
  );
