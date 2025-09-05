import React, { useState, useEffect } from 'react';
import { Typography, Card, Space, Spin, Input, Select, DatePicker, Button, Table, message, Tag } from 'antd';
import { api } from '../api/index';

const { Title } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;

const Logs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [logLevel, setLogLevel] = useState('all');
  const [dateRange, setDateRange] = useState(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });

  const fetchLogs = async (page = 1, pageSize = 50) => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        search: searchText || undefined,
        log_level: logLevel !== 'all' ? logLevel : undefined,
        start_date: dateRange?.[0]?.format('YYYY-MM-DD') || undefined,
        end_date: dateRange?.[1]?.format('YYYY-MM-DD') || undefined,
      };

      // Use the api utility to handle CORS and other issues
      const data = await api.getLogs(params);
      
      // Check if data is structured correctly
      if (!data || !data.logs) {
        console.error('Invalid log data structure:', data);
        message.error('Received invalid log data from server');
        setLoading(false);
        return;
      }
      
      // Format logs with sequential IDs
      const formattedLogs = data.logs.map((log, index) => ({
        key: index,
        ...log,
      }));
      
      setLogs(formattedLogs);
      setPagination({
        ...pagination,
        current: page,
        pageSize,
        total: data.total || formattedLogs.length,
      });
    } catch (error) {
      console.error('Error fetching logs:', error);
      message.error('Failed to fetch server logs');
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(pagination.current, pagination.pageSize);
  }, []);

  const handleTableChange = (pagination) => {
    fetchLogs(pagination.current, pagination.pageSize);
  };

  const handleSearch = () => {
    fetchLogs(1, pagination.pageSize);
  };

  const handleReset = () => {
    setSearchText('');
    setLogLevel('all');
    setDateRange(null);
    fetchLogs(1, pagination.pageSize);
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (text) => {
        try {
          return new Date(text).toLocaleString();
        } catch (e) {
          return text;
        }
      }
    },
    {
      title: 'Level',
      dataIndex: 'level',
      key: 'level',
      width: 100,
      render: (level) => {
        const colorMap = {
          'ERROR': 'error',
          'WARNING': 'warning',
          'INFO': 'success',
          'DEBUG': 'default'
        };
        
        return <Tag color={colorMap[level] || 'default'}>{level}</Tag>;
      }
    },
    {
      title: 'Type',
      dataIndex: 'source',
      key: 'source',
      width: 150,
      render: (source) => {
        // Map job types to nicer display names
        const typeMap = {
          'ingest': 'Ingest',
          'create': 'Create QA',
          'curate': 'Curate',
          'save-as': 'Export'
        };
        
        const displayName = typeMap[source] || source;
        return <Tag color="blue">{displayName}</Tag>;
      }
    },
    {
      title: 'Details',
      dataIndex: 'message',
      key: 'message',
      render: (message) => {
        if (!message) return <span>No details available</span>;
        
        // Split the message into parts for better display
        const parts = {};
        message.split(', ').forEach(part => {
          const [key, ...value] = part.split(': ');
          if (key && value.length > 0) {
            parts[key.trim()] = value.join(': ').trim();
          }
        });
        
        return (
          <div className="space-y-1">
            {parts.Project && (
              <div><strong>Project:</strong> {parts.Project}</div>
            )}
            {parts.Input && (
              <div><strong>Input:</strong> {parts.Input.split('/').pop()}</div>
            )}
            {parts.Output && (
              <div><strong>Output:</strong> {parts.Output.split('/').pop()}</div>
            )}
            {parts.Error && (
              <div className="text-red-500"><strong>Error:</strong> {parts.Error}</div>
            )}
          </div>
        );
      }
    },
  ];

  return (
    <div>
      <Title level={2}>Server Logs</Title>
      <Card className="mb-6">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Space wrap>
            <Input
              placeholder="Search logs"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 250 }}
              onPressEnter={handleSearch}
            />
            <Select
              value={logLevel}
              onChange={setLogLevel}
              style={{ width: 120 }}
            >
              <Option value="all">All Levels</Option>
              <Option value="INFO">Info</Option>
              <Option value="WARNING">Warning</Option>
              <Option value="ERROR">Error</Option>
              <Option value="DEBUG">Debug</Option>
            </Select>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
            />
            <Button type="primary" onClick={handleSearch}>
              Search
            </Button>
            <Button onClick={handleReset}>
              Reset
            </Button>
          </Space>
        </Space>
      </Card>

      <Card>
        <Spin spinning={loading}>
          <Table
            columns={columns}
            dataSource={logs}
            pagination={pagination}
            onChange={handleTableChange}
            scroll={{ x: 'max-content', y: 'calc(100vh - 350px)' }}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default Logs;