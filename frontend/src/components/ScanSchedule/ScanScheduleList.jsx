import React, { useState, useRef } from 'react';
import { 
  Table, 
  Button, 
  Space, 
  Popconfirm, 
  message, 
  Tag,
  Switch,
  Typography,
  Modal 
} from 'antd';
import { DeleteOutlined, PlayCircleOutlined, PlusOutlined } from '@ant-design/icons';
import { format } from 'date-fns';
import { getAuthToken } from '../../utils/auth';
import ScanScheduleForm from './ScanScheduleForm';
import useSWR from 'swr';
import { globalFetcher, endpointConfigs } from '../../utils/api';

const { Text } = Typography;

const ScanScheduleList = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const formRef = useRef(null);

  const { data: schedules = [], error, mutate } = useSWR(
    '/api/scan-schedules/',
    globalFetcher,
    endpointConfigs.schedules
  );

  const loading = !schedules && !error;

  const showModal = () => {
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setSelectedSchedule(null);
  };

  const handleFormSuccess = () => {
    setIsModalVisible(false);
    setSelectedSchedule(null);
    // Force a full refresh of the schedules data
    mutate(undefined, true);
  };

  const handleCreate = () => {
    setSelectedSchedule(null);
    // Reset any existing form state
    if (formRef.current) {
      formRef.current.resetFields();
      formRef.current.setFieldsValue({ computer_ids: undefined });
    }
    setIsModalVisible(true);
  };

  const handleEdit = (record) => {
    console.log('Editing schedule:', record);
    if (!record || !record.id) {
      console.error('Invalid schedule record:', record);
      message.error('Cannot edit schedule: Invalid data');
      return;
    }
    setSelectedSchedule(record);
    setIsModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      const response = await fetch(`/api/scan-schedules/${id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Token ${getAuthToken()}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to delete schedule');
      
      message.success('Schedule deleted successfully');
      mutate(); // Refresh the data
    } catch (error) {
      message.error('Failed to delete schedule');
      console.error('Error:', error);
    }
  };

  const handleToggleEnabled = async (id, currentEnabled) => {
    try {
      const response = await fetch(`/api/scan-schedules/${id}/toggle_enabled/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${getAuthToken()}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to toggle schedule');
      
      message.success(`Schedule ${currentEnabled ? 'disabled' : 'enabled'} successfully`);
      mutate(); // Refresh the data
    } catch (error) {
      message.error('Failed to toggle schedule');
      console.error('Error:', error);
    }
  };

  const handleRunNow = async (id) => {
    try {
      const response = await fetch(`/api/scan-schedules/${id}/run_now/`, {
        method: 'POST',
        headers: {
          'Authorization': `Token ${getAuthToken()}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to run schedule');
      
      message.success('Scan started successfully');
      mutate(); // Refresh the data
    } catch (error) {
      message.error('Failed to start scan');
      console.error('Error:', error);
    }
  };

  const columns = [
    {
      title: 'Time',
      dataIndex: 'time',
      key: 'time',
      render: (time) => format(new Date(`2000-01-01T${time}`), 'hh:mm a'),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Next Run',
      dataIndex: 'next_run',
      key: 'next_run',
      render: (next_run) => next_run ? format(new Date(next_run), 'MM/dd/yyyy hh:mm a') : 'Not scheduled',
    },
    {
      title: 'Last Run',
      dataIndex: 'last_run',
      key: 'last_run',
      render: (last_run) => last_run ? format(new Date(last_run), 'MM/dd/yyyy hh:mm a') : 'Never',
    },
    {
      title: 'Computers',
      dataIndex: 'computer_ids',
      key: 'computer_ids',
      render: (computer_ids) => (
        <Text>{computer_ids?.length || 0} computer(s)</Text>
      ),
    },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled, record) => (
        <Switch
          checked={enabled}
          onChange={() => handleToggleEnabled(record.id, enabled)}
        />
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>Scan Schedules</Typography.Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
        >
          Create Schedule
        </Button>
      </div>

      {schedules.length === 0 && !loading ? (
        <div style={{ 
          textAlign: 'center', 
          padding: '24px',
          background: '#fafafa',
          borderRadius: '4px'
        }}>
          <Typography.Text type="secondary">
            No schedules found. Click "Create Schedule" to add one.
          </Typography.Text>
        </div>
      ) : (
        <Table 
          columns={[
            ...columns,
            {
              title: 'Actions',
              key: 'actions',
              render: (_, record) => (
                <Space>
                  <Button type="link" onClick={() => handleEdit(record)}>
                    Edit
                  </Button>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={() => handleRunNow(record.id)}
                    disabled={!record.enabled}
                  >
                    Run Now
                  </Button>
                  <Popconfirm
                    title="Delete this schedule?"
                    description="Are you sure you want to delete this schedule? This action cannot be undone."
                    onConfirm={() => handleDelete(record.id)}
                    okText="Yes"
                    cancelText="No"
                  >
                    <Button danger icon={<DeleteOutlined />}>
                      Delete
                    </Button>
                  </Popconfirm>
                </Space>
              ),
            },
          ]} 
          dataSource={schedules}
          rowKey="id"
          loading={loading}
        />
      )}
      <Modal
        title={selectedSchedule ? "Edit Schedule" : "Create Schedule"}
        open={isModalVisible}
        onCancel={handleModalCancel}
        footer={null}
        width={600}
        destroyOnClose={true}
      >
        <ScanScheduleForm 
          ref={formRef}
          key={selectedSchedule?.id || 'new'} 
          onSuccess={handleFormSuccess} 
          onCancel={handleModalCancel}
          initialData={selectedSchedule}
        />
      </Modal>
    </div>
  );
};

export default ScanScheduleList;
