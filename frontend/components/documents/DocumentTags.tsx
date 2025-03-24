'use client';

import { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Plus, X } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { type Tag } from '@/app/utils/api';

interface DocumentTagsProps {
  path: string;
  computer: string;
  initialTags?: Tag[];
  documentTags: {
    tags: Tag[];
    loading: boolean;
    error: string | null;
    getDocumentTags: (path: string) => Promise<any>;
    addTag: (docPath: string, tagId: number) => Promise<boolean>;
    removeTag: (docPath: string, tagId: number) => Promise<boolean>;
    createTag: (name: string, color: string) => Promise<any>;
  };
}

export function DocumentTags({ path, computer, initialTags = [], documentTags }: DocumentTagsProps) {
  const [tags, setTags] = useState<Tag[]>(initialTags);
  const [isAddingTag, setIsAddingTag] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#3B82F6');
  const [loading, setLoading] = useState(false);

  const handleAddTag = async (tagId: number) => {
    setLoading(true);
    try {
      const success = await documentTags.addTag(path, tagId);
      if (success) {
        const updatedTags = await documentTags.getDocumentTags(path);
        setTags(updatedTags);
      }
    } finally {
      setLoading(false);
      setIsAddingTag(false);
    }
  };

  const handleRemoveTag = async (tagId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setLoading(true);
    try {
      const success = await documentTags.removeTag(path, tagId);
      if (success) {
        setTags(tags.filter(tag => tag.id !== tagId));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTag = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!newTagName.trim()) return;
    
    setLoading(true);
    try {
      const newTag = await documentTags.createTag(newTagName, newTagColor);
      if (newTag) {
        await handleAddTag(newTag.id);
        setNewTagName('');
        setNewTagColor('#3B82F6');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-wrap gap-2 items-center min-h-[32px]" onClick={(e) => e.stopPropagation()}>
      {tags.map((tag) => (
        <Badge
          key={tag.id}
          style={{ 
            backgroundColor: tag.color,
            color: 'white',  
            textShadow: '0 1px 1px rgba(0,0,0,0.2)'  
          }}
          className="flex items-center gap-1 cursor-default hover:opacity-90 text-xs"
          variant="secondary"
          onClick={(e) => e.stopPropagation()}
        >
          {tag.name}
          <X
            className="h-3 w-3 hover:text-red-200 cursor-pointer transition-colors"
            onClick={(e) => handleRemoveTag(tag.id, e)}
          />
        </Badge>
      ))}
    </div>
  );
}
