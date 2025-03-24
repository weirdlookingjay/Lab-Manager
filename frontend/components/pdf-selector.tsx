import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Paperclip, File, Folder, ChevronLeft, Search } from "lucide-react"
import { fetchWithAuth } from '@/app/utils/api'
import { Input } from "@/components/ui/input"

interface PDF {
  id: string
  original_filename: string
  file_url: string
  uploaded_at: string
  folder_path?: string
}

interface Folder {
  id: string
  name: string
  path: string
}

interface PDFSelectorProps {
  onSelect: (pdfs: PDF[]) => void
}

export function PDFSelector({ onSelect }: PDFSelectorProps) {
  const [pdfs, setPdfs] = useState<PDF[]>([])
  const [folders, setFolders] = useState<Folder[]>([])
  const [selectedPdfs, setSelectedPdfs] = useState<PDF[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [currentPath, setCurrentPath] = useState<string>('pdfs')
  const [breadcrumbs, setBreadcrumbs] = useState<string[]>(['pdfs'])
  const [searchQuery, setSearchQuery] = useState<string>('')
  const [searchTimeout, setSearchTimeout] = useState<NodeJS.Timeout | null>(null)

  useEffect(() => {
    // Fetch folders and PDFs when dialog opens
    if (open) {
      fetchItems()
    } else {
      // Reset to pdfs folder when dialog closes
      setCurrentPath('pdfs')
      setBreadcrumbs(['pdfs'])
      setSearchQuery('')
    }
  }, [open])

  // Debounced search effect
  useEffect(() => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }

    const timeout = setTimeout(() => {
      fetchItems()
    }, 300) // Debounce for 300ms

    setSearchTimeout(timeout)

    return () => {
      if (searchTimeout) {
        clearTimeout(searchTimeout)
      }
    }
  }, [searchQuery])

  // Fetch when changing folders (only if not searching)
  useEffect(() => {
    if (!searchQuery) {
      fetchItems()
    }
  }, [currentPath])

  const fetchItems = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        path: currentPath,
      })

      if (searchQuery) {
        params.set('search', searchQuery)
        params.set('recursive', 'true')
      }

      const data = await fetchWithAuth(`/api/notifications/files/?${params.toString()}`)
      setFolders(data.folders || [])
      setPdfs(data.pdfs || [])
    } catch (error) {
      console.error('Error fetching items:', error)
      setError(error instanceof Error ? error.message : 'Failed to fetch items')
    } finally {
      setLoading(false)
    }
  }

  const handleFolderClick = (folder: Folder) => {
    setSearchQuery('') // Clear search when navigating
    setCurrentPath(folder.path)
    setBreadcrumbs([...breadcrumbs, folder.name])
  }

  const handleBackClick = () => {
    if (breadcrumbs.length > 1) {
      setSearchQuery('') // Clear search when navigating
      const newBreadcrumbs = breadcrumbs.slice(0, -1)
      setBreadcrumbs(newBreadcrumbs)
      const newPath = newBreadcrumbs.join('/')
      setCurrentPath(newPath)
    }
  }

  const togglePDF = (pdf: PDF, checked: boolean) => {
    setSelectedPdfs(current => {
      if (checked) {
        // Add PDF if it's not already selected
        return current.some(p => p.id === pdf.id) ? current : [...current, pdf];
      } else {
        // Remove PDF
        return current.filter(p => p.id !== pdf.id);
      }
    });
  };

  const handleConfirm = () => {
    onSelect(selectedPdfs);
    setOpen(false);
    setSelectedPdfs([]);
    setCurrentPath('pdfs');
    setBreadcrumbs(['pdfs']);
    setSearchQuery('');
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" type="button">
          <Paperclip className="h-4 w-4 mr-2" />
          Select PDFs
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Select PDF Files</DialogTitle>
          <div className="relative mt-2">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search PDF files across all folders..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8"
            />
          </div>
          {!searchQuery && breadcrumbs.length > 0 && (
            <div className="flex items-center space-x-2 mt-2 text-sm text-muted-foreground">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={handleBackClick}
              >
                <ChevronLeft className="h-4 w-4" />
                <span className="sr-only">Go back</span>
              </Button>
              <span>{breadcrumbs.join(' / ')}</span>
            </div>
          )}
        </DialogHeader>
        <ScrollArea className="h-[400px] mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full text-red-500">
              <span className="text-sm">{error}</span>
              <Button variant="outline" onClick={fetchItems} className="mt-2">
                Try Again
              </Button>
            </div>
          ) : folders.length === 0 && pdfs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              {searchQuery ? 'No matching PDF files found' : 'No items available'}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Show folders first (only if not searching) */}
              {!searchQuery && folders.map((folder) => (
                <div
                  key={folder.id}
                  className="flex items-center space-x-4 p-2 hover:bg-accent rounded-lg cursor-pointer"
                  onClick={() => handleFolderClick(folder)}
                >
                  <Folder className="h-4 w-4 text-blue-500" />
                  <span className="text-sm font-medium">{folder.name}</span>
                </div>
              ))}
              
              {/* Show PDFs */}
              {pdfs.map((pdf) => (
                <div
                  key={pdf.id}
                  className="flex items-center space-x-4 p-2 hover:bg-accent rounded-lg"
                >
                  <Checkbox
                    id={pdf.id}
                    checked={selectedPdfs.some(p => p.id === pdf.id)}
                    onCheckedChange={(checked) => togglePDF(pdf, checked as boolean)}
                  />
                  <div className="flex items-center space-x-2 flex-1">
                    <File className="h-4 w-4 text-blue-500" />
                    <div className="flex flex-col">
                      <label
                        htmlFor={pdf.id}
                        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer select-none"
                      >
                        {pdf.original_filename}
                      </label>
                      {searchQuery && pdf.folder_path && (
                        <span className="text-xs text-muted-foreground mt-0.5">
                          in {pdf.folder_path}
                        </span>
                      )}
                    </div>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {pdf.uploaded_at && new Date(pdf.uploaded_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
        <div className="flex justify-end space-x-2 mt-4">
          <Button variant="outline" onClick={() => {
            setOpen(false)
            setSelectedPdfs([])
            setCurrentPath('pdfs')
            setBreadcrumbs(['pdfs'])
            setSearchQuery('')
          }}>
            Cancel
          </Button>
          <Button onClick={handleConfirm} disabled={selectedPdfs.length === 0}>
            Add Selected ({selectedPdfs.length})
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
