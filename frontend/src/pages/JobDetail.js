// pages/JobDetail.js
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Card, Descriptions, Alert, Spin, Button, Tag, Typography, Collapse } from 'antd';
import { api } from '../api/index';
import { ArrowLeftOutlined, DownloadOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';

const { Title } = Typography;
const { Panel } = Collapse;

const JobDetail = () => {
  const { jobId } = useParams();
  const [job, setJob] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [jobConfig, setJobConfig] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [contentLoading, setContentLoading] = useState(false);
  
  const fetchJob = useCallback(async () => {
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
  }, [jobId]);
  
  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  useEffect(() => {
    if (job?.status !== 'running') {
      return undefined;
    }
    const intervalId = setInterval(fetchJob, 5000);
    return () => clearInterval(intervalId);
  }, [job?.status, fetchJob]);
  
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
};

export default JobDetail;
