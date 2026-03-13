---
name: design-system-forge
description: >
  AI-powered design system generator with industry-specific rules, anti-pattern
  detection, accessibility validation, and framework-aware output. Covers 50+
  product categories with color palettes, typography, layout patterns, and
  component guidelines. Use when "design system", "UI guidelines", "color
  palette", "typography", "design-system-forge", "landing page design",
  "dashboard design", or any UI/UX design request is mentioned.
---

# Design System Forge

An enterprise-grade AI design intelligence engine that generates complete, production-ready design systems tailored to your industry, technology stack, and design mood.

## Core Capabilities

### Multi-Domain Design Engine
The system performs 5 parallel semantic searches across:
- **Product Category Matching**: Industry-specific design rules (SaaS, Fintech, Healthcare, E-commerce, etc.)
- **Style Recognition**: Visual aesthetics (minimalist, maximalist, glassmorphism, neumorphism, etc.)
- **Color Profiling**: Mood-based palette generation with WCAG AA contrast validation
- **Typography Selection**: Font pairing recommendations with personality matching
- **Pattern Discovery**: Layout structures and component behaviors specific to your category

Ranking uses BM25-inspired relevance scoring combined with semantic similarity for intelligent rule application.

### 50+ Product Categories
Each category includes:
- Recommended layout patterns and information architecture
- Color mood profiles with specific hex palettes
- Typography personality with font pairings
- Key effects (shadows, animations, hover states)
- Anti-patterns (what NOT to do in your industry)
- Component interaction patterns

**Covered Industries**: SaaS, Fintech, Healthcare, E-commerce, Education, Social Media, Developer Tools, AI/ML Platforms, Legal Tech, Real Estate, Food & Restaurant, Travel, Fitness, Gaming, Cybersecurity, IoT, Enterprise B2B, Nonprofit, Government, Media & Publishing, Crypto, HealthTech, PropTech, EdTech, InsurTech, RetailTech, LogisticsTech, ManufacturingTech, AgriTech, GreenTech, FinOps, DevOps Tools, Data Analytics, BI Platforms, CRM Systems, ERP Platforms, Project Management, Communications, Design Tools, Video Platforms, Music Platforms, Podcast Platforms, Weather Apps, News Aggregators, Booking Platforms, Delivery Services, Marketplace Platforms, and more.

### Design System Output Format
Generated systems follow this structure:
```
design-system/
├── MASTER.md              # Global design tokens and rules
├── pages/
│   ├── homepage.md        # Page-specific guidelines
│   ├── dashboard.md       # Dashboard patterns
│   └── onboarding.md      # Onboarding flows
└── components/
    ├── guidelines.md      # Component patterns
    ├── buttons.md         # Button styles and states
    ├── forms.md           # Form patterns
    └── navigation.md      # Navigation patterns
```

### Framework-Specific Output
Choose your technology stack for tailored implementation guides:

**React + Tailwind**
- Utility class patterns
- Component composition examples
- Props interface documentation

**Vue + CSS**
- Scoped style patterns
- Composition API integration
- Global CSS custom properties

**SwiftUI**
- View builder patterns
- Environment object usage
- Modifier composition

**HTML + CSS**
- Vanilla CSS patterns
- CSS custom properties (variables)
- BEM naming conventions

**Angular + Material**
- Component API documentation
- Theme configuration
- Utility service patterns

### Accessibility Validation

Every generated design system includes:
- **WCAG AA Compliance**: Contrast ratio validation (4.5:1 for text, 3:1 for graphics)
- **Responsive Breakpoints**: 375px (mobile), 768px (tablet), 1024px (laptop), 1440px (desktop)
- **Keyboard Navigation**: Tab order documentation, focus indicator specifications
- **Touch Targets**: 48×48px minimum for interactive elements
- **Screen Reader Support**: ARIA label recommendations and semantic HTML patterns
- **Color Contrast Matrix**: Mapping of all color combinations with pass/fail status

### Anti-Pattern Detection
The system identifies and warns against:
- Industry-inappropriate color choices
- Inaccessible typography sizes (< 16px for body text)
- Unsafe contrast ratios
- Cluttered layouts for minimalist industries
- Overly simple designs for complex B2B tools
- Missing affordances in interactive elements
- Inconsistent spacing and rhythm

## Usage Examples

```bash
# Generate SaaS design system with React + Tailwind focus
python3 design_forge.py generate --category saas --stack react --mood professional

# Healthcare platform with accessibility-first approach
python3 design_forge.py generate --category healthcare --stack vue --mood trustworthy

# E-commerce design system with energetic mood
python3 design_forge.py generate --category ecommerce --stack html --mood energetic

# Fintech with strict accessibility
python3 design_forge.py generate --category fintech --stack react --mood secure --accessibility-strict

# Validate existing design against rules
python3 design_forge.py validate --category saas --colors "#3B82F6" "#1F2937" "#10B981"

# Get color palette recommendations for specific mood
python3 design_forge.py colors --category startup --mood innovative
```

