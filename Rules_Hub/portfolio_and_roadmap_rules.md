---
trigger: portfolio, bim_portfolio, weekend_roadmap, ui_navigation, 3d_buttons
description: BIM Portfolio UI/UX standards, 3D tactile button conventions, and Weekend video production reminder & roadmap.
---

# BIM Portfolio Engineering Standards & Weekend Video Roadmap

## 1. Weekend Video Production Roadmap & Active Reminder
- **Context & Reminder Trigger**: When the user initiates a session on or approaching the weekend (or when discussing portfolio media enhancements), proactively remind the user of the planned **Tool Demo Video Integration**.
- **Target Tools for Video Captures (15–30s crisp screencasts)**:
  1. **Door & Window (D&W) Dynamic Scheduling Suite**: Parameter batch injection, dynamic table auto-alignment, live dims generation.
  2. **Enterprise Batch Exporter (v2.0)**: Background multi-file execution, inline vector preview, selective collision-free archiving.
  3. **AutoCAD MCP Bridge**: Automated drawing prep, layer isolation, and boundary extraction.
- **Implementation Architecture**:
  - Videos must be embedded within the project/tool detail modal (`openToolModal()`) and optional card preview with auto-looping, mute by default, and dark architectural frame chrome.
  - Video formats must be web-optimized (compressed MP4 / WebM / animated WebP) with zero initial page load performance penalty.

## 2. Portfolio 3D Tactile Button & Navigation Invariants
- **Navbar Shortcuts as 3D Box Buttons**:
  - All navbar shortcuts (`Custom Tools`, `BIM Projects`, `Capabilities`, `Philosophy`, `Credentials`, `Contact`) must remain full 3D tactile secondary buttons (`.btn.btn-secondary.nav-btn`) equipped with FontAwesome icons.
  - Always enforce `white-space: nowrap;` so that labels never wrap onto multiple lines.
- **Strict Desktop / Mobile Toggle Boundary**:
  - The mobile hamburger toggle (`.mobile-toggle`) must strictly remain `display: none !important;` on desktop viewports.
  - It must only become active (`display: inline-flex !important;`) on viewports `<= 992px`.
- **Theme Toggle (`⚙`) Isolation**:
  - The theme switcher must always be docked at the far right of the navbar, separated by a `.nav-divider` after `Get In Touch`, guaranteeing generous breathing room from `Contact`.

## 3. Data & Static Component Consistency Guardrail
- Whenever updating tool metadata or features in `js/projects-data.js`, always verify whether corresponding static elements (such as the Hero Interactive Console in `index.html`) require synchronized updates.
- Always increment asset version query strings (`?v=X.X`) on `styles.css`, `projects-data.js`, and `main.js` to bypass browser caching.
