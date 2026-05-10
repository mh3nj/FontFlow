"""
FontFlow Studio - Safe Duplicate Detector
NEVER auto-deletes - only suggests with evidence
"""

from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
import hashlib
from itertools import combinations

from models.font_family import FontFamily, FontStyle


@dataclass
class DuplicateEvidence:
    """Evidence that two fonts might be duplicates"""
    font_a_name: str
    font_b_name: str
    file_sizes_match: bool
    same_family_name: bool
    same_weight: bool
    same_italic: bool
    glyph_count_similar: bool
    hash_match: bool
    confidence: float
    
    def __str__(self):
        return f"Confidence: {self.confidence:.1%} - {self.font_a_name} ≈ {self.font_b_name}"
    
    def get_evidence_list(self) -> List[str]:
        """Get human-readable evidence list"""
        evidence = []
        if self.file_sizes_match:
            evidence.append("📁 File sizes are identical")
        if self.same_family_name:
            evidence.append("🏷️ Same family name in metadata")
        if self.same_weight:
            evidence.append("⚖️ Same weight (e.g., both Bold)")
        if self.same_italic:
            evidence.append("📎 Both have same italic style")
        if self.glyph_count_similar:
            evidence.append("🔤 Similar glyph count")
        if self.hash_match:
            evidence.append("🔒 Exact file hash match (99.9% duplicate)")
        return evidence


@dataclass
class DuplicateGroup:
    """Group of fonts that might be duplicates"""
    group_id: int
    fonts: List[FontStyle]
    confidence: float
    evidence: List[str]
    requires_review: bool = True
    
    @property
    def can_auto_resolve(self) -> bool:
        """Only auto-resolve if confidence > 99.5% AND user enables auto-mode"""
        return self.confidence > 0.995


