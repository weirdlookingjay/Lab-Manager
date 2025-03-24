'use client';

import { useState, useEffect, useCallback, memo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/app/contexts/AuthContext';
import { fetchWithAuth } from '@/app/utils/api';
import Cookies from 'js-cookie';


interface User {
    id: string;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    created: string;
    status: string;
    is_active: boolean;
    role: string;
}

interface Stats {
    totalUsers: number;
    activeUsers: number;
    newUsers30Days: number;
    verifiedUsers: number;
    roleDistribution: { [key: string]: number };
    staffUsers: number;
    superUsers: number;
    lockedUsers: number;
}

interface CreateUserModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: () => void;
    userData: {
        username: string;
        email: string;
        password: string;
        first_name: string;
        last_name: string;
        role: string;
    };
    error: string;
    onInputChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => void;
}

interface ResetPasswordModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (password: string) => void;
    error: string;
    username: string;
}

const CreateUserModal = memo(({ isOpen, onClose, onSubmit, userData, error, onInputChange }: CreateUserModalProps) => {
    if (!isOpen) return null;
    
    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                    <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                    <form onSubmit={(e) => {
                        e.preventDefault();
                        onSubmit();
                    }}>
                        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div className="sm:flex sm:items-start">
                                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Create New User</h3>
                                    {error && (
                                        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
                                            <span className="block sm:inline">{error}</span>
                                        </div>
                                    )}
                                    <div className="space-y-4">
                                        <div>
                                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
                                            <input
                                                type="text"
                                                id="username"
                                                value={userData.username}
                                                onChange={onInputChange}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                required
                                                autoComplete="off"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="email" className="block text-sm font-medium text-gray-700">Email</label>
                                            <input
                                                type="email"
                                                id="email"
                                                value={userData.email}
                                                onChange={onInputChange}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                required
                                                autoComplete="off"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
                                            <input
                                                type="password"
                                                id="password"
                                                value={userData.password}
                                                onChange={onInputChange}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                required
                                                autoComplete="new-password"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="role" className="block text-sm font-medium text-gray-700">Role</label>
                                            <select
                                                id="role"
                                                value={userData.role}
                                                onChange={onInputChange}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                required
                                            >
                                                <option value="">Select a role</option>
                                                <option value="user">User</option>
                                                <option value="staff">Staff</option>
                                                <option value="admin">Admin</option>
                                            </select>
                                        </div>
                                        <div>
                                            <label htmlFor="firstName" className="block text-sm font-medium text-gray-700">First Name</label>
                                            <input
                                                type="text"
                                                id="firstName"
                                                value={userData.first_name}
                                                onChange={onInputChange}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                autoComplete="off"
                                            />
                                        </div>
                                        <div>
                                            <label htmlFor="lastName" className="block text-sm font-medium text-gray-700">Last Name</label>
                                            <input
                                                type="text"
                                                id="lastName"
                                                value={userData.last_name}
                                                onChange={onInputChange}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                autoComplete="off"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 sm:px-6">
                            <div className="flex items-center justify-between">
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    Create
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
});

const ResetPasswordModal = memo(({ isOpen, onClose, onSubmit, error, username }: ResetPasswordModalProps) => {
    const [password, setPassword] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit(password);
    };

    if (!isOpen) return null;
    
    return (
        <div className="fixed inset-0 z-50 overflow-y-auto">
            <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
                <div className="fixed inset-0 transition-opacity" aria-hidden="true">
                    <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
                </div>
                <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
                <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
                    <form onSubmit={handleSubmit}>
                        <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                            <div className="sm:flex sm:items-start">
                                <div className="mt-3 text-center sm:mt-0 sm:text-left w-full">
                                    <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Reset Password for {username}</h3>
                                    {error && (
                                        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
                                            <span className="block sm:inline">{error}</span>
                                        </div>
                                    )}
                                    <div className="space-y-4">
                                        <div>
                                            <label htmlFor="newPassword" className="block text-sm font-medium text-gray-700">New Password</label>
                                            <input
                                                type="password"
                                                id="newPassword"
                                                value={password}
                                                onChange={(e) => setPassword(e.target.value)}
                                                className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                                required
                                                autoComplete="new-password"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 sm:px-6">
                            <div className="flex items-center justify-between">
                                <button
                                    type="button"
                                    onClick={onClose}
                                    className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:ml-3 sm:w-auto sm:text-sm"
                                >
                                    Reset Password
                                </button>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
});

