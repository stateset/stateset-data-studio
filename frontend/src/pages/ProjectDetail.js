// pages/ProjectDetail.js
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api } from '../api/index';
import { Card, Button, Table, Tag, Space, Tabs, Upload, Form, Input, Select, InputNumber, Alert, Modal, Spin, Typography } from 'antd';
import { UploadOutlined, LinkOutlined, FileTextOutlined, AppstoreOutlined, FilterOutlined, SaveOutlined, DownloadOutlined } from '@ant-design/icons';
import toast from 'react-hot-toast';

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
  
  // Helper function to safely handle arrays
  const safeArray = (arr) => {
    return Array.isArray(arr) ? arr : [];
  };
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const [projectData, jobsData] = await Promise.all([
        api.getProject(projectId),
        api.listJobs({ projectId }),
      ]);
      
      // Handle both direct objects and objects with data property
      const project = projectData.project || projectData;
      const jobs = jobsData.jobs || jobsData;
      
      setProject(project);
      setJobs(Array.isArray(jobs) ? jobs : []);
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
      const jobs = jobsData.jobs || jobsData;
      setJobs(Array.isArray(jobs) ? jobs : []);
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
      render: (_, record) => {
        const outputFile = record.output_file || `data/generated/${record.id}_output.json`;
        return (
          <Space size="small">
            {record.job_type === 'ingest' && (
              <Button
                type="primary"
                size="small"
                ghost
                onClick={() => handleSelectOutputFile(record.output_file)}
              >
                Use for QA
              </Button>
            )}
            {record.job_type === 'create' && (
              <Button
                type="primary"
                size="small"
                ghost
                onClick={() => {
                  handleSelectOutputFile(outputFile);
                  setActiveTab('3');
                }}
              >
                Use for Curation
              </Button>
            )}
            {record.job_type === 'curate' && (
              <Button
                type="primary"
                size="small"
                ghost
                onClick={() => handleSelectOutputFile(outputFile)}
              >
                Use for Export
              </Button>
            )}
            <Button 
              type="text"
              icon={<DownloadOutlined />}
              size="small"
              onClick={() => handlePreview(record.id)}
            >
              Download
            </Button>
          </Space>
        );
      },
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
      const result = await api.createIngestJob(projectId, file);
      
      if (result && result.status === 'error') {
        toast.error(`Failed to create ingest job: ${result.message || result.error || 'Unknown error'}`);
        console.error('Ingest error from API:', result);
        return;
      }
      
      toast.success('Ingest job created successfully');
      setFileList([]);
      refreshJobs();
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      toast.error(`Failed to create ingest job: ${errorMessage}`);
      console.error('Ingest error:', err);
    }
  };
  
  const handleIngestUrl = async () => {
    if (!urlInput) {
      toast.error('Please enter a URL to ingest');
      return;
    }
    
    try {
      const result = await api.createIngestUrlJob(projectId, urlInput);
      
      if (result && result.status === 'error') {
        toast.error(`Failed to create ingest job: ${result.message || result.error || 'Unknown error'}`);
        console.error('URL ingest error from API:', result);
        return;
      }
      
      toast.success('Ingest job created successfully');
      setUrlInput('');
      refreshJobs();
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      toast.error(`Failed to create ingest job: ${errorMessage}`);
      console.error('URL ingest error:', err);
    }
  };
  
  const handleSelectOutputFile = (filePath) => {
    if (!filePath) {
      console.error("Cannot select output file: filePath is null or undefined");
      toast.error("Invalid output file path");
      return;
    }
    
    // Check if we need to add the backend/ prefix for paths
    let adjustedPath = filePath;
    
    // Make sure ALL data paths include backend/ prefix for consistent handling
    if (filePath.startsWith('data/')) {
      adjustedPath = `${filePath}`;
      console.log(`Adjusted input file path: ${filePath} → ${adjustedPath}`);
    }
    
    // Handle absolute paths
    if (filePath.startsWith('/home/dom/synthetic-data-studio/')) {
      // Keep absolute paths as-is
      adjustedPath = filePath;
      console.log(`Using absolute path: ${adjustedPath}`);
    }
    
    console.log(`Selected output file for next step: ${adjustedPath}`);
    setSelectedFile(adjustedPath);
    
    // Determine which tab to switch to based on the file path
    const nextTab = filePath.includes('output') ? '2' : 
                   filePath.includes('generated') ? '3' : 
                   filePath.includes('cleaned') ? '4' : '1';
    setActiveTab(nextTab);
  };
  
  const handleCreateQA = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }
    
    try {
      console.log(`Creating QA job for file: ${selectedFile}`);
      console.log(`Parameters: projectId=${projectId}, qaType=${qaType}, numPairs=${numPairs}`);
      
      // Call the API - this will try multiple endpoints
      const result = await api.createQAJob(projectId, selectedFile, qaType, numPairs);
      console.log("createQAJob result:", result);
      
      if (result && (result.error || result.status === 'error')) {
        const errorMessage = result.message || result.error || 'Unknown error';
        toast.error(`Failed to create QA generation job: ${errorMessage}`);
        console.error('QA generation error from API:', result);
        return;
      }
      
      toast.success('QA generation job created successfully');
      refreshJobs();
    } catch (err) {
      // Enhanced error handling with more details
      const errorMessage = err.message || 'Unknown error occurred';
      console.error('Full error object:', err);
      
      if (err.response) {
        console.error('Response error data:', err.response.data);
        console.error('Response status:', err.response.status);
      }
      
      toast.error(`Failed to create QA generation job: ${errorMessage}`);
      console.error('QA generation error:', err);
      
      // Show a more user-friendly error message
      toast.error("Could not generate QA pairs. Please ensure the file exists and try again.", {
        duration: 5000,
      });
    }
  };
  
  const handleCurate = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }
    
    try {
      const result = await api.createCurateJob(projectId, selectedFile, threshold);
      console.log("Curate API response:", result);

      if (result && (result.error || result.status === 'error')) {
        const errorMessage = result.message || result.error || 'Unknown error';
        toast.error(`Failed to create curation job: ${errorMessage}`);
        console.error('Curation error from API:', result);
        return;
      }
      
      toast.success('Curation job created successfully');
      refreshJobs();
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      toast.error(`Failed to create curation job: ${errorMessage}`);
      console.error('Curation error:', err);
    }
  };
  
  const handleSaveAs = async () => {
    if (!selectedFile) {
      toast.error('Please select a file first');
      return;
    }
    
    try {
      const result = await api.createSaveJob(projectId, selectedFile, format, storage);
      
      if (result && (result.error || result.status === 'error')) {
        const errorMessage = result.message || result.error || 'Unknown error';
        toast.error(`Failed to create save job: ${errorMessage}`);
        console.error('Save error from API:', result);
        return;
      }
      
      toast.success('Save job created successfully');
      refreshJobs();
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      toast.error(`Failed to create save job: ${errorMessage}`);
      console.error('Save error:', err);
    }
  };
  
  const handlePreview = async (jobId) => {
    setPreviewModalVisible(true);
    setPreviewLoading(true);
    
    try {
      const result = await api.downloadJobResult(jobId);
      
      if (result && (result.error || result.status === 'error')) {
        const errorMessage = result.message || result.error || 'Unknown error';
        setPreviewContent({ error: `Failed to load preview: ${errorMessage}` });
        console.error('Preview error from API:', result);
      } else {
        setPreviewContent(result);
      }
    } catch (err) {
      const errorMessage = err.message || 'Unknown error occurred';
      setPreviewContent({ error: `Failed to load preview: ${errorMessage}` });
      console.error('Preview error:', err);
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
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: "1",
              label: (
                <span>
                  <UploadOutlined />
                  Ingest
                </span>
              ),
              children: (
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
              )
            },
            {
              key: "2",
              label: (
                <span>
                  <FileTextOutlined />
                  Create QA Pairs
                </span>
              ),
              children: (
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
                          <Button type="link" size="small" onClick={() => setActiveTab('1')}>
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
              )
            },
            {
              key: "3",
              label: (
                <span>
                  <FilterOutlined />
                  Curate
                </span>
              ),
              children: (
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
                          <Button type="link" size="small" onClick={() => setActiveTab('1')}>
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
              )
            },
            {
              key: "4",
              label: (
                <span>
                  <SaveOutlined />
                  Export
                </span>
              ),
              children: (
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
                          <Button type="link" size="small" onClick={() => setActiveTab('1')}>
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
              )
            }
          ]}
        />
      </Card>
      
      <Card title="Project Jobs">
        <Table 
          dataSource={Array.isArray(jobs) ? jobs : []} 
          columns={jobColumns} 
          rowKey="id"
          locale={{ emptyText: 'No jobs found' }}
        />
      </Card>
      
      <Modal
        title={previewContent?.filename || 'Preview'}
        open={previewModalVisible}
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
    </div>
  );
};

export default ProjectDetail;