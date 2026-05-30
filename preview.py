#!/usr/bin/env python3
import os
import re
import sys
import webbrowser
import json

import tempfile

DIR_PATH = "/home/anwar/projects/plymouth-themes"
README_PATH = os.path.join(DIR_PATH, "README.md")
TEMP_HTML_PATH = os.path.join(tempfile.gettempdir(), "plymouth_preview.html")
EXPORT_HTML_PATH = os.path.join(DIR_PATH, "index.html")

def scan_folders():
    """Scans pack subdirectories to mapping folder names to their packs."""
    folders = {}
    for i in range(1, 5):
        pack_name = f"pack_{i}"
        pack_dir = os.path.join(DIR_PATH, pack_name)
        if os.path.isdir(pack_dir):
            for d in os.listdir(pack_dir):
                if os.path.isdir(os.path.join(pack_dir, d)):
                    folders[d] = pack_name
    return folders

def get_normalized_mapping(theme_name, folders):
    """Fuzzy maps theme names from README to folder names in the repository."""
    normalized = theme_name.lower().replace(" ", "_").replace("-", "_")
    
    # Exact match
    if normalized in folders:
        return normalized, folders[normalized]
        
    # Singular match (e.g. abstract_rings -> abstract_ring)
    if normalized.endswith("s") and normalized[:-1] in folders:
        return normalized[:-1], folders[normalized[:-1]]
        
    # Special cases
    if normalized == "glow":
        return "glowing", folders.get("glowing")
        
    # Substring match
    for f, p in folders.items():
        if normalized in f or f in normalized:
            return f, p
            
    return None, None

def get_local_frames(pack_dir, folder):
    """Finds all progress-*.png files in the theme folder and returns sorted frame indices."""
    theme_path = os.path.join(DIR_PATH, pack_dir, folder)
    if not os.path.isdir(theme_path):
        return []
    
    frames = []
    for f in os.listdir(theme_path):
        match = re.match(r'progress-(\d+)\.png', f)
        if match:
            frames.append(int(match.group(1)))
            
    if not frames:
        return []
        
    frames.sort()
    return frames

def parse_themes():
    if not os.path.exists(README_PATH):
        print(f"Error: README.md not found at {README_PATH}")
        sys.exit(1)
        
    folders = scan_folders()
    themes = []
    
    # Read the file
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Find packs by parsing markdown details sections
    pack_blocks = re.split(r'<!-----------------------------\s*(Pack\s+\d+)\s*----------------------------->', content)
    
    for idx in range(1, len(pack_blocks), 2):
        pack_name = pack_blocks[idx]
        block_content = pack_blocks[idx+1]
        
        # Extract themes in this block: + [Theme Name](url)
        theme_matches = re.findall(r'\+\s+\[([^\]]+)\]\((https?://[^\)]+)\)', block_content)
        for name, url in theme_matches:
            name = name.strip()
            url = url.strip()
            folder_name, pack_dir = get_normalized_mapping(name, folders)
            
            # Find local frames if available
            local_frames = []
            if folder_name and pack_dir:
                local_frames = get_local_frames(pack_dir, folder_name)
                
            themes.append({
                "name": name,
                "url": url,
                "pack": pack_name,
                "folder": folder_name or name.lower().replace(" ", "_"),
                "pack_dir": pack_dir or "pack_1",
                "frames": local_frames
            })
            
    return themes

