// pages/NewProject.js
import React, { useState } from 'react';
import { Form, Input, Button, Card, Alert } from 'antd';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/index';
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