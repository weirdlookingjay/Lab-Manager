import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ComputerList from '../components/ComputerList';

const AdminDashboard = () => {
    const [stats, setStats] = useState({
        totalUsers: 0,
        activeComputers: 0,
        totalDocuments: 0,
        recentScans: 0
    });
    const [recentLogs, setRecentLogs] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const response = await axios.get('http://localhost:8000/api/admin/dashboard/');
            setStats(response.data.stats);
            setRecentLogs(response.data.recent_logs);
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
        }
    };

    const handleQuickAction = (action) => {
        switch (action) {
            case 'createUser':
                navigate('/admin/create-user');
                break;
            case 'addComputer':
                navigate('/admin/add-computer');
                break;
            case 'startScan':
                navigate('/admin/start-scan');
                break;
            case 'viewLogs':
                navigate('/admin/view-logs');
                break;
            default:
                break;
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            <div className="flex">
                {/* Sidebar */}
                <div className="bg-gray-800 text-white w-64 py-6 flex flex-col">
                    <div className="px-6 mb-8">
                        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
                    </div>
                    <nav className="flex-1">
                        <a href="/admin" className="block px-6 py-3 bg-gray-700">
                            <i className="fas fa-home mr-3"></i>Dashboard
                        </a>
                        <a href="/admin/users" className="block px-6 py-3 hover:bg-gray-700">
                            <i className="fas fa-users mr-3"></i>Users
                        </a>
                        <a href="/admin/computers" className="block px-6 py-3 hover:bg-gray-700">
                            <i className="fas fa-desktop mr-3"></i>Computers
                        </a>
                        <a href="/admin/documents" className="block px-6 py-3 hover:bg-gray-700">
                            <i className="fas fa-file-pdf mr-3"></i>Documents
                        </a>
                        <a href="/admin/audit-logs" className="block px-6 py-3 hover:bg-gray-700">
                            <i className="fas fa-history mr-3"></i>Audit Logs
                        </a>
                    </nav>
                </div>

                {/* Main Content */}
                <div className="flex-1">
                    <div className="container mx-auto px-6 py-8">
                        <h2 className="text-2xl font-semibold mb-8">Dashboard Overview</h2>
                        
                        {/* Quick Stats */}
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                            <div className="bg-white rounded-lg shadow-sm p-6">
                                <div className="flex items-center">
                                    <div className="p-3 bg-blue-500 rounded-lg">
                                        <i className="fas fa-users text-white text-2xl"></i>
                                    </div>
                                    <div className="ml-4">
                                        <p className="text-gray-500">Total Users</p>
                                        <p className="text-2xl font-semibold">{stats.totalUsers}</p>
                                    </div>
                                </div>
                            </div>
                            {/* Add other stat cards similarly */}
                        </div>

                        {/* Computer List */}
                        <ComputerList />

                        {/* Quick Actions */}
                        <div className="bg-white rounded-lg shadow-sm p-6 mb-8">
                            <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
                            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                <button
                                    onClick={() => handleQuickAction('createUser')}
                                    className="flex flex-col items-center p-4 bg-gray-50 rounded-lg hover:bg-gray-100"
                                >
                                    <div className="p-3 bg-blue-500 rounded-full mb-2">
                                        <i className="fas fa-user-plus text-white text-xl"></i>
                                    </div>
                                    <span className="text-sm font-medium">Create User</span>
                                </button>
                                {/* Add other quick action buttons similarly */}
                            </div>
                        </div>

                        {/* Recent Activity */}
                        <div className="bg-white rounded-lg shadow-sm p-6">
                            <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
                            <div className="space-y-4">
                                {recentLogs.map((log, index) => (
                                    <div key={index} className="flex items-center p-4 bg-gray-50 rounded-lg">
                                        <div className="p-2 bg-blue-100 rounded-full mr-4">
                                            <i className="fas fa-info-circle text-blue-500"></i>
                                        </div>
                                        <div>
                                            <p className="font-medium">{log.message}</p>
                                            <p className="text-sm text-gray-500">{log.timestamp}</p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
