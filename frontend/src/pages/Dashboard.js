// pages/Dashboard.js
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/index';
import { Card, Button, Table, Tag, Space, Alert } from 'antd';
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState({ status: 'unknown' });
  
  // Helper function to safely handle arrays
  const safeArray = (arr) => {
    return Array.isArray(arr) ? arr : [];
  };
  
  const fetchData = async () => {
    setLoading(true);
    try {
      // Test CORS first to verify connectivity
      try {
        console.log('Testing CORS connection...');
        const corsTest = await api.corsTest();
        console.log('CORS test response:', corsTest);
        // If we get here, CORS is working
      } catch (corsError) {
        console.error('CORS test failed:', corsError);
        setError('CORS test failed: ' + (corsError.message || 'Unknown error'));
        setLoading(false);
        return;
      }
      
      // If CORS test passed, load regular data
      const [projectsData, jobsData, statusData] = await Promise.all([
        api.listProjects(),
        api.listJobs({ limit: 5 }),
        api.systemCheck().catch(() => ({ status: 'error', message: 'Could not connect to vLLM server' })),
      ]);
      
      // Check if data has a property with the array inside
      const jobs = jobsData.jobs || jobsData;
      const projects = projectsData.projects || projectsData;
      
      setProjects(projects);
      setRecentJobs(jobs);
      setSystemStatus(statusData);
    } catch (err) {
      setError('Failed to load data: ' + (err.message || 'Unknown error'));
      console.error('Data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchData();
  }, []);
  
  const projectColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => <Link to={`/projects/${record.id}`}>{text}</Link>,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
    },
  ];
  
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
      title: 'Project',
      dataIndex: 'project_id',
      key: 'project_id',
      render: (text) => {
        const project = safeArray(projects).find(p => p.id === text);
        return project ? <Link to={`/projects/${text}`}>{project.name}</Link> : text;
      },
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
          <Link to={`/jobs/${record.id}`}>
            <Button type="link" size="small">View</Button>
          </Link>
        </Space>
      ),
    },
  ];
  
  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={fetchData}
          loading={loading}
        >
          Refresh
        </Button>
      </div>
      
      {error && <Alert message={error} type="error" showIcon />}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="System Status" loading={loading}>
          <div className="space-y-4">
            <div>
              <div className="text-sm text-gray-500 dark:text-gray-400">API Status</div>
              <div className="mt-1">
                  <Tag color="success">Connected</Tag>
              </div>
            </div>
            <div className="mt-4">
              <Link to="/settings">
                <Button>
                  System Settings
                </Button>
              </Link>
            </div>
          </div>
        </Card>
        
        <Card title="Projects" extra={<Link to="/projects/new"><Button icon={<PlusOutlined />}>New Project</Button></Link>} loading={loading}>
          <div>
            <div className="text-lg font-medium">{projects.length}</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Total Projects</div>
          </div>
        </Card>
        
        <Card title="Jobs" loading={loading}>
          <div className="flex space-x-4">
            <div>
              <div className="text-lg font-medium">{safeArray(recentJobs).filter(j => j.status === 'completed').length}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Completed</div>
            </div>
            <div>
              <div className="text-lg font-medium">{safeArray(recentJobs).filter(j => j.status === 'running').length}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Running</div>
            </div>
            <div>
              <div className="text-lg font-medium">{safeArray(recentJobs).filter(j => j.status === 'failed').length}</div>
              <div className="text-sm text-gray-500 dark:text-gray-400">Failed</div>
            </div>
          </div>
        </Card>
      </div>
      
      <Card title="Recent Projects" loading={loading}>
        <Table 
          dataSource={safeArray(projects).slice(0, 5)} 
          columns={projectColumns} 
          rowKey="id"
          pagination={false}
          locale={{ emptyText: 'No projects found' }}
        />
        {safeArray(projects).length > 0 && (
          <div className="mt-4 text-right">
            <Link to="/projects">View all projects</Link>
          </div>
        )}
      </Card>
      
      <Card title="Recent Jobs" loading={loading}>
        <Table 
          dataSource={safeArray(recentJobs)} 
          columns={jobColumns} 
          rowKey="id"
          pagination={false}
          locale={{ emptyText: 'No jobs found' }}
        />
      </Card>
    </div>
  );
};

export default Dashboard;