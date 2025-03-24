"use client"

import React, { useState } from 'react';

const AdminUserCreation: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [role, setRole] = useState('user');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError('');
        setSuccess('');
        
        try {
            const response = await fetch('http://localhost:8000/api/register/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                body: JSON.stringify({
                    username,
                    password,
                    email,
                    first_name: firstName,
                    last_name: lastName,
                    role,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setSuccess('User created successfully!');
                // Clear form
                setUsername('');
                setPassword('');
                setEmail('');
                setFirstName('');
                setLastName('');
                setRole('user');
            } else {
                // Handle validation errors
                if (data.username) {
                    setError(`Username error: ${data.username.join(', ')}`);
                } else if (data.email) {
                    setError(`Email error: ${data.email.join(', ')}`);
                } else if (data.password) {
                    setError(`Password error: ${data.password.join(', ')}`);
                } else {
                    setError('Failed to create user. Please check your input and try again.');
                }
                console.error('Validation errors:', data);
            }
        } catch (error) {
            setError('Network error. Please try again.');
            console.error('Error creating user:', error);
        }
    };

    return (
        <div className="p-4 border rounded-lg shadow-lg max-w-md mx-auto">
            <h2 className="text-xl font-bold mb-4">Create User Account</h2>
            
            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}
            
            {success && (
                <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                    {success}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-gray-700 mb-1">Username:</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="border rounded w-full p-2"
                        required
                        minLength={3}
                    />
                </div>
                <div>
                    <label className="block text-gray-700 mb-1">Email:</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="border rounded w-full p-2"
                        required
                    />
                </div>
                <div>
                    <label className="block text-gray-700 mb-1">First Name:</label>
                    <input
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        className="border rounded w-full p-2"
                    />
                </div>
                <div>
                    <label className="block text-gray-700 mb-1">Last Name:</label>
                    <input
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        className="border rounded w-full p-2"
                    />
                </div>
                <div>
                    <label className="block text-gray-700 mb-1">Password:</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="border rounded w-full p-2"
                        required
                        minLength={8}
                    />
                </div>
                <div>
                    <label className="block text-gray-700 mb-1">Role:</label>
                    <select
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        className="border rounded w-full p-2"
                    >
                        <option value="user">User</option>
                        <option value="admin">Admin</option>
                        <option value="moderator">Moderator</option>
                    </select>
                </div>
                <button
                    type="submit"
                    className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
                >
                    Create User
                </button>
            </form>
        </div>
    );
};

export default AdminUserCreation;