def generate_html(themes, filepath):
    themes_json = json.dumps(themes, indent=2)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Plymouth Themes - Interactive Preview Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0d16;
            --sidebar-bg: #111422;
            --card-bg: rgba(20, 24, 38, 0.6);
            --border-color: rgba(255, 255, 255, 0.06);
            --primary: #6366f1;
            --primary-glow: rgba(99, 102, 241, 0.2);
            --accent: #a855f7;
            --text-color: #f1f5f9;
            --text-muted: #64748b;
            --sidebar-width: 320px;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Outfit', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            height: 100vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        /* Header */
        header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 2rem;
            background-color: var(--sidebar-bg);
            border-bottom: 1px solid var(--border-color);
            z-index: 10;
        }}

        .logo-area {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .logo-icon {{
            width: 36px;
            height: 36px;
            background: linear-gradient(135deg, var(--primary), var(--accent));
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            box-shadow: 0 0 15px var(--primary-glow);
        }}

        h1 {{
            font-size: 1.25rem;
            font-weight: 600;
            background: linear-gradient(to right, #ffffff, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .controls {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .search-bar {{
            position: relative;
        }}

        .search-bar input {{
            background-color: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 0.5rem 1rem 0.5rem 2.2rem;
            color: white;
            font-family: inherit;
            width: 260px;
            transition: all 0.3s ease;
        }}

        .search-bar input:focus {{
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
            background-color: rgba(255, 255, 255, 0.06);
        }}

        .search-icon {{
            position: absolute;
            left: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-muted);
            pointer-events: none;
            width: 14px;
            height: 14px;
        }}

        .btn-group {{
            display: flex;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 3px;
        }}

        .btn {{
            background: transparent;
            border: none;
            color: var(--text-muted);
            padding: 0.4rem 1rem;
            border-radius: 6px;
            cursor: pointer;
            font-family: inherit;
            font-weight: 500;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s ease;
        }}

        .btn:hover {{
            color: white;
        }}

        .btn.active {{
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.2);
        }}

        /* Layout Container */
        .main-container {{
            display: flex;
            flex: 1;
            overflow: hidden;
            position: relative;
        }}

        /* Sidebar Scrollable List */
        .sidebar {{
            width: var(--sidebar-width);
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}

        .pack-section {{
            padding: 0.75rem 0.5rem;
        }}

        .pack-header {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
            font-weight: 600;
            padding-left: 0.75rem;
        }}

        .theme-list {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }}

        .theme-item {{
            padding: 0.6rem 0.75rem;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            justify-content: space-between;
            color: #cbd5e1;
            font-size: 0.9rem;
            border: 1px solid transparent;
        }}

        .theme-item:hover {{
            background-color: rgba(255, 255, 255, 0.03);
            color: white;
        }}

        .theme-item.active {{
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.3);
            color: #818cf8;
            font-weight: 500;
        }}

        .theme-index {{
            font-size: 0.7rem;
            color: var(--text-muted);
            background-color: rgba(255, 255, 255, 0.05);
            padding: 2px 6px;
            border-radius: 4px;
        }}

        /* Details Pane */
        .content-area {{
            flex: 1;
            overflow-y: auto;
            padding: 2.5rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            background: radial-gradient(circle at 50% 30%, rgba(99, 102, 241, 0.02), transparent 60%);
        }}

        .detail-view {{
            max-width: 960px;
            width: 100%;
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 3rem;
            align-items: start;
        }}

        .preview-box {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            aspect-ratio: 4/3;
            position: relative;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
        }}

        .preview-box img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            border-radius: 8px;
            z-index: 2;
        }}

        .preview-box::before {{
            content: '';
            position: absolute;
            width: 150px;
            height: 150px;
            background: var(--primary);
            filter: blur(80px);
            opacity: 0.15;
            border-radius: 50%;
            z-index: 1;
        }}

        .details-box {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}

        .theme-title {{
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            background: linear-gradient(to right, white, #cbd5e1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .theme-meta {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}

        .meta-tag {{
            background-color: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            color: #94a3b8;
            font-weight: 500;
        }}

        .meta-tag.accent {{
            border-color: rgba(168, 85, 247, 0.3);
            color: #c084fc;
            background-color: rgba(168, 85, 247, 0.05);
        }}

        .install-guide {{
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }}

        .tabs-header {{
            display: flex;
            background: rgba(0, 0, 0, 0.15);
            border-bottom: 1px solid var(--border-color);
        }}

        .tab-btn {{
            flex: 1;
            padding: 0.75rem 1rem;
            background: none;
            border: none;
            color: var(--text-muted);
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.8rem;
            border-bottom: 2px solid transparent;
        }}

        .tab-btn:hover {{
            color: white;
            background: rgba(255,255,255,0.01);
        }}

        .tab-btn.active {{
            color: var(--primary);
            border-bottom-color: var(--primary);
            background: rgba(99, 102, 241, 0.05);
        }}

        .tab-content {{
            padding: 1.25rem;
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .step-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-bottom: 6px;
            font-weight: 500;
        }}

        .code-container {{
            position: relative;
            background: #06070a;
            padding: 0.75rem 3rem 0.75rem 1rem;
            border-radius: 8px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.8rem;
            color: #a5b4fc;
            word-break: break-all;
            white-space: pre-wrap;
            border: 1px solid rgba(255, 255, 255, 0.03);
            margin-bottom: 1rem;
        }}

        .code-container:last-child {{
            margin-bottom: 0;
        }}

        .copy-btn {{
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid var(--border-color);
            color: var(--text-muted);
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.7rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }}

        .copy-btn:hover {{
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border-color: var(--text-muted);
        }}

        .keyboard-hint {{
            margin-top: 2rem;
            font-size: 0.75rem;
            color: var(--text-muted);
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        kbd {{
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-color);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: inherit;
            font-size: 0.7rem;
            color: #cbd5e1;
        }}

        /* Grid View Mode */
        .grid-view {{
            display: none;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1.5rem;
            width: 100%;
            max-width: 1200px;
            padding: 1rem 0;
        }}

        .grid-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 12px;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
        }}

        .grid-card:hover {{
            transform: translateY(-4px);
            border-color: var(--primary);
            box-shadow: 0 12px 25px var(--primary-glow);
        }}

        .grid-card-img {{
            width: 100%;
            aspect-ratio: 4/3;
            background: rgba(0, 0, 0, 0.25);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
        }}

        .grid-card-img img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        .grid-card-title {{
            font-size: 0.85rem;
            font-weight: 600;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            color: #cbd5e1;
        }}

        .grid-card-pack {{
            font-size: 0.7rem;
            color: var(--text-muted);
            text-align: center;
            margin-top: -6px;
        }}

        /* Hidden elements */
        .hidden {{
            display: none !important;
        }}
    </style>
</head>
<body>
    <header>
        <div class="logo-area">
            <div class="logo-icon">P</div>
            <div>
                <h1>Plymouth Themes</h1>
                <p style="font-size: 0.7rem; color: var(--text-muted); font-weight: 500;">Interactive Local Viewer Dashboard</p>
            </div>
        </div>
        
        <div class="controls">
            <div class="search-bar">
                <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input type="text" id="search" placeholder="Search spinners..." autocomplete="off">
            </div>
            
            <div class="btn-group">
                <button class="btn active" id="btn-split" onclick="setViewMode('split')">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/></svg>
                    Split View
                </button>
                <button class="btn" id="btn-grid" onclick="setViewMode('grid')">
                    <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
                    Grid View
                </button>
            </div>
        </div>
    </header>

    <div class="main-container">
        <!-- Sidebar split view -->
        <aside class="sidebar" id="sidebar">
            <!-- Populated dynamically -->
        </aside>

        <!-- Content Area -->
        <main class="content-area">
            <!-- Split View details -->
            <div class="detail-view" id="detail-view">
                <div class="preview-box">
                    <img id="preview-img" src="" alt="Theme Preview">
                </div>
                
                <div class="details-box">
                    <div>
                        <h2 class="theme-title" id="detail-title">Theme Name</h2>
                        <div class="theme-meta" id="detail-meta">
                            <!-- Populated dynamically -->
                        </div>
                    </div>

                    <div class="install-guide">
                        <div class="tabs-header">
                            <button class="tab-btn active" onclick="setDistro('arch')">Arch Linux</button>
                            <button class="tab-btn" onclick="setDistro('debian')">Debian / Ubuntu</button>
                        </div>
                        
                        <!-- Arch Linux install commands -->
                        <div class="tab-content active" id="install-arch">
                            <div class="step-label">Step 1: Copy theme folder to Plymouth library</div>
                            <div class="code-container">
                                <span id="code-arch-cp">sudo cp -r pack_1/abstract_ring /usr/share/plymouth/themes/</span>
                                <button class="copy-btn" onclick="copyCode('code-arch-cp')">Copy</button>
                            </div>
                            <div class="step-label">Step 2: Set as default theme and rebuild Initramfs</div>
                            <div class="code-container">
                                <span id="code-arch-set">sudo plymouth-set-default-theme -R abstract_ring</span>
                                <button class="copy-btn" onclick="copyCode('code-arch-set')">Copy</button>
                            </div>
                        </div>

                        <!-- Debian/Ubuntu install commands -->
                        <div class="tab-content" id="install-debian">
                            <div class="step-label">Step 1: Copy theme folder to Plymouth library</div>
                            <div class="code-container">
                                <span id="code-deb-cp">sudo cp -r pack_1/abstract_ring /usr/share/plymouth/themes/</span>
                                <button class="copy-btn" onclick="copyCode('code-deb-cp')">Copy</button>
                            </div>
                            <div class="step-label">Step 2: Install as alternative path</div>
                            <div class="code-container">
                                <span id="code-deb-install">sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/abstract_ring/abstract_ring.plymouth 100</span>
                                <button class="copy-btn" onclick="copyCode('code-deb-install')">Copy</button>
                            </div>
                            <div class="step-label">Step 3: Select theme and update initramfs</div>
                            <div class="code-container">
                                <span id="code-deb-update">sudo update-alternatives --config default.plymouth && sudo update-initramfs -u</span>
                                <button class="copy-btn" onclick="copyCode('code-deb-update')">Copy</button>
                            </div>
                        </div>
                    </div>

                    <div class="keyboard-hint">
                        <span>Navigation:</span>
                        <span><kbd>▲</kbd> <kbd>▼</kbd> keys to change selection</span>
                        <span><kbd>Tab</kbd> to change distro tabs</span>
                    </div>
                </div>
            </div>

            <!-- Grid view of all themes -->
            <div class="grid-view" id="grid-view">
                <!-- Populated dynamically -->
            </div>
        </main>
    </div>

    <script>
        const themes = {themes_json};
        
        let activeIndex = 0;
        let filteredThemes = [...themes];
        let viewMode = 'split';
        let currentDistro = 'arch';
        
        // Animation States
        let animationInterval = null;
        const cardIntervals = {{}};

        // Initialize UI
        function init() {{
            renderSidebar();
            renderGridView();
            selectTheme(0);
            
            // Search listener
            document.getElementById('search').addEventListener('input', (e) => {{
                const query = e.target.value.toLowerCase().trim();
                filteredThemes = themes.filter(t => 
                    t.name.toLowerCase().includes(query) || 
                    t.folder.toLowerCase().includes(query)
                );
                
                renderSidebar();
                renderGridView();
                
                if (filteredThemes.length > 0) {{
                    const origIndex = themes.findIndex(t => t.name === filteredThemes[0].name);
                    selectTheme(origIndex);
                }}
            }});

            // Keyboard navigation
            document.addEventListener('keydown', (e) => {{
                if (document.activeElement.tagName === 'INPUT') return;
                
                if (viewMode === 'split' && filteredThemes.length > 0) {{
                    const currentFilteredIdx = filteredThemes.findIndex(t => t.name === themes[activeIndex].name);
                    
                    if (e.key === 'ArrowDown') {{
                        e.preventDefault();
                        const nextIdx = (currentFilteredIdx + 1) % filteredThemes.length;
                        const origIndex = themes.findIndex(t => t.name === filteredThemes[nextIdx].name);
                        selectTheme(origIndex);
                    }} else if (e.key === 'ArrowUp') {{
                        e.preventDefault();
                        const prevIdx = (currentFilteredIdx - 1 + filteredThemes.length) % filteredThemes.length;
                        const origIndex = themes.findIndex(t => t.name === filteredThemes[prevIdx].name);
                        selectTheme(origIndex);
                    }} else if (e.key === 'Tab') {{
                        e.preventDefault();
                        setDistro(currentDistro === 'arch' ? 'debian' : 'arch');
                    }}
                }}
            }});
        }}

        // Local Animation Player logic
        function stopAnimation() {{
            if (animationInterval) {{
                clearInterval(animationInterval);
                animationInterval = null;
            }}
        }}

        function startAnimation(theme, imgElement) {{
            stopAnimation();
            
            // If no local frames found, fall back to remote URL (GIF)
            if (!theme.frames || theme.frames.length === 0) {{
                imgElement.src = theme.url;
                return;
            }}

            let frameIndex = 0;
            const basePath = `${{theme.pack_dir}}/${{theme.folder}}/progress-`;
            
            // Instantly show the first frame
            imgElement.src = `${{basePath}}${{theme.frames[0]}}.png`;

            // Preload all frames to memory cache
            const preloadedImages = [];
            theme.frames.forEach(frameNum => {{
                const img = new Image();
                img.src = `${{basePath}}${{frameNum}}.png`;
                preloadedImages.push(img);
            }});

            // Cycle frames at ~16fps (60ms)
            animationInterval = setInterval(() => {{
                frameIndex = (frameIndex + 1) % theme.frames.length;
                imgElement.src = preloadedImages[frameIndex].src;
            }}, 60);
        }}

        // Card Animation loops for Grid view
        function startCardAnimation(theme, cardImgElement, cardId) {{
            if (cardIntervals[cardId]) clearInterval(cardIntervals[cardId]);
            if (!theme.frames || theme.frames.length === 0) return;
            
            let frameIndex = 0;
            const basePath = `${{theme.pack_dir}}/${{theme.folder}}/progress-`;
            
            cardIntervals[cardId] = setInterval(() => {{
                frameIndex = (frameIndex + 1) % theme.frames.length;
                cardImgElement.src = `${{basePath}}${{theme.frames[frameIndex]}}.png`;
            }}, 60);
        }}

        function stopCardAnimation(theme, cardImgElement, cardId) {{
            if (cardIntervals[cardId]) {{
                clearInterval(cardIntervals[cardId]);
                delete cardIntervals[cardId];
            }}
            if (theme.frames && theme.frames.length > 0) {{
                cardImgElement.src = `${{theme.pack_dir}}/${{theme.folder}}/progress-${{theme.frames[0]}}.png`;
            }}
        }}

        function stopAllCardAnimations() {{
            Object.keys(cardIntervals).forEach(cardId => {{
                clearInterval(cardIntervals[cardId]);
                delete cardIntervals[cardId];
            }});
        }}

        // Render functions
        function renderSidebar() {{
            const sidebar = document.getElementById('sidebar');
            sidebar.innerHTML = '';

            const groups = {{}};
            filteredThemes.forEach(t => {{
                if (!groups[t.pack]) groups[t.pack] = [];
                groups[t.pack].push(t);
            }});

            Object.keys(groups).sort().forEach(packName => {{
                const section = document.createElement('div');
                section.className = 'pack-section';

                const header = document.createElement('div');
                header.className = 'pack-header';
                header.textContent = packName;
                section.appendChild(header);

                const ul = document.createElement('ul');
                ul.className = 'theme-list';

                groups[packName].forEach(t => {{
                    const origIndex = themes.findIndex(item => item.name === t.name);
                    const li = document.createElement('li');
                    li.className = 'theme-item' + (origIndex === activeIndex ? ' active' : '');
                    li.id = `sidebar-item-${{origIndex}}`;
                    li.onclick = () => selectTheme(origIndex);
                    
                    li.innerHTML = `
                        <span>${{t.name}}</span>
                        <span class="theme-index">${{origIndex + 1}}</span>
                    `;
                    ul.appendChild(li);
                }});

                section.appendChild(ul);
                sidebar.appendChild(section);
            }});

            if (filteredThemes.length === 0) {{
                sidebar.innerHTML = '<div style="padding: 2rem; color: var(--text-muted); text-align: center;">No themes found</div>';
            }}
        }}

        function renderGridView() {{
            const grid = document.getElementById('grid-view');
            grid.innerHTML = '';

            filteredThemes.forEach(t => {{
                const origIndex = themes.findIndex(item => item.name === t.name);
                const card = document.createElement('div');
                card.className = 'grid-card';
                
                const cardId = `grid-card-${{origIndex}}`;
                card.id = cardId;
                
                const firstFramePath = t.frames && t.frames.length > 0 
                    ? `${{t.pack_dir}}/${{t.folder}}/progress-${{t.frames[0]}}.png`
                    : t.url;

                card.innerHTML = `
                    <div class="grid-card-img">
                        <img id="img-${{cardId}}" src="${{firstFramePath}}" alt="${{t.name}}" loading="lazy">
                    </div>
                    <div class="grid-card-title">${{t.name}}</div>
                    <div class="grid-card-pack">${{t.pack}}</div>
                `;

                // Hover events to start and stop animations locally
                card.addEventListener('mouseenter', () => {{
                    const imgEl = document.getElementById(`img-${{cardId}}`);
                    startCardAnimation(t, imgEl, cardId);
                }});
                
                card.addEventListener('mouseleave', () => {{
                    const imgEl = document.getElementById(`img-${{cardId}}`);
                    stopCardAnimation(t, imgEl, cardId);
                }});

                card.addEventListener('click', () => {{
                    const imgEl = document.getElementById(`img-${{cardId}}`);
                    stopCardAnimation(t, imgEl, cardId);
                    
                    setViewMode('split');
                    selectTheme(origIndex);
                }});

                grid.appendChild(card);
            }});

            if (filteredThemes.length === 0) {{
                grid.innerHTML = '<div style="padding: 4rem; color: var(--text-muted); text-align: center; width: 100%;">No themes found matching your search.</div>';
            }}
        }}

        function selectTheme(index) {{
            if (index < 0 || index >= themes.length) return;
            
            const prevActive = document.querySelector(`.theme-item.active`);
            if (prevActive) prevActive.classList.remove('active');

            activeIndex = index;
            const theme = themes[index];

            const item = document.getElementById(`sidebar-item-${{index}}`);
            if (item) {{
                item.classList.add('active');
                item.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
            }}

            document.getElementById('detail-title').textContent = theme.name;
            
            const metaContainer = document.getElementById('detail-meta');
            metaContainer.innerHTML = `
                <span class="meta-tag accent">${{theme.pack}}</span>
                <span class="meta-tag">Folder: ${{theme.pack_dir}}/${{theme.folder}}</span>
                <span class="meta-tag">Frames: ${{theme.frames ? theme.frames.length : 0}}</span>
            `;

            // Start animation
            const previewImg = document.getElementById('preview-img');
            startAnimation(theme, previewImg);

            // Update commands
            document.getElementById('code-arch-cp').textContent = `sudo cp -r ${{theme.pack_dir}}/${{theme.folder}} /usr/share/plymouth/themes/`;
            document.getElementById('code-arch-set').textContent = `sudo plymouth-set-default-theme -R ${{theme.folder}}`;
            
            document.getElementById('code-deb-cp').textContent = `sudo cp -r ${{theme.pack_dir}}/${{theme.folder}} /usr/share/plymouth/themes/`;
            document.getElementById('code-deb-install').textContent = `sudo update-alternatives --install /usr/share/plymouth/themes/default.plymouth default.plymouth /usr/share/plymouth/themes/${{theme.folder}}/${{theme.folder}}.plymouth 100`;
            document.getElementById('code-deb-update').textContent = `sudo update-alternatives --config default.plymouth && sudo update-initramfs -u`;
        }}

        function setViewMode(mode) {{
            viewMode = mode;
            document.getElementById('btn-split').classList.toggle('active', mode === 'split');
            document.getElementById('btn-grid').classList.toggle('active', mode === 'grid');

            if (mode === 'split') {{
                stopAllCardAnimations();
                document.getElementById('sidebar').classList.remove('hidden');
                document.getElementById('detail-view').style.display = 'grid';
                document.getElementById('grid-view').style.display = 'none';
                selectTheme(activeIndex);
            }} else {{
                stopAnimation();
                document.getElementById('sidebar').classList.add('hidden');
                document.getElementById('detail-view').style.display = 'none';
                document.getElementById('grid-view').style.display = 'grid';
            }}
        }}

        function setDistro(distro) {{
            currentDistro = distro;
            const isArch = distro === 'arch';
            document.querySelectorAll('.install-guide .tab-btn')[0].classList.toggle('active', isArch);
            document.querySelectorAll('.install-guide .tab-btn')[1].classList.toggle('active', !isArch);
            document.getElementById('install-arch').classList.toggle('active', isArch);
            document.getElementById('install-debian').classList.toggle('active', !isArch);
        }}

        function copyCode(elementId) {{
            const text = document.getElementById(elementId).textContent;
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.querySelector(`#${{elementId}} ~ .copy-btn`) || 
                            document.querySelector(`#${{elementId}}`).nextElementSibling;
                const originalText = btn.textContent;
                btn.textContent = 'Copied!';
                btn.style.color = '#818cf8';
                setTimeout(() => {{
                    btn.textContent = originalText;
                    btn.style.color = '';
                }}, 1500);
            }}).catch(err => {{
                console.error('Failed to copy text: ', err);
            }});
        }}

        window.onload = init;
    </script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated local dashboard: {filepath}")

