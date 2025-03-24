import { useState, useCallback } from 'react';
import { fetchWithAuth } from '@/app/utils/api';
import type { Tag as ApiTag } from '@/app/utils/api';

export interface Tag extends ApiTag {}

export function useDocumentTags(computer: string) {
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTags = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetchWithAuth('/api/documents/tags/');
      if (!response.ok) throw new Error('Failed to fetch tags');
      const data = await response.json();
      setTags(data.tags);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tags');
    } finally {
      setLoading(false);
    }
  }, []);

  const getDocumentTags = useCallback(async (path: string) => {
    try {
      const response = await fetchWithAuth(`/api/documents/tags/document_tags/?path=${encodeURIComponent(path)}&computer=${encodeURIComponent(computer)}`);
      if (!response.ok) throw new Error('Failed to fetch document tags');
      const data = await response.json();
      return data.tags;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch document tags');
      return [];
    }
  }, [computer]);

  const addTag = useCallback(async (docPath: string, tagId: number) => {
    try {
      const response = await fetchWithAuth('/api/documents/tags/add/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          path: docPath, 
          tag_id: tagId,
          computer: computer 
        }),
      });
      if (!response.ok) throw new Error('Failed to add tag');
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add tag');
      return false;
    }
  }, [computer]);

  const removeTag = useCallback(async (docPath: string, tagId: number) => {
    try {
      const response = await fetchWithAuth('/api/documents/tags/remove/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          path: docPath, 
          tag_id: tagId,
          computer: computer 
        }),
      });
      if (!response.ok) throw new Error('Failed to remove tag');
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove tag');
      return false;
    }
  }, [computer]);

  const createTag = useCallback(async (name: string, color: string) => {
    try {
      const response = await fetchWithAuth('/api/documents/tags/create_tag/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, color }),
      });
      if (!response.ok) throw new Error('Failed to create tag');
      const newTag = await response.json();
      setTags(prev => [...prev, newTag]);
      return newTag;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create tag');
      return null;
    }
  }, []);

  return {
    tags,
    loading,
    error,
    fetchTags,
    getDocumentTags,
    addTag,
    removeTag,
    createTag,
  };
}
