"""Utilities for name handling and normalization."""
import re
import unicodedata

def normalize_name(name):
    """Normalize a name by handling special characters, spaces, and capitalization consistently."""
    if not name:
        return None
        
    # Convert to lowercase first for consistent processing
    name = name.strip().lower()
    
    # Replace multiple spaces with single space
    name = ' '.join(name.split())
    
    # Fix common patterns where single letters are split from names
    # e.g. "pizarr o" -> "pizarro", "sanche z" -> "sanchez"
    name = re.sub(r'([a-z]+)\s+([a-z])(?:\s|$)', r'\1\2', name)
    
    # Fix cases where two-letter prefixes are split
    # e.g. "ar agones" -> "aragones"
    name = re.sub(r'\b([a-z]{2})\s+([a-z]+)\b', r'\1\2', name)
    
    # Handle Spanish name prefixes consistently
    name = re.sub(r'\b(de)\s*l?\s*(os|as?)\b', r'de \2', name)
    name = re.sub(r'\b(de)\s*la\b', r'de la', name)
    
    # Handle Mc/Mac variations consistently
    name = re.sub(r'\b(mc|mac)\s*([a-z]+)\b', r'\1\2', name)
    
    # Split into words and capitalize each one
    name = ' '.join(part.capitalize() for part in name.split())
    
    # Replace spaces with underscores for filename
    name = name.replace(' ', '_')
    
    # Remove any remaining special characters
    name = re.sub(r'[^a-zA-Z0-9_]', '', name)
    
    return name if name else "Unknown_Name"
