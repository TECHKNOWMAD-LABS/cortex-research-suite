# Design Rules Reference

Top 20 industry design rules with specific palettes, typography, layouts, and anti-patterns.

---

## 1. SaaS (Software as a Service)

**Color Palette**
- Primary: `#3B82F6` (Trust Blue)
- Secondary: `#6366F1` (Indigo)
- Accent: `#06B6D4` (Cyan)
- Success: `#10B981` (Emerald)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Inter 700 (Bold)
- Heading: Inter 600 (SemiBold)
- Body: Inter 400 (Regular)
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Sidebar navigation with collapsible menu
- Top command bar with search
- Dashboard grid system (8-12 columns)
- Card-based content containers
- Two-column layout for settings/configuration

**Key Effects**
- Shadows: Subtle, elevation-based (sm to md)
- Borders: 1px solid neutral-200
- Animations: Micro-interactions (150-300ms)
- Hover: Subtle background shift or elevation

**Anti-Patterns**
- Overly bright or saturated colors
- Inconsistent button styles across pages
- Heavy animations slowing workflows
- No keyboard shortcuts for power users
- Unclear data visualization hierarchy

---

## 2. Fintech (Financial Technology)

**Color Palette**
- Primary: `#1E40AF` (Deep Blue)
- Secondary: `#065F73` (Teal)
- Accent: `#0891B2` (Cyan)
- Success: `#059669` (Green)
- Warning: `#D97706` (Amber)
- Error: `#DC2626` (Red)

**Typography**
- Display: Georgia 700
- Heading: Georgia 600
- Body: System UI 400
- Monospace: IBM Plex Mono 400

**Layout Patterns**
- Dashboard with account overview
- Transaction list with detailed view
- Account management pages
- Security-focused layouts
- Transaction confirmation flows

**Key Effects**
- Shadows: Professional, controlled (md to lg)
- Borders: 1px solid neutral-300
- Animations: Linear, predictable (100-200ms)
- Hover: Subtle elevation increase

**Anti-Patterns**
- Playful animations (reduce trust)
- Hidden or unclear pricing
- Confusing transaction terminology
- Lack of confirmation dialogs
- Missing 2FA indicators

---

## 3. Healthcare & Medical

**Color Palette**
- Primary: `#0EA5E9` (Sky Blue)
- Secondary: `#06B6D4` (Cyan)
- Accent: `#10B981` (Green)
- Success: `#059669` (Emerald)
- Warning: `#EAB308` (Yellow)
- Error: `#DC2626` (Red)

**Typography**
- Display: Lora 700
- Heading: Lora 600
- Body: Open Sans 400
- Monospace: Roboto Mono 400

**Layout Patterns**
- Patient-centered information display
- Medical record organization
- Appointment scheduling grid
- Emergency alert prominent placement
- Doctor-patient communication layout

**Key Effects**
- Shadows: Soft, calming (xs to sm)
- Borders: 1px solid neutral-300
- Animations: Smooth, reassuring (300-400ms)
- Hover: Gentle background tint

**Anti-Patterns**
- Medical jargon without explanations
- Insufficient visual hierarchy for critical info
- Lack of accessibility features
- Insensitive imagery
- Confusing appointment flows

---

## 4. E-Commerce & Retail

**Color Palette**
- Primary: `#EC4899` (Pink)
- Secondary: `#F43F5E` (Rose)
- Accent: `#EF4444` (Red)
- Success: `#22C55E` (Green)
- Warning: `#FBBF24` (Amber)
- Error: `#DC2626` (Red)

**Typography**
- Display: Playfair Display 700
- Heading: Playfair Display 600
- Body: Poppins 400
- Monospace: Source Code Pro 400

**Layout Patterns**
- Hero section with product imagery
- Grid-based product listings
- Quick view overlays
- Shopping cart with order summary
- Multi-step checkout flow

**Key Effects**
- Shadows: Strong, attention-grabbing (md to lg)
- Borders: 2px solid primary on hover
- Animations: Energetic, engaging (100-250ms)
- Hover: Scale up, elevation increase

**Anti-Patterns**
- Hidden or unclear pricing
- Overly complex checkout
- Missing product images
- No customer reviews visible
- Aggressive notifications

---

## 5. Education & Learning

**Color Palette**
- Primary: `#7C3AED` (Purple)
- Secondary: `#6366F1` (Indigo)
- Accent: `#06B6D4` (Cyan)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Montserrat 700
- Heading: Montserrat 600
- Body: Nunito 400
- Monospace: Courier Prime 400