## Key Design Principles

### Category-Aware Design
Different industries require different design approaches:
- **SaaS**: Clean, professional, data-forward, minimal distractions
- **Fintech**: Secure, trustworthy, precise, confidence-building
- **Healthcare**: Calming, accessible, clear information hierarchy, patient-focused
- **E-commerce**: Energetic, persuasive, conversion-focused, social proof
- **Education**: Encouraging, structured, exploration-friendly, progress-visible
- **Gaming**: Energetic, immersive, feedback-rich, engagement-optimized

### Mood-Based Design
Select from moods that influence every design decision:
- **Professional**: Corporate, serious, confidence-building (financial, legal, enterprise)
- **Trustworthy**: Honest, transparent, reliable (healthcare, finance, government)
- **Energetic**: Dynamic, vibrant, motivating (social, gaming, fitness)
- **Calming**: Peaceful, minimal, focused (meditation, therapy, wellness)
- **Playful**: Fun, approachable, friendly (education, social, consumer)
- **Secure**: Protective, controlled, fortress-like (cybersecurity, fintech, legal)
- **Innovative**: Forward-thinking, cutting-edge, experimental (AI, tech, startup)

### Color Psychology
Palettes are scientifically selected:
- **Trust & Reliability**: Blues and greens (fintech, healthcare)
- **Energy & Action**: Reds and oranges (e-commerce, gaming)
- **Growth & Progress**: Greens (education, SaaS, fitness)
- **Creativity & Innovation**: Purples and magentas (design tools, creative platforms)
- **Premium & Exclusivity**: Deep navy, gold, black (luxury, high-end services)

## Design Tokens

Every generated system includes:

### Color System
- Primary, secondary, accent, neutral palette
- Status colors (success, warning, error, info)
- Semantic color mapping (interactive, disabled, hover, active)
- Dark mode variants

### Typography System
- Font families (primary, secondary, monospace)
- Scale: 10px to 48px with semantic labels
- Font weights: 400, 500, 600, 700, 800
- Line heights and letter spacing

### Spacing System
- Base unit: 4px or 8px
- Scale: xs (4px) to xl (32px)
- Consistent rhythm across components

### Effects System
- Shadow elevation scale (1-4 levels)
- Border radius scale (xs to full)
- Animation timing (fast, normal, slow)
- Transition curves (ease-in-out, ease-in, ease-out)

## Component Patterns

All generated systems document:
- **Buttons**: Primary, secondary, tertiary, danger states
- **Forms**: Input patterns, validation, error handling
- **Navigation**: Header, sidebar, breadcrumb patterns
- **Cards**: Content container patterns and variations
- **Modals**: Dialog patterns and overlay behaviors
- **Alerts**: Status messaging patterns
- **Typography**: Heading, body, caption styles
- **Pagination**: Data set navigation patterns
- **Tables**: Data visualization patterns

## Accessibility Checklist

Generated systems include:
- [ ] All color pairs meet WCAG AA contrast ratios
- [ ] Text is at least 16px for body content
- [ ] Interactive elements are at least 48×48px
- [ ] Keyboard navigation is fully supported
- [ ] Focus indicators are visible (min 2px outline)
- [ ] Error messages are associated with form fields
- [ ] Images have descriptive alt text guidance
- [ ] Motion is optional (respects prefers-reduced-motion)
- [ ] Zoom up to 200% is supported
- [ ] Language is clear and consistent

## Best Practices

1. **Consistency is Key**: All design decisions build on established tokens
2. **Contrast First**: Accessibility improves usability for everyone
3. **Whitespace Matters**: Breathing room makes interfaces clearer
4. **Motion Purpose**: Every animation should communicate or guide
5. **Type Hierarchy**: Clear visual hierarchy reduces cognitive load
6. **Component Reusability**: Define once, use everywhere
7. **Dark Mode Ready**: Plan for light and dark variants
8. **Performance**: Optimize images, reduce animations on slow devices
9. **Mobile First**: Design for smallest screen first, then enhance
10. **Test with Real Users**: Validate assumptions with your audience

## Getting Started

1. Identify your product category from the 50+ options
2. Choose your design mood (professional, energetic, calming, etc.)
3. Select your technology stack (React, Vue, SwiftUI, HTML, etc.)
4. Run the generator to create your complete design system
5. Customize tokens and component patterns for your brand
6. Validate against accessibility requirements
7. Implement across your product

## Output Quality

Every generated design system includes:
- **Completeness**: All components and patterns documented
- **Accuracy**: Industry-specific best practices applied
- **Actionability**: Ready-to-implement code examples
- **Scalability**: Token system that grows with your product
- **Maintainability**: Clear structure for team collaboration
- **Accessibility**: WCAG AA compliance built-in
- **Flexibility**: Customization hooks for brand personalization

---

**Generated Design Systems are Production-Ready** — Use immediately or as a foundation for deeper customization.
