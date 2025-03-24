'use client';

import { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { PdfPreviewModal } from '../components/ui/pdf-preview-modal';
import { DocumentTags } from '@/components/documents/DocumentTags';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { QuestionInput } from '@/components/QuestionInput';
import { AnswerDisplay } from '@/components/AnswerDisplay';

import { 
  Loader2, 
  Download as DownloadIcon, 
  Eye as EyeIcon,
  Tag as TagIcon,
  MoreHorizontal,
  Brain,
} from "lucide-react";
import { getComputers, getDocuments } from '@/app/utils/api';
import { 
  fetchWithAuth, 
  type Computer,
  type Tag,
  type ApiTag 
} from '../utils/api';
import Cookies from 'js-cookie';
import { useToast } from '@/hooks/use-toast';
import { formatFileSize } from '@/lib/utils';
import { useDocumentSelection } from '@/hooks/useDocumentSelection';
import { useDocumentTags } from '@/hooks/useDocumentTags';
import { BulkActionBar } from '@/components/documents/BulkActionBar';
import { DocumentCheckbox } from '@/components/documents/DocumentCheckbox';

// API base URL
const API_BASE = '/api/auth';

interface Document {
  name: string;
  path: string;
  type: 'document';
  size: number;
  created: string;
  tags: Tag[];
}

interface Folder {
  name: string;
  type: 'folder';
}

// Default color for tags that don't have one
const DEFAULT_TAG_COLOR = '#3B82F6';

interface Pagination {
  current_page: number;
  total_pages: number;
  total_items: number;
  per_page: number;
}

interface FilterState {
  startDate: string;
  endDate: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
  tags: Tag[];
}

const WindowsFolderIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 6C2 4.89543 2.89543 4 4 4H9L11 6H20C21.1046 6 22 6.89543 22 8V18C22 19.1046 21.1046 20 20 20H4C2.89543 20 2 19.1046 2 18V6Z" fill="#FFC107"/>
    <path d="M2 6C2 4.89543 2.89543 4 4 4H9L11 6H20C21.1046 6 22 6.89543 22 8V18C22 19.1046 21.1046 20 20 20H4C2.89543 20 2 19.1046 2 18V6Z" fill="url(#paint0_linear)"/>
    <defs>
      <linearGradient id="paint0_linear" x1="12" y1="4" x2="12" y2="20" gradientUnits="userSpaceOnUse">
        <stop stopColor="#FFE082"/>
        <stop offset="1" stopColor="#FFA000"/>
      </linearGradient>
    </defs>
  </svg>
);

const PdfIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M3 2C3 1.44772 3.44772 1 4 1H14L21 8V22C21 22.5523 20.5523 23 20 23H4C3.44772 23 3 22.5523 3 22V2Z" fill="#FF2116"/>
    <path d="M14 1L21 8H15C14.4477 8 14 7.55228 14 7V1Z" fill="#white"/>
    <path d="M6.60156 19V11.3789H8.9375C9.65625 11.3789 10.2266 11.5312 10.6484 11.8359C11.0703 12.1406 11.2812 12.5938 11.2812 13.1953C11.2812 13.5078 11.1953 13.7852 11.0234 14.0273C10.8516 14.2695 10.6094 14.4492 10.2969 14.5664C10.6562 14.6445 10.9375 14.8164 11.1406 15.082C11.3438 15.3477 11.4453 15.6719 11.4453 16.0547C11.4453 16.6953 11.2344 17.1836 10.8125 17.5195C10.3906 17.8555 9.79688 18.0234 9.03125 18.0234L6.60156 19ZM7.89844 14.4023H8.89844C9.27344 14.4023 9.55469 14.3242 9.74219 14.168C9.92969 14.0117 10.0234 13.7812 10.0234 13.4766C10.0234 13.1953 9.92188 12.9844 9.71875 12.8438C9.51562 12.7031 9.21094 12.6328 8.80469 12.6328H7.89844V14.4023ZM7.89844 15.6094V16.7695H9.03125C9.40625 16.7695 9.69141 16.6875 9.88672 16.5234C10.082 16.3594 10.1797 16.125 10.1797 15.8203C10.1797 15.5312 10.0859 15.3086 9.89844 15.1523C9.71094 14.9961 9.42969 14.918 9.05469 14.918H7.89844V15.6094Z" fill="white"/>
  </svg>
);