**Layout Patterns**
- Learning path progression
- Course grid with progress visualization
- Lesson structured layout
- Progress tracking dashboard
- Interactive quiz interface

**Key Effects**
- Shadows: Playful, encouraging (xs to sm)
- Borders: 2px solid primary (progress)
- Animations: Celebratory, motivating (150-300ms)
- Hover: Lift effect, shadow increase

**Anti-Patterns**
- Overwhelming content without structure
- No progress visualization
- Lack of gamification
- Unclear learning objectives
- Inaccessible video content

---

## 6. Developer Tools & Platforms

**Color Palette**
- Primary: `#10B981` (Green)
- Secondary: `#06B6D4` (Cyan)
- Accent: `#F59E0B` (Amber)
- Success: `#34D399` (Emerald)
- Warning: `#FBBF24` (Amber)
- Error: `#F87171` (Red)

**Typography**
- Display: Fira Code 700
- Heading: Fira Sans 600
- Body: Fira Sans 400
- Monospace: Fira Code 400

**Layout Patterns**
- IDE-like layout with sidebar and editor
- Documentation split (left nav + content)
- API reference table format
- Console interface with output
- Code snippet displays

**Key Effects**
- Shadows: Minimal, code-focused (xs)
- Borders: 1px solid neutral-300
- Animations: Quick, responsive (100-150ms)
- Hover: Color change, no movement

**Anti-Patterns**
- Inconsistent API documentation
- Unclear error messages
- Outdated code examples
- Missing version information
- No dark mode support

---

## 7. Real Estate & Property

**Color Palette**
- Primary: `#8B5CF6` (Purple)
- Secondary: `#D946EF` (Magenta)
- Accent: `#EC4899` (Pink)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Merriweather 700
- Heading: Merriweather 600
- Body: Lato 400
- Monospace: Source Code Pro 400

**Layout Patterns**
- Property grid with image gallery
- Map integration for location
- Listing detail with photos
- Neighborhood info section
- Schedule showing form

**Key Effects**
- Shadows: Moderate, elegant (sm to md)
- Borders: 2px solid primary on featured
- Animations: Smooth property transitions (200-300ms)
- Hover: Image zoom, shadow increase

**Anti-Patterns**
- Poor quality property images
- Missing neighborhood information
- Unclear pricing breakdown
- No contact method
- Unresponsive property gallery

---

## 8. Social Media & Community

**Color Palette**
- Primary: `#1f2937` (Dark Gray)
- Secondary: `#3b82f6` (Blue)
- Accent: `#ec4899` (Pink)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Inter 700
- Heading: Inter 600
- Body: Inter 400
- Monospace: IBM Plex Mono 400

**Layout Patterns**
- Feed-based timeline
- User profile layout
- Post creation interface
- Comment threads
- Notification center

**Key Effects**
- Shadows: Subtle, layer-based (xs to sm)
- Borders: 1px solid neutral-200
- Animations: Smooth reactions (200-250ms)
- Hover: Background tint, shadow

**Anti-Patterns**
- Unclear notification badges
- Missing content moderation indicators
- No mention/tag suggestions
- Unclear privacy settings
- Aggressive recommendation algorithms

---

## 9. Fitness & Wellness

**Color Palette**
- Primary: `#EF4444` (Red)
- Secondary: `#F97316` (Orange)
- Accent: `#FBBF24` (Amber)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#DC2626` (Dark Red)

**Typography**
- Display: Inter Black 900
- Heading: Inter Bold 700
- Body: Inter Regular 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Workout calendar grid
- Progress tracking charts
- Activity feed
- Leaderboard display
- Workout history list

**Key Effects**
- Shadows: Energetic, prominent (sm to md)
- Borders: 2px solid accent on active
- Animations: Dynamic, motivating (150-250ms)
- Hover: Glow effect, elevation

**Anti-Patterns**
- Unclear progress tracking
- No achievement recognition
- Missing social features
- Confusing workout instructions
- Overly complex form inputs

---

## 10. Gaming Platforms

**Color Palette**
- Primary: `#7C3AED` (Purple)
- Secondary: `#EC4899` (Pink)
- Accent: `#FBBF24` (Amber)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Outfit 700
- Heading: Outfit 600
- Body: Open Sans 400
- Monospace: Courier Prime 400

**Layout Patterns**
- Game showcase grid
- Player profile
- Achievement display
- Leaderboard ranking
- Game store catalog

**Key Effects**
- Shadows: Dynamic, glowing (md to lg)
- Borders: Neon glow effects
- Animations: Rapid, feedback-rich (100-200ms)
- Hover: Glow, scale, shadow

