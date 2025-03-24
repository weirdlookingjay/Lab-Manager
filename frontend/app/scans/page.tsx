'use client'

import { useState, useEffect } from 'react'
import useSWR from 'swr'

import { 
  Play,  
  Clock, 
  StopCircle, 
  Loader2,
  FolderIcon,
  ScanLine,
  Calendar,
  Mail,
  MonitorIcon,
  Eye as EyeIcon,
  FolderOpen,
  Download,
  ChevronRightIcon
} from 'lucide-react'

import { 
  ChevronsUpDown, 
  X, 
  Settings2
} from 'lucide-react'
import { ScheduleSettings } from '../components/schedule-settings'

import {
  Command,
  CommandInput,
  CommandItem,
  CommandList,

} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

import { toast, useToast } from '@/hooks/use-toast'
import { 
  getScanStatus,
  startScan,
  stopScan,
  getComputers,
  getFolders,
  updateScanSchedule,
  deleteScanSchedule,
  runScanSchedule,
  type ScanStatus,
  type ScanSchedule,
  type Computer,
  type ScanFolder,
  globalFetcher,
  endpointConfigs,
  createScanSchedule
} from '../utils/api'

import { fetchWithAuth } from '../utils/api'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'

const INITIAL_SCAN_STATUS: ScanStatus = {
  total: 0,
  online: 0,
  offline: 0,
  enabled: 0,
  disabled: 0,
  processed_pdfs: 0,
  renamed_pdfs: 0,
  computers_scanned: 0,
  total_computers: 0,
  start_time: undefined,
  estimated_completion: undefined,
  per_computer_progress: {},
  failed_computers: [],
  retry_attempts: {},
  scan_in_progress: false,
  status: 'idle',
  scanning: false,
  queue_length: 0,
  schedule: {
    type: 'daily',
    time: '',
    selectedDays: undefined,
    monthlyDate: undefined,
    emailNotification: false,
    emailAddresses: []
  }
};

