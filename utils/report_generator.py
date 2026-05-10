"""
FontFlow Studio - Report Generator
Generates HTML and PDF reports of classified fonts
"""

from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import html

from models.font_family import FontFamily


class ReportGenerator:
    """
    Generates professional reports from font classification data.
    """
    
    def __init__(self, library_path: Path, families: List[FontFamily], session_data: dict):
        self.library_path = library_path
        self.families = families
        self.session_data = session_data
        self.classified_families = []
        self.uncertain_families = []
        self.unclassified_families = []
        self._categorize_families()
    
    def _categorize_families(self):
        """Categorize families by classification status"""
        for family in self.families:
            if hasattr(family, 'classified') and family.classified:
                self.classified_families.append(family)
            elif hasattr(family, 'classified_uncertain') and family.classified_uncertain:
                self.uncertain_families.append(family)
            else:
                self.unclassified_families.append(family)
    
    def generate_html_report(self, output_path: Path) -> str:
        """
        Generate an HTML report.
        
        Args:
            output_path: Where to save the HTML file
            
        Returns:
            Path to generated file as string
        """
        html_content = self._build_html()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return str(output_path)
    
    def _build_html(self) -> str:
        """Build the complete HTML report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Calculate statistics
        total = len(self.families)
        classified = len(self.classified_families)
        uncertain = len(self.uncertain_families)
        unclassified = total - classified - uncertain
        percent_complete = (classified / total * 100) if total > 0 else 0
        
        # Group classified families by category (from source folder)
        categories = self._group_by_category()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FontFlow Studio - Classification Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #0a1628;
            color: #e0e0e0;
            padding: 40px;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #0d1b2a;
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        }}
        
        .header {{
            background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 48px;
            font-weight: bold;
            color: #0a1628;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 18px;
            color: #0a1628;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #1b263b;
        }}
        
        .stat-card {{
            background: #0d1b2a;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid #2d3e5f;
        }}
        
        .stat-number {{
            font-size: 48px;
            font-weight: bold;
            color: #00ff88;
        }}
        
        .stat-label {{
            font-size: 14px;
            color: #8892b0;
            margin-top: 8px;
        }}
        
        .progress-bar {{
            background: #2d3e5f;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin: 20px 0;
        }}
        
        .progress-fill {{
            background: linear-gradient(90deg, #00ff88, #00cc6a);
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
            width: {percent_complete:.1f}%;
        }}
        
        .section {{
            padding: 30px 40px;
            border-bottom: 1px solid #2d3e5f;
        }}
        
        .section h2 {{
            font-size: 28px;
            color: #00ff88;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .category-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .category-card {{
            background: #0d1b2a;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid #2d3e5f;
        }}
        
        .category-header {{
            background: #1b263b;
            padding: 15px 20px;
            font-weight: bold;
            font-size: 18px;
            color: #00ff88;
            border-bottom: 1px solid #2d3e5f;
        }}
        
        .font-list {{
            padding: 15px 20px;
        }}
        
        .font-item {{
            padding: 10px 0;
            border-bottom: 1px solid #2d3e5f;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .font-item:last-child {{
            border-bottom: none;
        }}
        
        .font-name {{
            font-weight: 500;
        }}
        
        .font-details {{
            font-size: 12px;
            color: #8892b0;
        }}
        
        .badge {{
            background: #00ff88;
            color: #0a1628;
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
        }}
        
        .badge-uncertain {{
            background: #ffd93d;
            color: #0a1628;
        }}
        
        .footer {{
            padding: 30px 40px;
            text-align: center;
            color: #495670;
            font-size: 12px;
            background: #0a1628;
        }}
        
        @media (max-width: 768px) {{
            body {{
                padding: 20px;
            }}
            .stats {{
                grid-template-columns: 1fr;
            }}
            .category-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 FontFlow Studio</h1>
            <p>Professional Font Classification Report</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total}</div>
                <div class="stat-label">Total Families</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #00ff88">{classified}</div>
                <div class="stat-label">Classified ✓</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #ffd93d">{uncertain}</div>
                <div class="stat-label">Uncertain ⚠</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" style="color: #8892b0">{unclassified}</div>
                <div class="stat-label">Unclassified ○</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Overall Progress</h2>
            <div class="progress-bar">
                <div class="progress-fill"></div>
            </div>
            <p style="text-align: center; margin-top: 10px;">{percent_complete:.1f}% Complete</p>
        </div>
        
        <div class="section">
            <h2>📁 Classified Fonts by Category</h2>
            <div class="category-grid">
                {self._build_category_html(categories)}
            </div>
        </div>
        
        {self._build_uncertain_section() if uncertain > 0 else ''}
        
        <div class="footer">
            <p>Generated by FontFlow Studio</p>
            <p>{timestamp}</p>
            <p>Library: {self.library_path}</p>
        </div>
    </div>
</body>
</html>"""
    
    def _group_by_category(self) -> Dict[str, List[FontFamily]]:
        """Group classified families by their category folder"""
        categories = {}
        
        for family in self.classified_families:
            # Get category from family's source folder structure
            try:
                # Look for category folder name in path
                parts = family.source_folder.parts
                for part in parts:
                    if part.startswith(('01_', '02_', '03_', '04_', '05_', '06_', '07_', '08_', '09_', '10_')):
                        category_name = part.split('_', 1)[-1] if '_' in part else part
                        categories.setdefault(category_name, []).append(family)
                        break
                else:
                    categories.setdefault("Other", []).append(family)
            except:
                categories.setdefault("Other", []).append(family)
        
        return categories
    
    def _build_category_html(self, categories: Dict[str, List[FontFamily]]) -> str:
        """Build HTML for category grid"""
        if not categories:
            return '<p style="color: #8892b0;">No classified fonts yet.</p>'
        
        html_parts = []
        for category_name, families in sorted(categories.items()):
            # Sort families by name
            families_sorted = sorted(families, key=lambda f: f.family_name.lower())
            
            fonts_html = []
            for family in families_sorted[:20]:  # Limit to 20 per category
                fonts_html.append(f'''
                    <div class="font-item">
                        <div>
                            <div class="font-name">{html.escape(family.family_name)}</div>
                            <div class="font-details">{family.style_count} styles · {family.weight_range_name}</div>
                        </div>
                        <span class="badge">✓</span>
                    </div>
                ''')
            
            if len(families_sorted) > 20:
                fonts_html.append(f'<div class="font-item"><div class="font-details">... and {len(families_sorted) - 20} more</div></div>')
            
            html_parts.append(f'''
                <div class="category-card">
                    <div class="category-header">📁 {html.escape(category_name)} ({len(families_sorted)})</div>
                    <div class="font-list">
                        {''.join(fonts_html)}
                    </div>
                </div>
            ''')
        
        return ''.join(html_parts)
    
    def _build_uncertain_section(self) -> str:
        """Build HTML for uncertain fonts section"""
        if not self.uncertain_families:
            return ''
        
        fonts_html = []
        for family in sorted(self.uncertain_families, key=lambda f: f.family_name.lower()):
            fonts_html.append(f'''
                <div class="font-item">
                    <div>
                        <div class="font-name">{html.escape(family.family_name)}</div>
                        <div class="font-details">{family.style_count} styles · {family.weight_range_name}</div>
                    </div>
                    <span class="badge badge-uncertain">⚠</span>
                </div>
            ''')
        
        return f'''
        <div class="section">
            <h2>⚠ Fonts Needing Review</h2>
            <div class="category-grid">
                <div class="category-card">
                    <div class="category-header">Uncertain / Review Later ({len(self.uncertain_families)})</div>
                    <div class="font-list">
                        {''.join(fonts_html)}
                    </div>
                </div>
            </div>
        </div>
        '''
