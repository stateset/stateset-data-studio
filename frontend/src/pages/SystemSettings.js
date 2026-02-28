// pages/SystemSettings.js
import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Alert, Spin, Divider, Typography, Radio } from 'antd';
import { api } from '../api/index';
import toast from 'react-hot-toast';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const SystemSettings = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [systemStatus, setSystemStatus] = useState({ status: 'unknown' });
  const [apiType, setApiType] = useState('vllm');
  
  useEffect(() => {
    const fetchConfig = async () => {
      setLoading(true);
      try {
        const [config, status] = await Promise.all([
          api.getSystemConfig(),
          api.systemCheck().catch(() => ({ status: 'error', message: 'Could not connect to LLM server' })),
        ]);
        
        // Set API type based on config
        const currentApiType = config.api_type || 'vllm';
        setApiType(currentApiType);
        
        form.setFieldsValue({
          api_type: currentApiType,
          vllm_api_base: config.vllm?.api_base || 'http://localhost:8000/v1',
          vllm_model: config.vllm?.model || 'meta-llama/Llama-3.3-70B-Instruct',
          llama_api_key: config.llama?.api_key || '',
          llama_model: config.llama?.model || 'Llama-4-Maverick-17B-128E-Instruct-FP8',
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
      const config = {
        api_type: values.api_type,
        vllm: {
          api_base: values.vllm_api_base,
          model: values.vllm_model,
        },
        llama: {
          api_key: values.llama_api_key,
          model: values.llama_model,
        },
      };
      
      await api.updateSystemConfig(config);
      
      toast.success('System configuration updated');
      
      // Check system status after update
      const status = await api.systemCheck().catch(() => ({ 
        status: 'error', 
        message: 'Could not connect to LLM server' 
      }));
      setSystemStatus(status);
    } catch (err) {
      setError('Failed to update system configuration');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };
  
  const handleApiTypeChange = (e) => {
    setApiType(e.target.value);
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
          <span className="font-medium mr-2">LLM Server:</span>
          {systemStatus.status === 'ok' ? (
            <Text type="success"><CheckCircleOutlined /> Connected</Text>
          ) : (
            <Text type="danger"><CloseCircleOutlined /> Disconnected</Text>
          )}
        </div>
        
        {systemStatus.status !== 'ok' && (
          <Alert 
            message="LLM Server Not Connected" 
            description={
              <div>
                <Paragraph>
                  An LLM server is required for synthetic data generation. You can either:
                </Paragraph>
                <ul className="list-disc pl-6 mb-2">
                  <li>Use a local vLLM server with the command:
                    <pre className="bg-gray-100 dark:bg-gray-800 p-2 rounded-md mt-1">
                      vllm serve meta-llama/Llama-3.3-70B-Instruct --port 8000
                    </pre>
                  </li>
                  <li>Configure the Llama API connection below with your API key</li>
                </ul>
                <Paragraph className="mt-2">
                  Note: For vLLM, you may need to provide a Hugging Face Authentication token. Check the README for details.
                </Paragraph>
              </div>
            }
            type="warning" 
            showIcon 
          />
        )}
      </Card>
      
      <Card title="LLM Configuration">
        {error && <Alert message={error} type="error" className="mb-4" />}
        
        <Form form={form} layout="vertical" onFinish={onFinish}>
          <Form.Item 
            label="LLM API Type" 
            name="api_type"
            rules={[{ required: true, message: 'Please select an API type' }]}
          >
            <Radio.Group onChange={handleApiTypeChange}>
              <Radio.Button value="vllm">vLLM</Radio.Button>
              <Radio.Button value="llama">Llama API</Radio.Button>
            </Radio.Group>
          </Form.Item>
          
          {apiType === 'vllm' && (
            <>
              <Form.Item 
                label="vLLM API Base URL" 
                name="vllm_api_base"
                rules={[{ required: apiType === 'vllm', message: 'Please enter the vLLM API base URL' }]}
              >
                <Input placeholder="http://localhost:8000/v1" />
              </Form.Item>
              
              <Form.Item 
                label="vLLM Model Name" 
                name="vllm_model"
                rules={[{ required: apiType === 'vllm', message: 'Please enter the model name' }]}
              >
                <Input placeholder="meta-llama/Llama-3.3-70B-Instruct" />
              </Form.Item>
            </>
          )}
          
          {apiType === 'llama' && (
            <>
              <Form.Item 
                label="Llama API Key" 
                name="llama_api_key"
                rules={[{ required: apiType === 'llama', message: 'Please enter your Llama API key' }]}
              >
                <Input.Password placeholder="Bearer LLM|your-api-key" />
              </Form.Item>
              
              <Form.Item 
                label="Llama Model" 
                name="llama_model"
                rules={[{ required: apiType === 'llama', message: 'Please enter the Llama model name' }]}
              >
                <Input placeholder="Llama-4-Maverick-17B-128E-Instruct-FP8" />
              </Form.Item>
            </>
          )}
          
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