export default function ScansPage() {
  // Search and sort state
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState<'name' | 'status' | 'last_seen'>('name')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')

  // Scan status state
  const { data: scanStatusData = INITIAL_SCAN_STATUS, error: scanError, mutate: mutateScanStatus } = useSWR<ScanStatus>(
    '/api/scan/status/',
    globalFetcher,
    {
      refreshInterval: 1000,
      fallbackData: INITIAL_SCAN_STATUS
    }
  )
  const [starting, setStarting] = useState(false)
  const [stopping, setStopping] = useState(false)

  // Schedule state
  const { data: schedulesList = [], error: schedulesError, mutate: mutateSchedules } = useSWR<ScanSchedule[]>(
    '/api/scan-schedules/',
    globalFetcher,
    {
      refreshInterval: 5000,
      fallbackData: []
    }
  )
  const [isScheduleOpen, setIsScheduleOpen] = useState(false)
  const [selectedSchedule, setSelectedSchedule] = useState<ScanSchedule | undefined>(undefined)
  const [scheduleType, setScheduleType] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [scheduleTime, setScheduleTime] = useState('13:01')
  const [selected_days, setSelectedDays] = useState<number[]>([])
  const [monthly_date, setMonthlyDate] = useState<string>('1')
  const [scheduleEnabled, setScheduleEnabled] = useState(true)
  const [email_notification, setEmailNotification] = useState(false)
  const [email_addresses, setEmailAddresses] = useState<string[]>([])

  // Create a wrapper function for setMonthlyDate that accepts undefined
  const handleMonthlyDateChange = (date: string | undefined) => {
    setMonthlyDate(date ?? '1')
  }

  // Computer selection state
  const [selectedComputers, setSelectedComputers] = useState<string[]>([])
  const [isComputerSelectOpen, setIsComputerSelectOpen] = useState(false)
  const [computers, setComputers] = useState<Computer[]>([])

  // Folder state
  const [folders, setFolders] = useState<ScanFolder[]>([])
  const [selectedFolder, setSelectedFolder] = useState<ScanFolder | null>(null)
  const [folderDocuments, setFolderDocuments] = useState<{ name: string; path: string; size: number }[]>([])
  const [isFolderModalOpen, setIsFolderModalOpen] = useState(false)

  // Initialize computers from cache
  useEffect(() => {
    const cachedComputers = localStorage.getItem('computers_cache');
    if (cachedComputers) {
      setComputers(JSON.parse(cachedComputers));
    }
  }, []);

  // Load computers data with caching
  const { data: computersData, error: computersError } = useSWR<Computer[]>(
    '/api/computers/',
    globalFetcher,
    {
      ...endpointConfigs.computers,
      fallback: [], // Fallback to empty array if no data
      keepPreviousData: true,
      revalidateIfStale: false,
      revalidateOnMount: false, // Don't fetch on mount if we have cache
      onSuccess: (data) => {
        if (data) {
          setComputers(data);
          localStorage.setItem('computers_cache', JSON.stringify(data));
        }
      },
    }
  );

  // Fetch folders data
  const { data: foldersList = [], error: foldersError, mutate: mutateFolders } = useSWR<ScanFolder[]>(
    '/api/scan/folders/',
    globalFetcher,
    {
      refreshInterval: 5000,
      fallbackData: []
    }
  )

  // Handle schedule actions
  const handleScheduleSubmit = async () => {
    try {
      const scheduleData: Partial<ScanSchedule> = {
        id: selectedSchedule?.id,
        type: scheduleType,
        time: scheduleTime,
        selected_days,
        monthly_date,
        enabled: scheduleEnabled,
        email_notification,
        email_addresses,
        computer_ids: selectedComputers.map(id => parseInt(id, 10))
      }

      if (selectedSchedule) {
        await updateScanSchedule(scheduleData)
        toast({
          title: "Success",
          description: "Schedule updated successfully",
        })
      } else {
        await createScanSchedule(scheduleData)
        toast({
          title: "Success",
          description: "Schedule created successfully",
        })
      }
      
      await mutateSchedules()
      setIsScheduleOpen(false)
      setSelectedSchedule(undefined)
    } catch (error) {
      console.error('Error saving schedule:', error)
      toast({
        title: "Error",
        description: "Failed to save schedule. Please try again.",
        variant: "destructive"
      })
    }
  }

  const handleDeleteSchedule = async () => {
    if (!selectedSchedule?.id) {
      toast({
        title: "Error",
        description: "Invalid schedule ID",
        variant: "destructive"
      })
      return
    }

    try {
      await deleteScanSchedule(selectedSchedule.id)
      await mutateSchedules()
      setIsScheduleOpen(false)
      setSelectedSchedule(undefined)
      toast({
        title: "Success",
        description: "Schedule deleted successfully",
      })
    } catch (error) {
      console.error('Error deleting schedule:', error)
      toast({
        title: "Error",
        description: "Failed to delete schedule. Please try again.",
        variant: "destructive"
      })
    }
  }

  const handleStartScan = async () => {
    try {
      setStarting(true);
      await startScan(selectedComputers)
      await mutateScanStatus()
      toast({
        title: 'Scan Started',
        description: 'The scan has been started successfully.',
        variant: 'default',
      })
    } catch (error) {
      console.error('Error starting scan:', error)
      toast({
        title: 'Error',
        description: 'Failed to start scan. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setStarting(false);
    }
  }

  const handleStopScan = async () => {
    try {
      setStopping(true);
      await stopScan()
      await mutateScanStatus()
      toast({
        title: 'Scan Stopped',
        description: 'The scan has been stopped successfully.',
        variant: 'default',
      })
    } catch (error) {
      console.error('Error stopping scan:', error)
      toast({
        title: 'Error',
        description: 'Failed to stop scan. Please try again.',
        variant: 'destructive',
      })
    } finally {
      setStopping(false);
    }
  }

  const handleEmailChange = (email: string) => {
    if (email && !email_addresses.includes(email)) {
      setEmailAddresses([...email_addresses, email])
    }
  }

  const handleEmailRemove = (email: string) => {
    setEmailAddresses(email_addresses.filter(e => e !== email))
  }

  const handleComputerSelect = (computer: Computer) => {
    const computerId = computer.id.toString()
    if (selectedComputers.includes(computerId)) {
      setSelectedComputers(selectedComputers.filter(id => id !== computerId))
    } else {
      setSelectedComputers([...selectedComputers, computerId])
    }
  };

  const handleRunNow = async () => {
    if (!selectedSchedule?.id) {
      toast({
        title: "Error",
        description: "Invalid schedule ID",
        variant: "destructive"
      })
      return
    }

    try {
      await runScanSchedule(selectedSchedule.id)
      toast({
        title: 'Schedule Running',
        description: 'The scan schedule has been started.',
        variant: 'default',
      });
      // Refresh scan status to show progress
      await mutateScanStatus();
    } catch (error) {
      console.error('Error running schedule:', error);
      toast({
        title: 'Error',
        description: 'Failed to run schedule. Please try again.',
        variant: 'destructive',
      });
    }
  };

  // Function to fetch documents for a folder
  const fetchFolderDocuments = async (folder: ScanFolder) => {
    try {
      const response = await fetchWithAuth(`/api/documents/?computer=${folder.name}`);
      if (!response.ok) throw new Error('Failed to fetch documents');
      const data = await response.json();
      setFolderDocuments(data.documents);
    } catch (error) {
      console.error('Error fetching folder documents:', error);
      toast({
        title: "Error",
        description: "Failed to fetch documents. Please try again.",
        variant: "destructive"
      });
    }
  };

  // Function to download document
  const handleDownload = async (path: string, name: string) => {
    try {
      const url = new URL('http://localhost:8000/api/documents/download/');
      url.searchParams.set('path', path);
      url.searchParams.set('preview', 'false');

      const response = await fetch(url.toString());
      if (!response.ok) throw new Error('Download failed');

      // Get the blob from the response
      const blob = await response.blob();
      
      // Create a temporary URL for the blob
      const downloadUrl = window.URL.createObjectURL(blob);
      
      // Create a temporary link element
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = name;
      
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the URL
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Error downloading document:', error);
      toast({
        title: "Error",
        description: `Failed to download ${name}`,
        variant: "destructive"
      });
    }
  };

  // Filter and sort computers
  const filteredComputers = (computers || []).filter(computer => {
    const query = searchQuery.toLowerCase();
    return (
      (computer?.name?.toLowerCase() || '').includes(query) ||
      (computer?.label?.toLowerCase() || '').includes(query) ||
      (computer?.ip?.toLowerCase() || '').includes(query)
    );
  }).sort((a, b) => {
    let compareResult = 0;
    switch (sortField) {
      case 'name':
        compareResult = (a?.name || '').localeCompare(b?.name || '');
        break;
      case 'status':
        compareResult = (a?.status || '').localeCompare(b?.status || '');
        break;
      case 'last_seen':
        compareResult = new Date(b?.last_seen || 0).getTime() - new Date(a?.last_seen || 0).getTime();
        break;
    }
    return sortDirection === 'asc' ? compareResult : -compareResult;
  });

  // Get the count of selected computers that are currently visible
  const visibleSelectedCount = selectedComputers.filter(id => 
    filteredComputers.some(c => c.id.toString() === id)
  ).length

  const handleSelectAll = () => {
    // Only select filtered computers when there's a search query
    if (searchQuery) {
      const filteredIds = filteredComputers.map(c => c.id.toString())
      setSelectedComputers(prev => {
        const existingSelected = prev.filter(id => !filteredComputers.some(c => c.id.toString() === id))
        return [...existingSelected, ...filteredIds]
      })
    } else {
      // Select all computers when no search query
      const allIds = computers.map(c => c.id.toString())
      setSelectedComputers(allIds)
    }
  }

  const handleDeselectAll = () => {
    // Only deselect filtered computers when there's a search query
    if (searchQuery) {
      const filteredIds = filteredComputers.map(c => c.id.toString())
      setSelectedComputers(prev => prev.filter(id => !filteredIds.includes(id)))
    } else {
      // Deselect all when no search query
      setSelectedComputers([])
    }
  }

  // Get scan progress for a specific computer
  const getComputerProgress = (computerId: string) => {
    return scanStatusData?.per_computer_progress?.[computerId] ?? 0;
  }

  // Check if a computer has failed
  const getComputerError = (computerId: string) => {
    return scanStatusData?.failed_computers?.find(fc => fc.computer === computerId)?.error;
  }

  if (!scanStatusData) {
    return (
      <div className="container mx-auto py-6">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading scan status...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex justify-between items-center mb-6">
        <Input
          placeholder="Search by name, asset, or IP..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="max-w-sm"
        />
        <Select
          value={sortField}
          onValueChange={(value) => setSortField(value as 'name' | 'status' | 'last_seen')}
        >
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="name">Name</SelectItem>
            <SelectItem value="status">Status</SelectItem>
            <SelectItem value="last_seen">Last Seen</SelectItem>
          </SelectContent>
        </Select>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
        >
          <ChevronsUpDown className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid gap-6 grid-cols-1 lg:grid-cols-2">
        {/* Scan Status Card */}
        <Card className="bg-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ScanLine className="h-5 w-5 text-primary" />
                <CardTitle>Scan Status</CardTitle>
              </div>
            </div>
            <CardDescription>Current scan progress and statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Badge variant={scanStatusData.scanning ? "default" : "secondary"} className="h-6">
                  {scanStatusData.scanning ? "Scanning" : "Ready to Scan"}
                </Badge>
                {scanStatusData.scanning ? (
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={handleStopScan}
                    disabled={stopping}
                  >
                    {stopping ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Stopping
                      </>
                    ) : (
                      <>
                        <StopCircle className="mr-2 h-4 w-4" />
                        Stop Scan
                      </>
                    )}
                  </Button>
                ) : (
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleStartScan}
                    disabled={starting || selectedComputers.length === 0}
                  >
                    {starting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Starting
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Start Scan
                      </>
                    )}
                  </Button>
                )}
              </div>

              <div className="space-y-2">
                <Label>Overall Progress</Label>
                <Progress value={scanStatusData.computers_scanned / scanStatusData.total_computers * 100} className="h-2" />
                <div className="text-sm text-muted-foreground">
                  {scanStatusData.computers_scanned} of {scanStatusData.total_computers} computers
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <Label>Processed PDFs</Label>
                  <div className="text-2xl font-bold">{scanStatusData.processed_pdfs}</div>
                </div>
                <div className="space-y-1">
                  <Label>Renamed PDFs</Label>
                  <div className="text-2xl font-bold">{scanStatusData.renamed_pdfs}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* PDF Folders Card */}
        <Card className="bg-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FolderIcon className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-primary-foreground">PDF Folders</h2>
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Computer folders containing scanned PDFs
            </p>
            <div className="space-y-2">
              {foldersError ? (
                <div className="text-center py-4 text-destructive">
                  Error loading folders
                </div>
              ) : !foldersList?.length ? (
                <div className="text-center py-4 text-muted-foreground">
                  No folders found
                </div>
              ) : (
                foldersList.map((folder) => (
                  <div
                    key={folder.path}
                    className="flex items-center justify-between rounded-lg border p-4 hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedFolder(folder);
                      fetchFolderDocuments(folder);
                      setIsFolderModalOpen(true);
                    }}
                  >
                    <div className="flex items-center space-x-4">
                      <FolderIcon className="h-6 w-6 text-primary" />
                      <div>
                        <div className="font-medium">{folder.name}</div>
                        <div className="text-sm text-muted-foreground">
                        {folder.pdf_count} PDF{folder.pdf_count !== 1 ? 's' : ''} *{formatBytes(folder.total_size)}
                        </div>
                      </div>
                    </div>
                    <ChevronRightIcon className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
                  </div>
                ))
              )}
            </div>
          </CardHeader>
        </Card>

        {/* Scan Schedule Card */}
        <Card className="bg-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" />
                <CardTitle>Scan Schedule</CardTitle>
              </div>
            </div>
            <CardDescription>Configure automated scan schedules</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-medium">Active Schedules</h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setSelectedSchedule(undefined);
                    setIsScheduleOpen(true);
                  }}
                >
                  Create New Schedule
                </Button>
              </div>

              {schedulesError ? (
                <div className="text-center py-4 text-destructive">
                  Error loading schedules
                </div>
              ) : schedulesList.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground">
                  No schedules found
                </div>
              ) : (
                schedulesList.map((schedule) => (
                  <div
                    key={schedule.id}
                    className="flex items-center justify-between p-3 rounded-lg border hover:bg-accent hover:text-accent-foreground transition-colors cursor-pointer"
                    onClick={() => {
                      setSelectedSchedule(schedule);
                      setScheduleType(schedule.type || 'daily');
                      setScheduleTime(schedule.time || '13:01');
                      setSelectedDays(schedule.selected_days || []);
                      setMonthlyDate(schedule.monthly_date || '1');
                      setScheduleEnabled(schedule.enabled ?? false);
                      setEmailNotification(schedule.email_notification ?? false);
                      setEmailAddresses(schedule.email_addresses || []);
                      setIsScheduleOpen(true);
                    }}
                  >
                    <div className="flex items-center gap-3">
                      <Clock className="h-5 w-5 text-primary" />
                      <div>
                        <div className="font-medium">
                          {schedule.type?.charAt(0).toUpperCase() + schedule.type?.slice(1)} Schedule
                          <Badge variant={schedule.enabled ? "default" : "secondary"} className="ml-2">
                            {schedule.enabled ? "Enabled" : "Disabled"}
                          </Badge>
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Time: {schedule.time}
                        </div>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedSchedule(schedule);
                        setIsScheduleOpen(true);
                      }}
                    >
                      <Settings2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Select Computers Card */}
        <Card className="bg-card">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MonitorIcon className="h-5 w-5 text-primary" />
                <CardTitle>Select Computers</CardTitle>
              </div>
            </div>
            <CardDescription>Choose which computers to scan</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Popover open={isComputerSelectOpen} onOpenChange={setIsComputerSelectOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={isComputerSelectOpen}
                    className="w-full justify-between"
                  >
                    {selectedComputers.length > 0
                      ? `${selectedComputers.length} computers selected`
                      : "Select computers..."}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0">
                  <Command>
                    <CommandInput placeholder="Search computers..." />
                    <CommandList>
                      {computers.map((computer) => (
                        <CommandItem
                          key={computer.id}
                          onSelect={() => handleComputerSelect(computer)}
                        >
                          <Checkbox
                            checked={selectedComputers.includes(computer.id.toString())}
                            className="mr-2"
                          />
                          {computer.name}
                        </CommandItem>
                      ))}
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>
          </CardContent>
        </Card>
      </div>

      <Dialog open={isScheduleOpen} onOpenChange={setIsScheduleOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{selectedSchedule ? 'Edit Schedule' : 'Create New Schedule'}</DialogTitle>
            <DialogDescription>
              Set up automated scanning schedule for selected computers
            </DialogDescription>
          </DialogHeader>
          <ScheduleSettings
            open={isScheduleOpen}
            onClose={() => setIsScheduleOpen(false)}
            schedule={selectedSchedule}
            onSubmit={handleScheduleSubmit}
            computers={computers}
            selectedComputers={selectedComputers}
            onComputerSelectionChange={setSelectedComputers}
            selected_days={selected_days}
            setSelectedDays={setSelectedDays}
            monthlyDate={monthly_date}
            setMonthlyDate={handleMonthlyDateChange}
            scheduleType={scheduleType}
            setScheduleType={setScheduleType}
            scheduleTime={scheduleTime}
            setScheduleTime={setScheduleTime}
            scheduleEnabled={scheduleEnabled}
            setScheduleEnabled={setScheduleEnabled}
            email_notification={email_notification}
            setEmailNotification={setEmailNotification}
            email_addresses={email_addresses}
            setEmailAddresses={setEmailAddresses}
            mutateSchedule={mutateSchedules}
          />
        </DialogContent>
      </Dialog>

      {/* Folder Contents Dialog */}
      <Dialog open={isFolderModalOpen} onOpenChange={setIsFolderModalOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FolderIcon className="h-5 w-5" />
              {selectedFolder?.name} Contents
            </DialogTitle>
            <DialogDescription>
              {folderDocuments.length} PDF{folderDocuments.length !== 1 ? 's' : ''} • {formatBytes(selectedFolder?.total_size || 0)}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {folderDocuments.map((doc) => (
                  <TableRow key={doc.path}>
                    <TableCell className="font-medium">{doc.name}</TableCell>
                    <TableCell>{formatBytes(doc.size)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDownload(doc.path, doc.name)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} bytes`
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(2)} KB`
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(2)} MB`
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`
}