def open_tabs(themes, urls_to_open):
    print(f"\nOpening {len(urls_to_open)} tabs in your default web browser...")
    for url in urls_to_open:
        webbrowser.open_new_tab(url)
    print("Done! Browser tabs should be opening.")

def main():
    themes = parse_themes()
    print(f"Loaded {len(themes)} spinner previews from README.md.")
    
    # Check what packs we have
    packs = sorted(list(set(t["pack"] for t in themes)))
    
    while True:
        print("\nPlymouth Themes - Preview Tool Options:")
        print("---------------------------------------")
        print("1. Generate and Open the Local Interactive Dashboard (Recommended!)")
        print("   -> Opens inside your system's temp directory so your workspace remains clean.")
        print("2. Export 'index.html' to the repository root")
        print("   -> Use this to push to your GitHub fork to deploy on GitHub Pages!")
        print("3. Open ALL 80 spinner GIFs directly as browser tabs (from remote)")
        print("   -> WARNING: Can cause high CPU/RAM usage and popup blockers")
        
        for idx, pack in enumerate(packs, start=4):
            count = sum(1 for t in themes if t["pack"] == pack)
            print(f"{idx}. Open {pack} ({count} themes) as browser tabs (from remote)")
            
        exit_option = len(packs) + 4
        print(f"{exit_option}. Exit")
        
        try:
            choice = input(f"\nSelect an option (1-{exit_option}): ").strip()
            if not choice:
                continue
                
            choice_num = int(choice)
            
            if choice_num == 1:
                generate_html(themes, TEMP_HTML_PATH)
                webbrowser.open(f"file://{TEMP_HTML_PATH}")
                print("Dashboard opened in your web browser. Enjoy!")
                break
                
            elif choice_num == 2:
                generate_html(themes, EXPORT_HTML_PATH)
                print(f"\nCreated index.html in repository root.")
                print(f"You can now run: git add index.html && git commit -m 'Add interactive preview index.html'")
                print(f"And push it to your fork to enable GitHub Pages!")
                break
                
            elif choice_num == 3:
                confirm = input("Are you sure you want to open 80 tabs at once? [y/N]: ").strip().lower()
                if confirm == 'y':
                    urls = [t["url"] for t in themes]
                    open_tabs(themes, urls)
                    break
                else:
                    print("Cancelled opening all tabs.")
                    
            elif 4 <= choice_num < exit_option:
                selected_pack = packs[choice_num - 4]
                pack_themes = [t for t in themes if t["pack"] == selected_pack]
                confirm = input(f"Open {len(pack_themes)} tabs for {selected_pack}? [Y/n]: ").strip().lower()
                if confirm != 'n':
                    urls = [t["url"] for t in pack_themes]
                    open_tabs(themes, urls)
                    break
                else:
                    print("Cancelled opening pack tabs.")
                    
            elif choice_num == exit_option:
                print("Exiting.")
                break
            else:
                print(f"Invalid option. Please enter a number between 1 and {exit_option}.")
        except ValueError:
            print("Please enter a valid number.")

if __name__ == "__main__":
    main()