**Anti-Patterns**
- Unclear achievement criteria
- No social integration
- Missing in-game notifications
- Confusing UI during gameplay
- Inaccessible colorblind modes

---

## 11. Cybersecurity & Compliance

**Color Palette**
- Primary: `#DC2626` (Red)
- Secondary: `#065F73` (Teal)
- Accent: `#1E40AF` (Blue)
- Success: `#059669` (Green)
- Warning: `#D97706` (Amber)
- Error: `#7F1D1D` (Dark Red)

**Typography**
- Display: IBM Plex Sans 700
- Heading: IBM Plex Sans 600
- Body: IBM Plex Sans 400
- Monospace: IBM Plex Mono 400

**Layout Patterns**
- Risk dashboard
- Threat detection timeline
- System status monitor
- Audit log viewer
- Alert management center

**Key Effects**
- Shadows: Strong, commanding (md to lg)
- Borders: 2px alert colors on warnings
- Animations: Alert states (200-300ms)
- Hover: Emphasis on threats

**Anti-Patterns**
- Unclear threat severity
- Missing alert context
- Confusing remediation steps
- No audit trail
- Insufficient authentication indicators

---

## 12. Content Management Systems (CMS)

**Color Palette**
- Primary: `#2563EB` (Blue)
- Secondary: `#1F2937` (Gray)
- Accent: `#10B981` (Green)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Inter 700
- Heading: Inter 600
- Body: Inter 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Content tree navigation
- Rich text editor
- Media library grid
- Workflow stage indicator
- Publish scheduler

**Key Effects**
- Shadows: Professional (sm to md)
- Borders: 1px solid neutral-300
- Animations: Quick transitions (150-200ms)
- Hover: Subtle highlight

**Anti-Patterns**
- Unclear content status
- No version control visible
- Missing workflow indicators
- Confusing publish settings
- Poor media management

---

## 13. Project Management Tools

**Color Palette**
- Primary: `#3B82F6` (Blue)
- Secondary: `#8B5CF6` (Purple)
- Accent: `#06B6D4` (Cyan)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Poppins 700
- Heading: Poppins 600
- Body: Poppins 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Kanban board columns
- Timeline/Gantt chart
- List view with filters
- Team calendar
- Task detail panel

**Key Effects**
- Shadows: Layered, task-focused (xs to sm)
- Borders: 2px on drag-over state
- Animations: Drag feedback (100-200ms)
- Hover: Highlight, ready-to-move state

**Anti-Patterns**
- Unclear task status
- No deadline visibility
- Missing team assignments
- Confusing filter options
- No progress percentage

---

## 14. Video & Media Platforms

**Color Palette**
- Primary: `#EF4444` (Red)
- Secondary: `#1F2937` (Gray)
- Accent: `#FBBF24` (Amber)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#DC2626` (Red)

**Typography**
- Display: Poppins 700
- Heading: Poppins 600
- Body: Roboto 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Video grid layout
- Player full-screen interface
- Playlist sidebar
- Comments section
- Recommendation carousel

**Key Effects**
- Shadows: Minimal during playback
- Borders: None (distraction-free)
- Animations: Fade only (200-300ms)
- Hover: Overlay controls fade in

**Anti-Patterns**
- Auto-playing videos (without consent)
- Unclear video duration
- No subtitle options
- Missing quality selection
- Intrusive ads

---

## 15. Music & Audio Platforms

**Color Palette**
- Primary: `#1DB954` (Spotify Green)
- Secondary: `#1F1F1F` (Dark)
- Accent: `#1ED760` (Bright Green)
- Success: `#1ED760` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Circular Std 700
- Heading: Circular Std 600
- Body: Circular Std 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Now playing bar
- Playlist grid
- Queue view
- Search results
- Library organization

**Key Effects**
- Shadows: Minimal (xs only)
- Borders: 1px on selected track
- Animations: Smooth playback (200-250ms)
- Hover: Highlight on track

**Anti-Patterns**
- Unclear current playback time
- No queue management
- Missing playlist organization
- Confusing search filters
- No download indicators

---

## 16. News & Publishing

**Color Palette**
- Primary: `#1F2937` (Dark Gray)
- Secondary: `#3B82F6` (Blue)
- Accent: `#EF4444` (Red)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#DC2626` (Red)

**Typography**
- Display: Georgia 700
- Heading: Georgia 600
- Body: Georgia 400
- Monospace: IBM Plex Mono 400

**Layout Patterns**
- Featured article hero
- Article grid/list
- Category filtering
- Search interface
- Reading time indicator