export default function DocumentsPage() {
  const [items, setItems] = useState<(Document | Folder)[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [computers, setComputers] = useState<Computer[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [downloading, setDownloading] = useState<string | null>(null);
  const [currentComputer, setCurrentComputer] = useState<string | null>(null);
  const [pagination, setPagination] = useState<Pagination | null>(null);
  const [previewFile, setPreviewFile] = useState<{ url: string; name: string } | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [filters, setFilters] = useState<FilterState>({
    startDate: '',
    endDate: '',
    sortBy: 'name',
    sortOrder: 'asc',
    tags: []
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedComputer, setSelectedComputer] = useState<Computer | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'created'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  const [showQAModal, setShowQAModal] = useState(false);
  const [currentQADoc, setCurrentQADoc] = useState<Document | null>(null);

  const { toast } = useToast();

  const { 
    selectedDocs, 
    toggleSelection, 
    selectAll, 
    clearSelection, 
    hasSelection 
  } = useDocumentSelection();

  const documentTags = useDocumentTags(currentComputer || '');

  const {
    tags,
    loading: tagsLoading,
    error: tagsError,
    fetchTags,
    addTag,
    removeTag
  } = documentTags;

  const handleItemClick = (item: Document | Folder) => {
    if (item.type === 'folder') {
      // Set the current computer and reset pagination
      setCurrentComputer(item.name);
      setCurrentPage(1);
    } else {
      // Handle document preview/download
      downloadDocument(item.path, item.name);
    }
  };

  useEffect(() => {
    const fetchComputers = async () => {
      try {
        console.log('Fetching computers...');
        // Get the computer list from the API (now filtered to only those with documents)
        const data = await getComputers('documents');
        console.log('Received computers:', data);
        setComputers(data);
        
        if (data.length === 0) {
          console.log('No computers found');
          setError('No computers with documents found');
          setItems([]);
          setLoading(false);
        } else {
          // Convert computers to folders
          console.log('Converting computers to folders...');
          const computerFolders: Folder[] = data.map((computer: Computer) => ({
            name: computer.name || computer.label, // Use name if available, fallback to label
            type: 'folder'
          }));
          console.log('Setting folders:', computerFolders);
          setItems(computerFolders);
          setLoading(false);
        }
      } catch (err) {
        console.error('Error fetching computers:', err);
        setError('Failed to fetch computers');
        setItems([]);
        setLoading(false);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to fetch computers",
        });
      }
    };

    if (!currentComputer) {
      setLoading(true);
      fetchComputers();
    }
  }, [currentComputer, toast]);

  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true);
      try {
        console.log('Fetching documents for computer:', currentComputer);
        const data = await getDocuments({
          computer: currentComputer,
          page: currentPage,
          per_page: 10,
          search: searchQuery,
          sort_by: sortBy,
          sort_order: sortOrder
        });
        
        // Map API response to match Document interface
        const mappedDocuments: Document[] = data.documents.map(doc => ({
          name: doc.name,
          path: doc.path,
          type: 'document',
          size: doc.size,
          created: doc.created,
          tags: doc.tags.map(tag => ({
            ...tag,
            color: tag.color || DEFAULT_TAG_COLOR
          }))
        }));
        
        setDocuments(mappedDocuments);
        setPagination(data.pagination);
        setItems(mappedDocuments); // Update items to show documents
      } catch (error) {
        console.error('Error fetching documents:', error);
        toast({
          title: "Error",
          description: "Failed to fetch documents. Please try again.",
          variant: "destructive"
        });
        setItems([]); // Clear items on error
      } finally {
        setLoading(false);
      }
    };

    if (currentComputer) {
      fetchDocuments();
    }
  }, [currentPage, currentComputer, searchQuery, sortBy, sortOrder, toast]);

  const handleSort = (field: 'name' | 'size' | 'created') => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const downloadDocument = async (path: string, filename: string) => {
    try {
      setDownloading(filename);
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
      link.download = filename;
      
      // Append to body, click, and remove
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // Clean up the URL
      window.URL.revokeObjectURL(downloadUrl);
    } catch (err) {
      console.error('Error downloading document:', err);
      toast({
        variant: "destructive",
        title: "Error",
        description: `Failed to download ${filename}`,
      });
    } finally {
      setDownloading(null);
    }
  };

  const handleBackClick = () => {
    setCurrentComputer(null);
    setSearchQuery('');
  };

  const handlePreview = async (doc: Document) => {
    try {
      // Don't add the base URL since fetchWithAuth will handle that
      const url = new URL('/api/documents/download/', 'http://placeholder.com');
      url.searchParams.set('path', doc.path);
      url.searchParams.set('preview', 'true');
      // Only use the pathname and search parts of the URL
      setPreviewFile({
        url: `${url.pathname}${url.search}`,
        name: doc.name
      });
    } catch (error) {
      console.error('Error getting document URL:', error);
      toast({
        title: "Error",
        description: "Failed to open document preview",
        variant: "destructive",
      });
    }
  };

  const handleBulkDownload = async () => {
    const selectedItems = items.filter(
      (item): item is Document => 
        item.type === 'document' && selectedDocs.has(item.path)
    );

    for (const doc of selectedItems) {
      await downloadDocument(doc.path, doc.name);
    }
    
    clearSelection();
    toast({
      title: "Success",
      description: `Downloaded ${selectedItems.length} documents`,
    });
  };

  const handleCreateTag = async (docPath: string) => {
    if (!newTagName.trim()) return;
    
    try {
      const newTag = await documentTags.createTag(newTagName, newTagColor);
      if (newTag) {
        await documentTags.addTag(docPath, newTag.id);
        setNewTagName('');
        setNewTagColor('#3B82F6');
      }
    } catch (error) {
      console.error('Failed to create tag:', error);
    }
  };

  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8 text-foreground">Document Folders</h1>
      
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <Input
            type="text"
            placeholder="Search folders..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-sm bg-background text-foreground border-border"
          />
        </div>

        <div className="rounded-md border border-border">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-muted/50">
                <TableHead className="w-[30px]">
                  <DocumentCheckbox
                    checked={selectedDocs.size === documents.length}
                    onCheckedChange={(checked: boolean) => {
                      if (checked) {
                        selectAll(documents);
                      } else {
                        clearSelection();
                      }
                    }}
                  />
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('name')}>
                  Name {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('size')}>
                  Size {sortBy === 'size' && (sortOrder === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead className="cursor-pointer" onClick={() => handleSort('created')}>
                  Created {sortBy === 'created' && (sortOrder === 'asc' ? '↑' : '↓')}
                </TableHead>
                <TableHead>Tags</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center">
                    <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                  </TableCell>
                </TableRow>
              ) : error ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-destructive">
                    {error}
                  </TableCell>
                </TableRow>
              ) : items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                    No documents found
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow
                    key={item.name}
                    className="hover:bg-muted/50 cursor-pointer"
                    onClick={() => handleItemClick(item)}
                  >
                    <TableCell>
                      {item.type === 'document' && (
                        <DocumentCheckbox
                          checked={selectedDocs.has(item.path)}
                          onCheckedChange={(checked: boolean) => {
                            if (checked) {
                              toggleSelection(item.path);
                            } else {
                              toggleSelection(item.path);
                            }
                          }}
                        />
                      )}
                    </TableCell>
                    <TableCell className="flex items-center gap-2">
                      {item.type === 'folder' ? (
                        <>
                          <WindowsFolderIcon />
                          <span className="text-foreground">{item.name}</span>
                        </>
                      ) : (
                        <>
                          <PdfIcon />
                          <span className="text-foreground">{item.name}</span>
                        </>
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {item.type === 'document' ? formatFileSize(item.size) : ''}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {item.type === 'document' ? new Date(item.created).toLocaleDateString() : ''}
                    </TableCell>
                    <TableCell>
                      {item.type === 'document' && (
                        <DocumentTags
                          path={item.path}
                          computer={currentComputer || ''}
                          initialTags={item.tags}
                          documentTags={documentTags}
                        />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.type === 'document' && (
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              handlePreview(item);
                            }}
                          >
                            <EyeIcon className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={(e) => {
                              e.stopPropagation();
                              downloadDocument(item.path, item.name);
                            }}
                          >
                            {downloading === item.path ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <DownloadIcon className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {hasSelection && <BulkActionBar selectedDocs={selectedDocs} onClearSelection={clearSelection} />}
      </div>

      {previewFile && (
        <PdfPreviewModal
          isOpen={!!previewFile}
          onClose={() => setPreviewFile(null)}
          pdfUrl={previewFile.url}
          fileName={previewFile.name}
        />
      )}
    </div>
  );
}
