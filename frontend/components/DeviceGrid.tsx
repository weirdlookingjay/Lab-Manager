'use client'

import { CheckCircleIcon, XCircleIcon } from '@heroicons/react/20/solid'

interface Device {
  id: string
  name: string
  status: 'online' | 'offline'
  lastCheckIn: string
  ipAddress: string
  location: string
  type: string
}

interface DeviceGridProps {
  devices: Device[]
}

export default function DeviceGrid({ devices }: DeviceGridProps) {
  return (
    <div className="mt-8 flow-root">
      <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
        <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
          <table className="min-w-full divide-y divide-gray-300">
            <thead>
              <tr>
                <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-0">
                  Name
                </th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                  Status
                </th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                  Last Check-in
                </th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                  IP Address
                </th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                  Location
                </th>
                <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                  Type
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {devices.map((device) => (
                <tr key={device.id}>
                  <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-0">
                    {device.name}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm">
                    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ${
                      device.status === 'online' 
                        ? 'bg-green-50 text-green-700 ring-1 ring-inset ring-green-600/20' 
                        : 'bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20'
                    }`}>
                      {device.status === 'online' ? (
                        <CheckCircleIcon className="mr-1 h-4 w-4 text-green-400" aria-hidden="true" />
                      ) : (
                        <XCircleIcon className="mr-1 h-4 w-4 text-red-400" aria-hidden="true" />
                      )}
                      {device.status}
                    </span>
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {device.lastCheckIn}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {device.ipAddress}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {device.location}
                  </td>
                  <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                    {device.type}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
