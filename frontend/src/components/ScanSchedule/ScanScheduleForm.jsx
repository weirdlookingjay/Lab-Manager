import React, { useState, useEffect } from 'react';
import { 
  Form, 
  Input, 
  Button, 
  TimePicker, 
  Radio,
  Checkbox,
  Switch,
  Row,
  Col,
  Typography,
  message 
} from 'antd';
import { getAuthToken } from '../../utils/auth';
import moment from 'moment';

const { Title } = Typography;

const ScanScheduleForm = ({ onSuccess, onCancel, initialData }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [computers, setComputers] = useState([]);

  useEffect(() => {
    fetchComputers();
    if (initialData) {
      form.setFieldsValue({
        ...initialData,
        time: initialData.time ? moment(initialData.time, 'HH:mm') : undefined
      });
    }
  }, [initialData]);

  const fetchComputers = async () => {
    try {
      const response = await fetch('/api/computers/', {
        headers: {
          'Authorization': `Token ${getAuthToken()}`,
          'Accept': 'application/json',
        },
      });
      if (!response.ok) throw new Error('Failed to fetch computers');
      const data = await response.json();
      setComputers(data.computers || []);
    } catch (error) {
      message.error('Failed to load computers');
      console.error('Error:', error);
    }
  };

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      // Format time to HH:mm format
      const formattedTime = values.time.format('HH:mm');
      
      const requestData = {
        ...values,
        time: formattedTime,
        computer_ids: values.computer_ids || [],
      };

      console.log('Submitting schedule data:', { 
        isUpdate: !!initialData?.id,
        data: requestData 
      });

      // Fix: Explicitly check for initialData.id
      const isEditing = initialData && initialData.id;
      const method = isEditing ? 'PUT' : 'POST';
      const url = isEditing
        ? `/api/scan-schedules/${initialData.id}/`
        : '/api/scan-schedules/';

      console.log('Making request:', { url, method });

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Token ${getAuthToken()}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('API Error:', { 
          status: response.status, 
          statusText: response.statusText,
          data: errorData 
        });
        throw new Error(errorData.error || `Failed to ${method.toLowerCase()} schedule`);
      }

      const responseData = await response.json();
      console.log('API Response:', responseData);

      message.success(isEditing ? 'Schedule updated successfully' : 'Schedule created successfully');
      
      // Reset form and state
      form.resetFields();
      if (!isEditing) {
        // Clear computer selection state
        form.setFieldsValue({ computer_ids: undefined });
        // Reset computers state and refetch
        setComputers([]);
        fetchComputers();
      }

      // Call onSuccess with the response data
      if (onSuccess) onSuccess(responseData);
    } catch (error) {
      message.error(error.message || 'Failed to save schedule');
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={{
        type: 'daily',
        enabled: true,
        email_notification: false,
        computer_ids: [],
      }}
    >
      <Title level={5}>Schedule Settings</Title>

      <Form.Item
        name="type"
        label="Schedule Type"
      >
        <Radio.Group>
          <Radio value="daily">Daily</Radio>
          <Radio value="weekly">Weekly</Radio>
          <Radio value="monthly">Monthly</Radio>
        </Radio.Group>
      </Form.Item>

      <Form.Item
        name="enabled"
        label="Enable Schedule"
        valuePropName="checked"
      >
        <Switch />
      </Form.Item>

      <Form.Item
        name="time"
        label="Time"
        rules={[{ required: true, message: 'Please select time' }]}
      >
        <TimePicker 
          format="hh:mm A"
          use12Hours
          style={{ width: '100%' }}
        />
      </Form.Item>

      <Form.Item
        label="Select Computers"
        required
        help="Choose which computers to scan"
      >
        <Form.Item
          name="computer_ids"
          rules={[{ required: true, message: 'Please select at least one computer' }]}
        >
          <Checkbox.Group style={{ width: '100%' }}>
            <Row>
              {computers.map(computer => (
                <Col span={8} key={computer.id}>
                  <Checkbox value={computer.id}>
                    {computer.name || computer.label}
                  </Checkbox>
                </Col>
              ))}
            </Row>
          </Checkbox.Group>
        </Form.Item>
      </Form.Item>

      <Form.Item
        name="email_notification"
        label="Email Notifications"
        valuePropName="checked"
      >
        <Switch />
      </Form.Item>

      <Form.Item
        noStyle
        shouldUpdate={(prevValues, currentValues) => 
          prevValues.email_notification !== currentValues.email_notification
        }
      >
        {({ getFieldValue }) => 
          getFieldValue('email_notification') ? (
            <Form.Item
              name="email_addresses"
              label="Email Addresses"
              rules={[{ required: true, message: 'Please enter email addresses' }]}
            >
              <Input placeholder="Enter comma-separated email addresses" />
            </Form.Item>
          ) : null
        }
      </Form.Item>

      <Form.Item>
        <Button type="default" onClick={onCancel} style={{ marginRight: 8 }}>
          Cancel
        </Button>
        <Button type="primary" htmlType="submit" loading={loading}>
          Save Changes
        </Button>
      </Form.Item>
    </Form>
  );
};

export default ScanScheduleForm;