**Key Effects**
- Shadows: Subtle, editorial (xs to sm)
- Borders: 1px subtle dividers
- Animations: Fade transitions (200-300ms)
- Hover: Subtle background tint

**Anti-Patterns**
- Unclear article dates
- Missing author information
- Intrusive ads in content
- No reading time estimates
- Broken image layouts

---

## 17. Banking & Finance

**Color Palette**
- Primary: `#0369A1` (Deep Blue)
- Secondary: `#065F73` (Teal)
- Accent: `#0891B2` (Cyan)
- Success: `#059669` (Green)
- Warning: `#D97706` (Amber)
- Error: `#991B1B` (Dark Red)

**Typography**
- Display: Merriweather 700
- Heading: Merriweather 600
- Body: Source Sans Pro 400
- Monospace: IBM Plex Mono 400

**Layout Patterns**
- Account overview dashboard
- Transaction details
- Transfer wizard
- Loan calculator
- Budget tracking

**Key Effects**
- Shadows: Formal, professional (md to lg)
- Borders: 1px solid neutral-400
- Animations: Linear, trustworthy (200-300ms)
- Hover: Subtle color shift

**Anti-Patterns**
- Unclear fee structures
- Missing balance information
- No transaction categorization
- Unclear loan terms
- No budget visualization

---

## 18. Travel & Booking Platforms

**Color Palette**
- Primary: `#0284C7` (Ocean Blue)
- Secondary: `#DB2777` (Magenta)
- Accent: `#FBBF24` (Amber)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Poppins 700
- Heading: Poppins 600
- Body: Inter 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Search hero section
- Results listing with filters
- Map integration
- Booking summary
- Itinerary view

**Key Effects**
- Shadows: Moderate elevation (sm to md)
- Borders: 2px on selected items
- Animations: Smooth transitions (200-250ms)
- Hover: Elevation increase, info preview

**Anti-Patterns**
- Hidden booking fees
- Unclear cancellation policies
- No price breakdown
- Missing review ratings
- Confusing filter options

---

## 19. Restaurant & Food Delivery

**Color Palette**
- Primary: `#F97316` (Orange)
- Secondary: `#EF4444` (Red)
- Accent: `#EC4899` (Pink)
- Success: `#10B981` (Green)
- Warning: `#FBBF24` (Amber)
- Error: `#DC2626` (Red)

**Typography**
- Display: Fredoka 700
- Heading: Fredoka 600
- Body: Poppins 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Restaurant discovery cards
- Menu category tabs
- Item detail with options
- Cart summary
- Delivery tracking

**Key Effects**
- Shadows: Appetizing (sm to md)
- Borders: 2px on selected items
- Animations: Food-focused (150-250ms)
- Hover: Image zoom, shadow increase

**Anti-Patterns**
- Missing food images
- Unclear delivery time
- No dietary information
- Confusing menu layout
- Hidden service fees

---

## 20. Appointment & Scheduling

**Color Palette**
- Primary: `#7C3AED` (Purple)
- Secondary: `#6366F1` (Indigo)
- Accent: `#06B6D4` (Cyan)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Typography**
- Display: Inter 700
- Heading: Inter 600
- Body: Inter 400
- Monospace: JetBrains Mono 400

**Layout Patterns**
- Calendar grid view
- Time slot selection
- Availability indicator
- Booking confirmation
- Reminder notification

**Key Effects**
- Shadows: Minimal, focus on dates (xs)
- Borders: 2px on selected dates
- Animations: Smooth calendar transitions (200-300ms)
- Hover: Highlight available slots

**Anti-Patterns**
- Unclear available times
- No timezone display
- Missing confirmation details
- Confusing cancellation process
- No reminder options

---

## Accessibility Guidelines (All Categories)

### Color Contrast
- **AA Standard**: 4.5:1 for normal text, 3:1 for large text
- **AAA Standard**: 7:1 for normal text, 4.5:1 for large text

### Responsive Breakpoints
- Mobile: 375px
- Tablet: 768px
- Desktop: 1024px
- Wide: 1440px

### Touch Target Sizing
- Minimum: 44x44px (recommended)
- Optimal: 48x48px
- Minimum spacing: 8px between targets

### Type Scale
- Minimum body: 16px
- Minimum caption: 12px
- Recommended line-height: 1.5-1.6

### Focus Indicators
- Minimum visible outline: 2px
- Recommended color: Distinct from background
- Should not obscure content

---

**Last Updated**: March 2026  
Generated by Design System Forge