const AdminPage: React.FC = () => {
    const { user } = useAuth();
    const [users, setUsers] = useState<User[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [itemsPerPage, setItemsPerPage] = useState(50);
    const [currentPage, setCurrentPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [error, setError] = useState('');
    const [stats, setStats] = useState<Stats>({
        totalUsers: 0,
        activeUsers: 0,
        newUsers30Days: 0,
        verifiedUsers: 0,
        roleDistribution: {},
        staffUsers: 0,
        superUsers: 0,
        lockedUsers: 0
    });

    const [newUser, setNewUser] = useState({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        role: '',
    });

    const [isResetPasswordModalOpen, setIsResetPasswordModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<{ id: string; username: string } | null>(null);
    const [resetPasswordError, setResetPasswordError] = useState('');

    const fetchUsers = async () => {
        try {
            setLoading(true);
            const response = await fetchWithAuth<User[]>('/api/auth/users/');
            setUsers(response);
        } catch (error) {
            console.error('Error fetching users:', error);
            setError('Failed to fetch users');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [usersData, statsData] = await Promise.all([
                    fetchWithAuth<User[]>('/api/auth/users/'),
                    fetchWithAuth<Stats>('/api/auth/users/stats/')
                ]);
                setUsers(usersData);
                setStats(statsData);
            } catch (error) {
                console.error('Error fetching data:', error);
                setError('Failed to fetch data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (user.first_name && user.first_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
        (user.last_name && user.last_name.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedUsers = filteredUsers.slice(startIndex, endIndex);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'Active':
                return 'bg-green-100 text-green-800';
            case 'Deactivated':
                return 'bg-red-100 text-red-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const formatDate = (dateString: string) => {
        if (!dateString) return 'N/A';
        
        // The date should already be in YYYY-MM-DD format from the backend
        const [year, month, day] = dateString.split('-');
        if (year && month && day) {
            return `${month}/${day}/${year}`;
        }
        return dateString;
    };

    const handleAction = async (userId: string, action: string) => {
        try {
            const endpoint = `/api/auth/users/${userId}/${action}/`;
            await fetchWithAuth<void>(endpoint, {
                method: 'POST',
            });

            // Refresh the user list after successful action
            await fetchUsers();
        } catch (error) {
            console.error(`Error ${action}ing user:`, error);
            setError(`Failed to ${action} user`);
        }
    };

    const handleCreateUser = useCallback(async () => {
        try {
            const data = await fetchWithAuth('/api/auth/users/create_user/', {
                method: 'POST',
                body: JSON.stringify(newUser),
            });

            // Reset form and close modal
            setNewUser({
                username: '',
                email: '',
                password: '',
                first_name: '',
                last_name: '',
                role: '',
            });
            setError('');
            setIsCreateModalOpen(false);

            // Refresh users and stats
            const [usersData, statsData] = await Promise.all([
                fetchWithAuth<User[]>('/api/auth/users/'),
                fetchWithAuth<Stats>('/api/auth/users/stats/')
            ]);

            setUsers(Array.isArray(usersData) ? usersData : []);
            setStats(statsData);
        } catch (error: any) {
            console.error('Error creating user:', error);
            setError(error.message || 'Failed to create user. Please try again.');
        }
    }, [newUser]);

    const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { id, value } = e.target;
        setNewUser(prev => ({
            ...prev,
            [id === 'firstName' ? 'first_name' : 
             id === 'lastName' ? 'last_name' : id]: value
        }));
    }, []);

    const handleCloseModal = useCallback(() => {
        setIsCreateModalOpen(false);
        setError('');
        setNewUser({
            username: '',
            email: '',
            password: '',
            first_name: '',
            last_name: '',
            role: '',
        });
    }, []);

    const openCreateModal = useCallback(() => {
        setNewUser({
            username: '',
            email: '',
            password: '',
            first_name: '',
            last_name: '',
            role: '',
        });
        setIsCreateModalOpen(true);
    }, []);

    const handleResetPassword = useCallback(async (password: string) => {
        if (!selectedUser) return;
        
        try {
            const data = await fetchWithAuth(`/api/auth/users/${selectedUser.id}/reset_password/`, {
                method: 'POST',
                body: JSON.stringify({ password }),
            });
            
            setResetPasswordError('');
            setIsResetPasswordModalOpen(false);
            setSelectedUser(null);
        } catch (error: any) {
            console.error('Error resetting password:', error);
            setResetPasswordError(error.message || 'Failed to reset password. Please try again.');
        }
    }, [selectedUser]);

    const handleCloseResetPasswordModal = useCallback(() => {
        setIsResetPasswordModalOpen(false);
        setResetPasswordError('');
        setSelectedUser(null);
    }, []);

    const openResetPasswordModal = useCallback((user: { id: string; username: string }) => {
        setSelectedUser(user);
        setIsResetPasswordModalOpen(true);
    }, []);

    const ActionButtons = ({ userId, status, username }: { userId: string, status: string, username: string }) => (
        <div className="flex items-center space-x-2">
            <button
                onClick={() => openResetPasswordModal({ id: userId, username })}
                className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
                Reset Password
            </button>
            <button
                onClick={() => handleAction(userId, 'deactivate')}
                className="inline-flex items-center px-2.5 py-1.5 border border-gray-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
                Deactivate
            </button>
            <button
                onClick={() => handleAction(userId, 'delete')}
                className="inline-flex items-center px-2.5 py-1.5 border border-red-300 text-xs font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
                Delete
            </button>
        </div>
    );

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900">Total Users</h3>
                    <p className="text-3xl font-bold text-blue-600">{stats.totalUsers}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900">Active Users</h3>
                    <p className="text-3xl font-bold text-green-600">{stats.activeUsers}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900">New Users (30 Days)</h3>
                    <p className="text-3xl font-bold text-purple-600">{stats.newUsers30Days}</p>
                </div>
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900">Staff Users</h3>
                    <p className="text-3xl font-bold text-orange-600">{stats.staffUsers}</p>
                </div>
            </div>

            <div className="flex justify-between items-center mb-6">
                <h1 className="text-2xl font-bold">Users ({users.length})</h1>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                >
                    Create User
                </button>
            </div>

            <div className="mb-4">
                <input
                    type="text"
                    placeholder="Search by username, email, or name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-2 border rounded"
                />
            </div>

            <div className="bg-white shadow-md rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {paginatedUsers.map((user) => (
                            <tr key={user.id}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                        <div className="h-8 w-8 rounded-full bg-gray-200 flex items-center justify-center">
                                            {user.username.charAt(0).toUpperCase()}
                                        </div>
                                        <div className="ml-4">
                                            <div className="text-sm font-medium text-gray-900">{user.username}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-900">
                                        {user.first_name} {user.last_name}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-900">{user.email}</div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm text-gray-500">
                                        {formatDate(user.created)}
                                    </div>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(user.status)}`}>
                                        {user.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                    <button
                                        onClick={() => {
                                            setSelectedUser({ id: user.id, username: user.username });
                                            setIsResetPasswordModalOpen(true);
                                        }}
                                        className="text-blue-600 hover:text-blue-900"
                                    >
                                        Reset Password
                                    </button>
                                    {user.is_active ? (
                                        <button
                                            onClick={() => handleAction(user.id, 'deactivate')}
                                            className="text-red-600 hover:text-red-900"
                                        >
                                            Deactivate
                                        </button>
                                    ) : (
                                        <button
                                            onClick={() => handleAction(user.id, 'activate')}
                                            className="text-green-600 hover:text-green-900"
                                        >
                                            Activate
                                        </button>
                                    )}
                                    <button
                                        onClick={() => handleAction(user.id, 'delete')}
                                        className="text-red-600 hover:text-red-900"
                                    >
                                        Delete
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="bg-white px-4 py-3 border-t border-gray-200 sm:px-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <span className="text-sm text-gray-700">
                            Rows per page:
                        </span>
                        <select
                            value={itemsPerPage}
                            onChange={(e) => setItemsPerPage(Number(e.target.value))}
                            className="ml-2 border-gray-300 rounded-md text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value={10}>10</option>
                            <option value={25}>25</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                        </select>
                    </div>
                    <div className="flex items-center space-x-2">
                        <span className="text-sm text-gray-700">
                            {startIndex + 1}-{Math.min(endIndex, filteredUsers.length)} of {filteredUsers.length}
                        </span>
                        <button
                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                            disabled={currentPage === 1}
                            className="relative inline-flex items-center px-2 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Previous
                        </button>
                        <button
                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                            disabled={currentPage === totalPages}
                            className="relative inline-flex items-center px-2 py-2 rounded-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Next
                        </button>
                    </div>
                </div>
            </div>

            <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Role Distribution</h3>
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700">Admin Users</span>
                                <span className="text-sm font-medium text-gray-900">{stats.superUsers}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{ width: `${(stats.superUsers / stats.totalUsers * 100) || 0}%` }}
                                ></div>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700">Staff Users</span>
                                <span className="text-sm font-medium text-gray-900">{stats.staffUsers}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-green-600 h-2 rounded-full"
                                    style={{ width: `${(stats.staffUsers / stats.totalUsers * 100) || 0}%` }}
                                ></div>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700">Regular Users</span>
                                <span className="text-sm font-medium text-gray-900">
                                    {stats.totalUsers - stats.staffUsers - stats.superUsers}
                                </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-purple-600 h-2 rounded-full"
                                    style={{ width: `${((stats.totalUsers - stats.staffUsers - stats.superUsers) / stats.totalUsers * 100) || 0}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">User Status</h3>
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700">Active Users</span>
                                <span className="text-sm font-medium text-gray-900">{stats.activeUsers}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-green-600 h-2 rounded-full"
                                    style={{ width: `${(stats.activeUsers / stats.totalUsers * 100) || 0}%` }}
                                ></div>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700">Locked Users</span>
                                <span className="text-sm font-medium text-gray-900">{stats.lockedUsers}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-red-600 h-2 rounded-full"
                                    style={{ width: `${(stats.lockedUsers / stats.totalUsers * 100) || 0}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">User Growth</h3>
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm font-medium text-gray-700">New Users (30 Days)</span>
                                <span className="text-sm font-medium text-gray-900">{stats.newUsers30Days}</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                    className="bg-blue-600 h-2 rounded-full"
                                    style={{ width: `${(stats.newUsers30Days / stats.totalUsers * 100) || 0}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <CreateUserModal 
                isOpen={isCreateModalOpen}
                onClose={handleCloseModal}
                onSubmit={handleCreateUser}
                userData={newUser}
                error={error}
                onInputChange={handleInputChange}
            />
            <ResetPasswordModal
                isOpen={isResetPasswordModalOpen}
                onClose={handleCloseResetPasswordModal}
                onSubmit={handleResetPassword}
                error={resetPasswordError}
                username={selectedUser?.username || ''}
            />
        </div>
    );
};

export default AdminPage;