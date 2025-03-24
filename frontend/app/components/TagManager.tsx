'use client';

import { useState, useEffect } from 'react';
import { PlusIcon, XIcon } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getTags, createTag, addTagToDocument, removeTagFromDocument } from '@/app/utils/api';

interface Tag {
  id: number;
  name: string;
  color: string;
}

interface TagManagerProps {
  documentPath?: string;
  computer?: string;
  selectedTags: Tag[];
  onTagsChange: (tags: Tag[]) => void;
}

export function TagManager({ documentPath, computer, selectedTags, onTagsChange }: TagManagerProps) {
  const [tags, setTags] = useState<Tag[]>([]);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all available tags
  const fetchTags = async () => {
    try {
      setError(null);
      const data = await getTags();
      setTags(data);
    } catch (error) {
      console.error('Error fetching tags:', error);
      setError('Failed to load tags');
    }
  };

  // Create a new tag
  const handleCreateTag = async () => {
    if (!newTagName.trim()) return;
    
    try {
      setLoading(true);
      setError(null);
      const newTag = await createTag(newTagName, newTagColor);
      setTags([...tags, newTag]);
      setNewTagName('');
    } catch (error) {
      console.error('Error creating tag:', error);
      setError('Failed to create tag');
    } finally {
      setLoading(false);
    }
  };

  // Add a tag to the current document
  const handleAddTagToDocument = async (tag: Tag) => {
    if (!documentPath || !computer) return;
    
    try {
      setLoading(true);
      setError(null);
      await addTagToDocument(tag.id, documentPath, computer);
      onTagsChange([...selectedTags, tag]);
    } catch (error) {
      console.error('Error adding tag to document:', error);
      setError('Failed to add tag to document');
    } finally {
      setLoading(false);
    }
  };

  // Remove a tag from the current document
  const handleRemoveTagFromDocument = async (tag: Tag) => {
    if (!documentPath || !computer) return;
    
    try {
      setLoading(true);
      setError(null);
      await removeTagFromDocument(tag.id, documentPath, computer);
      onTagsChange(selectedTags.filter(t => t.id !== tag.id));
    } catch (error) {
      console.error('Error removing tag from document:', error);
      setError('Failed to remove tag from document');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}
      
      <div className="flex items-end gap-4">
        <div className="flex-1">
          <Label htmlFor="tagName">Tag Name</Label>
          <Input
            id="tagName"
            value={newTagName}
            onChange={(e) => setNewTagName(e.target.value)}
            placeholder="Enter tag name"
            disabled={loading}
          />
        </div>
        <div>
          <Label htmlFor="tagColor">Color</Label>
          <Input
            id="tagColor"
            type="color"
            value={newTagColor}
            onChange={(e) => setNewTagColor(e.target.value)}
            className="w-20 h-10"
            disabled={loading}
          />
        </div>
        <Button
          onClick={handleCreateTag}
          disabled={!newTagName.trim() || loading}
          className="mb-0.5"
        >
          <PlusIcon className="w-4 h-4 mr-1" />
          Add
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => {
          const isSelected = selectedTags.some(t => t.id === tag.id);
          return (
            <Badge
              key={tag.id}
              style={{ backgroundColor: tag.color }}
              className={`cursor-pointer ${isSelected ? 'opacity-50' : ''}`}
              onClick={() => {
                if (isSelected) {
                  handleRemoveTagFromDocument(tag);
                } else {
                  handleAddTagToDocument(tag);
                }
              }}
            >
              {tag.name}
            </Badge>
          );
        })}
      </div>
    </div>
  );
}
