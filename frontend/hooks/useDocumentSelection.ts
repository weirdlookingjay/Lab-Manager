import { useState, useCallback } from 'react';

export interface DocumentItem {
  path: string;
  name: string;
  size: number;
}

export function useDocumentSelection() {
  const [selectedDocs, setSelectedDocs] = useState<Set<string>>(new Set());

  const toggleSelection = useCallback((docPath: string) => {
    setSelectedDocs(prev => {
      const newSelection = new Set(prev);
      if (newSelection.has(docPath)) {
        newSelection.delete(docPath);
      } else {
        newSelection.add(docPath);
      }
      return newSelection;
    });
  }, []);

  const selectAll = useCallback((docs: DocumentItem[]) => {
    setSelectedDocs(new Set(docs.map(doc => doc.path)));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedDocs(new Set());
  }, []);

  return {
    selectedDocs,
    toggleSelection,
    selectAll,
    clearSelection,
    hasSelection: selectedDocs.size > 0
  };
}