class SafeDuplicateDetector:
    """
    Safe duplicate detection - never deletes without user confirmation.
    
    Features:
    - Multiple confidence levels
    - Shows evidence for each decision
    - Batch review interface
    - Preserves creative work
    """
    
    # Confidence thresholds
    CONFIDENCE_EXACT = 0.995  # Identical files (99.5%+)
    CONFIDENCE_HIGH = 0.95     # Very likely duplicate
    CONFIDENCE_MEDIUM = 0.85   # Possible duplicate
    CONFIDENCE_LOW = 0.70      # Suspicious
    
    def __init__(self, library_path: Path):
        self.library_path = Path(library_path)
        self.font_hashes: Dict[Path, str] = {}
    
    def detect_duplicates(self, families: List[FontFamily], 
                         auto_mode: bool = False) -> List[DuplicateGroup]:
        """
        Find potential duplicates across all families.
        
        Args:
            families: List of font families to check
            auto_mode: If True, auto-resolve exact duplicates (99.5%+)
            
        Returns:
            List of duplicate groups for user review
        """
        print(f"🔍 Scanning for duplicates across {len(families)} families...")
        
        # Step 1: Collect all font files
        all_fonts = []
        for family in families:
            for style in family.styles:
                all_fonts.append((family, style))
        
        print(f"   Checking {len(all_fonts)} font files...")
        
        # Step 2: Pre-calculate hashes for exact matching
        self._precompute_hashes([style for _, style in all_fonts])
        
        # Step 3: Find duplicate pairs
        duplicate_pairs = []
        checked_pairs = set()
        
        for i, (family_a, font_a) in enumerate(all_fonts):
            for j, (family_b, font_b) in enumerate(all_fonts[i+1:], i+1):
                pair_key = tuple(sorted([str(font_a.path), str(font_b.path)]))
                if pair_key in checked_pairs:
                    continue
                checked_pairs.add(pair_key)
                
                evidence = self._compare_fonts(font_a, font_b, family_a, family_b)
                
                if evidence.confidence >= self.CONFIDENCE_LOW:
                    duplicate_pairs.append(evidence)
                    print(f"   Found: {evidence}")
        
        # Step 4: Group pairs into duplicate groups
        groups = self._group_duplicates(duplicate_pairs)
        
        # Step 5: Filter and sort
        if not auto_mode:
            # In manual mode, show all potential duplicates
            groups = [g for g in groups if g.confidence >= self.CONFIDENCE_MEDIUM]
        else:
            # In auto mode, auto-resolve exact duplicates
            auto_resolved = []
            for group in groups:
                if group.can_auto_resolve:
                    auto_resolved.append(group)
                    print(f"🤖 Auto-resolved: {group.fonts[0].path.name}")
            
            # Return only groups that need review
            groups = [g for g in groups if not g.can_auto_resolve]
        
        print(f"\n📊 Duplicate detection complete:")
        print(f"   Total groups found: {len(groups)}")
        print(f"   Need review: {len(groups)}")
        
        if auto_mode:
            print(f"   Auto-resolved: {len(auto_resolved)}")
        
        return groups
    
    def _precompute_hashes(self, fonts: List[FontStyle]):
        """Precompute file hashes for exact matching"""
        for font in fonts:
            try:
                with open(font.path, 'rb') as f:
                    # Read first 64KB and last 64KB (fast approximate hash)
                    f.seek(0)
                    data = f.read(65536)
                    f.seek(-65536, 2)
                    data += f.read(65536)
                    self.font_hashes[font.path] = hashlib.md5(data).hexdigest()
            except Exception as e:
                print(f"Warning: Could not hash {font.path.name}: {e}")
                self.font_hashes[font.path] = ""
    
    def _compare_fonts(self, font_a: FontStyle, font_b: FontStyle,
                      family_a: FontFamily, family_b: FontFamily) -> DuplicateEvidence:
        """Compare two fonts and return evidence"""
        
        # File size match
        size_match = abs(font_a.path.stat().st_size - font_b.path.stat().st_size) < 1024
        
        # Hash match (exact file content)
        hash_a = self.font_hashes.get(font_a.path, "")
        hash_b = self.font_hashes.get(font_b.path, "")
        hash_match = hash_a == hash_b and hash_a != ""
        
        # Family name match (with normalization)
        same_family = family_a.family_name.lower() == family_b.family_name.lower()
        
        # Weight match
        same_weight = font_a.weight == font_b.weight
        
        # Italic match
        same_italic = font_a.is_italic == font_b.is_italic
        
        # Glyph count similarity (within 10%)
        glyph_diff = abs(font_a.glyph_count - font_b.glyph_count)
        glyph_similar = glyph_diff / max(font_a.glyph_count, font_b.glyph_count) < 0.1
        
        # Calculate confidence
        confidence = 0.0
        weights = {
            'hash_match': 0.50,      # 50% weight for exact hash match
            'same_family': 0.20,      # 20% for same family name
            'same_weight': 0.10,      # 10% for same weight
            'same_italic': 0.10,      # 10% for same italic
            'glyph_similar': 0.05,    # 5% for similar glyph count
            'size_match': 0.05,       # 5% for similar file size
        }
        
        confidence += weights['hash_match'] * (1.0 if hash_match else 0)
        confidence += weights['same_family'] * (1.0 if same_family else 0)
        confidence += weights['same_weight'] * (1.0 if same_weight else 0)
        confidence += weights['same_italic'] * (1.0 if same_italic else 0)
        confidence += weights['glyph_similar'] * (1.0 if glyph_similar else 0)
        confidence += weights['size_match'] * (1.0 if size_match else 0)
        
        return DuplicateEvidence(
            font_a_name=font_a.path.name,
            font_b_name=font_b.path.name,
            file_sizes_match=size_match,
            same_family_name=same_family,
            same_weight=same_weight,
            same_italic=same_italic,
            glyph_count_similar=glyph_similar,
            hash_match=hash_match,
            confidence=confidence
        )
    
    def _group_duplicates(self, pairs: List[DuplicateEvidence]) -> List[DuplicateGroup]:
        """Group duplicate pairs into connected components"""
        # Build graph
        graph = defaultdict(set)
        for evidence in pairs:
            graph[evidence.font_a_name].add(evidence.font_b_name)
            graph[evidence.font_b_name].add(evidence.font_a_name)
        
        # Find connected components
        visited = set()
        groups = []
        
        for font_name in graph:
            if font_name not in visited:
                # BFS to find component
                component = []
                queue = [font_name]
                visited.add(font_name)
                
                while queue:
                    current = queue.pop(0)
                    component.append(current)
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                
                # Calculate group confidence (average of pairwise confidences)
                if len(component) > 1:
                    # Find relevant evidence for this group
                    group_evidence = []
                    for evidence in pairs:
                        if evidence.font_a_name in component and evidence.font_b_name in component:
                            group_evidence.append(evidence)
                    
                    avg_confidence = sum(e.confidence for e in group_evidence) / len(group_evidence) if group_evidence else 0.5
                    
                    # Collect all evidence messages
                    evidence_list = []
                    for e in group_evidence[:3]:  # Limit to first 3 pieces of evidence
                        evidence_list.extend(e.get_evidence_list())
                    evidence_list = list(set(evidence_list))  # Remove duplicates
                    
                    groups.append(DuplicateGroup(
                        group_id=len(groups),
                        fonts=[],  # Will populate with actual FontStyle objects later
                        confidence=avg_confidence,
                        evidence=evidence_list[:5]  # Limit to 5 pieces of evidence
                    ))
        
        return groups


class DuplicateReviewUI:
    """UI for reviewing and resolving duplicates"""
    
    def __init__(self, duplicate_groups: List[DuplicateGroup]):
        self.groups = duplicate_groups
        self.resolved = []
    
    def show_review_dialog(self):
        """Show interactive dialog for duplicate review"""
        print("\n" + "="*60)
        print("⚠️  DUPLICATE FONT DETECTION")
        print("="*60)
        print(f"\nFound {len(self.groups)} potential duplicate groups to review.\n")
        
        for i, group in enumerate(self.groups):
            print(f"\n📦 Group {i+1}/{len(self.groups)}")
            print(f"   Confidence: {group.confidence:.1%}")
            print(f"   Evidence:")
            for evidence in group.evidence:
                print(f"     • {evidence}")
            
            # In real UI, this would show side-by-side preview
            print(f"\n   Actions:")
            print(f"     [1] Keep both (not duplicates)")
            print(f"     [2] Keep first, delete second")
            print(f"     [3] Keep second, delete first")
            print(f"     [4] Move to review later folder")
            print(f"     [S] Skip for now")
        
        print("\n" + "="*60)
