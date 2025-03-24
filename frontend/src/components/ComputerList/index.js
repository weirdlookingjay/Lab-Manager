import React, { useState, useEffect } from 'react';
import axios from 'axios';

const ComputerList = () => {
    const [computers, setComputers] = useState([]);

    useEffect(() => {
        fetchComputers();
        // Refresh every 30 seconds
        const interval = setInterval(fetchComputers, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchComputers = async () => {
        try {
            console.log('Fetching computers from API...');
            const response = await axios.get('http://localhost:8000/api/computers/');
            console.log('Raw computer data:', JSON.stringify(response.data, null, 2));
            setComputers(response.data);
        } catch (error) {
            console.error('Error fetching computers:', error);
        }
    };

    return (
        <div className="container mx-auto px-4 py-8">
            <h2 className="text-2xl font-bold mb-6">Connected Computers</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {computers.map(computer => (
                    <div key={computer.id} className="bg-white rounded-lg shadow-md p-6">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-semibold">{computer.label}</h3>
                            <span className={`px-2 py-1 rounded text-sm ${computer.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                                {computer.status === 'online' ? 'Online' : 'Offline'}
                            </span>
                        </div>
                        <div className="space-y-2">
                            <p className="text-gray-600">
                                <span className="font-medium">Hostname:</span>{' '}
                                {computer.hostname || 'Unknown'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">IP:</span>{' '}
                                {computer.ip_address || 'Unknown'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">User:</span>{' '}
                                {computer.logged_in_user || 'Not logged in'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">CPU:</span>{' '}
                                {computer.cpu_model ? (
                                    <span>
                                        {computer.cpu_model.split(',')[0]}<br/>
                                        {computer.cpu_cores} cores, {computer.cpu_threads} threads
                                    </span>
                                ) : 'N/A'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">Memory:</span>{' '}
                                {computer.memory_usage ? `${computer.memory_usage}% of ${computer.memory_gb}` : 'N/A'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">Disk:</span>{' '}
                                {computer.disk_usage ? `${computer.disk_usage}% of ${computer.disk_gb}` : 'N/A'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">OS:</span>{' '}
                                {computer.os_version || 'Unknown'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">Last Seen:</span>{' '}
                                {computer.last_seen ? new Date(computer.last_seen).toLocaleString() : 'Never'}
                            </p>
                            <p className="text-gray-600">
                                <span className="font-medium">Uptime:</span>{' '}
                                {computer.uptime || 'N/A'}
                            </p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default ComputerList;
