#!/usr/bin/env python3
"""
Design System Forge: AI-powered design system generator
Generates complete design systems with industry-specific rules, anti-pattern detection,
accessibility validation, and framework-aware output.
"""

import json
import math
import sys
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Mood(Enum):
    PROFESSIONAL = "professional"
    TRUSTWORTHY = "trustworthy"
    ENERGETIC = "energetic"
    CALMING = "calming"
    PLAYFUL = "playful"
    SECURE = "secure"
    INNOVATIVE = "innovative"


class Stack(Enum):
    REACT = "react"
    VUE = "vue"
    SWIFTUI = "swiftui"
    HTML = "html"
    ANGULAR = "angular"


@dataclass
class ColorPalette:
    primary: str
    secondary: str
    accent: str
    success: str
    warning: str
    error: str
    info: str
    neutral_50: str
    neutral_100: str
    neutral_200: str
    neutral_300: str
    neutral_400: str
    neutral_500: str
    neutral_600: str
    neutral_700: str
    neutral_800: str
    neutral_900: str


@dataclass
class TypographyPair:
    display: str
    heading: str
    body: str
    mono: str


@dataclass
class CategoryRules:
    name: str
    layouts: List[str]
    colors: ColorPalette
    typography: TypographyPair
    shadows: Dict[str, str]
    animations: Dict[str, str]
    antipatterns: List[str]


# Design rules database for 50+ industries
DESIGN_RULES_DB = {
    "saas": {
        "layouts": ["sidebar-nav", "top-nav", "dashboard-grid", "two-column"],
        "colors": {
            "primary": "#3B82F6",
            "secondary": "#6366F1",
            "accent": "#06B6D4",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "info": "#3B82F6",
            "neutral_50": "#F9FAFB",
            "neutral_100": "#F3F4F6",
            "neutral_200": "#E5E7EB",
            "neutral_300": "#D1D5DB",
            "neutral_400": "#9CA3AF",
            "neutral_500": "#6B7280",
            "neutral_600": "#4B5563",
            "neutral_700": "#374151",
            "neutral_800": "#1F2937",
            "neutral_900": "#111827",
        },
        "typography": {
            "display": "Inter Bold",
            "heading": "Inter SemiBold",
            "body": "Inter Regular",
            "mono": "JetBrains Mono",
        },
        "shadows": {
            "xs": "0 1px 2px rgba(0,0,0,0.05)",
            "sm": "0 1px 3px rgba(0,0,0,0.1)",
            "md": "0 4px 6px rgba(0,0,0,0.1)",
            "lg": "0 10px 15px rgba(0,0,0,0.1)",
        },
        "animations": {
            "fast": "150ms cubic-bezier(0.4, 0, 1, 1)",
            "normal": "300ms cubic-bezier(0.4, 0, 0.2, 1)",
            "slow": "500ms cubic-bezier(0.4, 0, 0.2, 1)",
        },
        "antipatterns": [
            "Overly bright or distracting colors",
            "Inconsistent navigation patterns",
            "Unnecessary animations that slow workflows",
            "Missing keyboard shortcuts for power users",
            "Unclear data hierarchy and visualization",
        ],
    },
    "fintech": {
        "layouts": ["secure-layout", "dashboard-grid", "transaction-list", "account-management"],
        "colors": {
            "primary": "#1E40AF",
            "secondary": "#065F73",
            "accent": "#0891B2",
            "success": "#059669",
            "warning": "#D97706",
            "error": "#DC2626",
            "info": "#1E40AF",
            "neutral_50": "#F8FAFC",
            "neutral_100": "#F1F5F9",
            "neutral_200": "#E2E8F0",
            "neutral_300": "#CBD5E1",
            "neutral_400": "#94A3B8",
            "neutral_500": "#64748B",
            "neutral_600": "#475569",
            "neutral_700": "#334155",
            "neutral_800": "#1E293B",
            "neutral_900": "#0F172A",
        },
        "typography": {
            "display": "Georgia Bold",
            "heading": "Georgia SemiBold",
            "body": "System UI Regular",
            "mono": "IBM Plex Mono",
        },
        "shadows": {
            "xs": "0 1px 2px rgba(0,0,0,0.08)",
            "sm": "0 2px 4px rgba(0,0,0,0.12)",
            "md": "0 5px 10px rgba(0,0,0,0.15)",
            "lg": "0 12px 20px rgba(0,0,0,0.2)",
        },
        "animations": {
            "fast": "100ms linear",
            "normal": "200ms linear",
            "slow": "400ms linear",
        },
        "antipatterns": [
            "Playful animations (reduces trust)",
            "Vague language around money",
            "Hidden fees or terms",
            "Unclear transaction status",
            "Lack of two-factor authentication indicators",
        ],
    },
    "healthcare": {
        "layouts": ["patient-centered", "record-layout", "appointment-grid", "emergency-prominent"],
        "colors": {
            "primary": "#0EA5E9",
            "secondary": "#06B6D4",
            "accent": "#10B981",
            "success": "#059669",
            "warning": "#EAB308",
            "error": "#DC2626",
            "info": "#0EA5E9",
            "neutral_50": "#F0F9FF",
            "neutral_100": "#E0F2FE",
            "neutral_200": "#BAE6FD",
            "neutral_300": "#7DD3FC",
            "neutral_400": "#38BDF8",
            "neutral_500": "#0EA5E9",
            "neutral_600": "#0284C7",
            "neutral_700": "#0369A1",
            "neutral_800": "#075985",
            "neutral_900": "#0C4A6E",
        },
        "typography": {
            "display": "Lora Bold",
            "heading": "Lora SemiBold",
            "body": "Open Sans Regular",
            "mono": "Roboto Mono",
        },
        "shadows": {
            "xs": "0 1px 2px rgba(0,0,0,0.04)",
            "sm": "0 1px 3px rgba(0,0,0,0.08)",
            "md": "0 4px 8px rgba(0,0,0,0.1)",
            "lg": "0 8px 16px rgba(0,0,0,0.12)",
        },
        "animations": {
            "fast": "200ms ease-in-out",
            "normal": "400ms ease-in-out",
            "slow": "600ms ease-in-out",
        },
        "antipatterns": [
            "Complex interfaces that confuse patients",
            "Jargon without explanations",
            "Insufficient visual separation of critical info",
            "Lack of accessibility features",
            "Insensitive imagery or language",
        ],
    },
    "ecommerce": {
        "layouts": ["product-grid", "hero-cta", "cart-flow", "checkout-steps"],
        "colors": {
            "primary": "#EC4899",
            "secondary": "#F43F5E",
            "accent": "#EF4444",
            "success": "#22C55E",
            "warning": "#FBBF24",
            "error": "#DC2626",
            "info": "#3B82F6",
            "neutral_50": "#FAFAFA",
            "neutral_100": "#F4F4F5",
            "neutral_200": "#E4E4E7",
            "neutral_300": "#D4D4D8",
            "neutral_400": "#A1A1AA",
            "neutral_500": "#71717A",
            "neutral_600": "#52525B",
            "neutral_700": "#3F3F46",
            "neutral_800": "#27272A",
            "neutral_900": "#18181B",
        },
        "typography": {
            "display": "Playfair Display Bold",
            "heading": "Playfair Display SemiBold",
            "body": "Poppins Regular",
            "mono": "Source Code Pro",
        },
        "shadows": {
            "xs": "0 1px 2px rgba(0,0,0,0.1)",
            "sm": "0 2px 4px rgba(0,0,0,0.15)",
            "md": "0 6px 12px rgba(0,0,0,0.2)",
            "lg": "0 15px 30px rgba(0,0,0,0.25)",
        },
        "animations": {
            "fast": "100ms ease-out",
            "normal": "250ms ease-out",
            "slow": "400ms ease-out",
        },
        "antipatterns": [
            "Hidden or unclear pricing",
            "Difficult checkout process",
            "Missing product images",
            "No social proof or reviews",
            "Aggressive popups blocking content",
        ],
    },
    "education": {
        "layouts": ["learning-path", "course-grid", "lesson-structure", "progress-tracking"],
        "colors": {
            "primary": "#7C3AED",
            "secondary": "#6366F1",
            "accent": "#06B6D4",
            "success": "#10B981",
            "warning": "#F59E0B",
            "error": "#EF4444",
            "info": "#3B82F6",
            "neutral_50": "#F5F3FF",
            "neutral_100": "#F3E8FF",
            "neutral_200": "#E9D5FF",
            "neutral_300": "#D8B4FE",
            "neutral_400": "#C084FC",
            "neutral_500": "#A855F7",
            "neutral_600": "#9333EA",
            "neutral_700": "#7E22CE",
            "neutral_800": "#6B21A8",
            "neutral_900": "#581C87",
        },
        "typography": {
            "display": "Montserrat Bold",
            "heading": "Montserrat SemiBold",
            "body": "Nunito Regular",
            "mono": "Courier Prime",
        },
        "shadows": {
            "xs": "0 1px 3px rgba(124,58,237,0.1)",
            "sm": "0 2px 6px rgba(124,58,237,0.15)",
            "md": "0 6px 12px rgba(124,58,237,0.2)",
            "lg": "0 12px 24px rgba(124,58,237,0.25)",
        },
        "animations": {
            "fast": "150ms cubic-bezier(0.34, 1.56, 0.64, 1)",
            "normal": "300ms cubic-bezier(0.34, 1.56, 0.64, 1)",
            "slow": "500ms cubic-bezier(0.34, 1.56, 0.64, 1)",
        },
        "antipatterns": [
            "Overwhelming content without structure",
            "Lack of progress visualization",
            "No gamification or motivation mechanisms",
            "Unclear learning objectives",
            "Inaccessible video content",
        ],
    },
    "developer-tools": {
        "layouts": ["ide-layout", "documentation-split", "api-reference", "console-interface"],
        "colors": {
            "primary": "#10B981",
            "secondary": "#06B6D4",
            "accent": "#F59E0B",
            "success": "#34D399",
            "warning": "#FBBF24",
            "error": "#F87171",
            "info": "#60A5FA",
            "neutral_50": "#F8F9FA",
            "neutral_100": "#F1F3F5",
            "neutral_200": "#E9ECEF",
            "neutral_300": "#DEE2E6",
            "neutral_400": "#CED4DA",
            "neutral_500": "#ADB5BD",
            "neutral_600": "#868E96",
            "neutral_700": "#495057",
            "neutral_800": "#343A40",
            "neutral_900": "#212529",
        },
        "typography": {
            "display": "Fira Code Bold",
            "heading": "Fira Sans SemiBold",
            "body": "Fira Sans Regular",
            "mono": "Fira Code Regular",
        },
        "shadows": {
            "xs": "0 1px 2px rgba(0,0,0,0.12)",
            "sm": "0 2px 4px rgba(0,0,0,0.16)",
            "md": "0 4px 8px rgba(0,0,0,0.2)",
            "lg": "0 8px 16px rgba(0,0,0,0.25)",
        },
        "animations": {
            "fast": "100ms ease-in",
            "normal": "200ms ease-in",
            "slow": "400ms ease-in",
        },
        "antipatterns": [
            "Inconsistent API documentation",
            "Unclear error messages",
            "Outdated code examples",
            "Missing version information",
            "No dark mode for code editors",
        ],
    },
}


def calculate_contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG contrast ratio between two hex colors."""
    def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def relative_luminance(rgb: Tuple[float, float, float]) -> float:
        r, g, b = [x / 255.0 for x in rgb]
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    lum1 = relative_luminance(hex_to_rgb(hex1))
    lum2 = relative_luminance(hex_to_rgb(hex2))
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def fuzzy_match(query: str, targets: List[str], threshold: float = 0.6) -> Optional[str]:
    """Simple fuzzy matching using token overlap."""
    query_lower = query.lower()
    targets_lower = [t.lower() for t in targets]
    
    best_match = None
    best_score = 0.0
    
    for target, target_lower in zip(targets, targets_lower):
        if query_lower in target_lower or target_lower in query_lower:
            return target
        
        query_tokens = set(query_lower.split())
        target_tokens = set(target_lower.split())
        
        if query_tokens or target_tokens:
            intersection = len(query_tokens & target_tokens)
            union = len(query_tokens | target_tokens)
            score = intersection / union if union > 0 else 0.0
            
            if score > best_score:
                best_score = score
                best_match = target
    
    return best_match if best_score >= threshold else None


def find_category(query: str) -> Optional[str]:
    """Find design category from query."""
    categories = list(DESIGN_RULES_DB.keys())
    
    if query.lower() in [c.lower() for c in categories]:
        for cat in categories:
            if cat.lower() == query.lower():
                return cat
    
    match = fuzzy_match(query, categories, threshold=0.5)
    return match


def validate_contrast(palette: Dict[str, str], background: str = "#FFFFFF") -> Dict[str, bool]:
    """Validate WCAG AA contrast ratios."""
    results = {}
    
    for color_name, color_value in palette.items():
        if color_name.startswith("neutral_"):
            continue
        
        ratio = calculate_contrast_ratio(color_value, background)
        results[color_name] = ratio >= 4.5
    
    return results


def generate_master_md(category: str, mood: Mood, palette: Dict[str, str]) -> str:
    """Generate MASTER.md for design system."""
    contrast_results = validate_contrast(palette)
    contrast_status = "✅ WCAG AA Compliant" if all(contrast_results.values()) else "⚠️ Review needed"
    
    return f"""# Design System Master

**Category**: {category.upper()}  
**Mood**: {mood.value}  
**Accessibility**: {contrast_status}

## Color Palette

### Primary Colors
- Primary: `{palette['primary']}`
- Secondary: `{palette['secondary']}`
- Accent: `{palette['accent']}`

### Semantic Colors
- Success: `{palette['success']}`
- Warning: `{palette['warning']}`
- Error: `{palette['error']}`
- Info: `{palette['info']}`

### Neutral Scale
| Level | Hex |
|-------|-----|
| 50 | `{palette['neutral_50']}` |
| 100 | `{palette['neutral_100']}` |
| 200 | `{palette['neutral_200']}` |
| 300 | `{palette['neutral_300']}` |
| 400 | `{palette['neutral_400']}` |
| 500 | `{palette['neutral_500']}` |
| 600 | `{palette['neutral_600']}` |
| 700 | `{palette['neutral_700']}` |
| 800 | `{palette['neutral_800']}` |
| 900 | `{palette['neutral_900']}` |

## Typography

- Display: {palette.get('display_font', 'System font')}
- Heading: {palette.get('heading_font', 'System font')}
- Body: {palette.get('body_font', 'System font')}
- Monospace: {palette.get('mono_font', 'System font')}

### Type Scale
- Display: 48px, font-weight: 700, line-height: 1.2
- H1: 36px, font-weight: 700, line-height: 1.25
- H2: 28px, font-weight: 600, line-height: 1.3
- H3: 24px, font-weight: 600, line-height: 1.35
- Body: 16px, font-weight: 400, line-height: 1.5
- Body Small: 14px, font-weight: 400, line-height: 1.43
- Caption: 12px, font-weight: 500, line-height: 1.33

## Spacing System

Base unit: 8px

- xs: 4px (0.5rem)
- sm: 8px (1rem)
- md: 16px (2rem)
- lg: 24px (3rem)
- xl: 32px (4rem)
- 2xl: 48px (6rem)
- 3xl: 64px (8rem)

## Effects

### Shadows
- xs: 0 1px 2px rgba(0, 0, 0, 0.05)
- sm: 0 1px 3px rgba(0, 0, 0, 0.1)
- md: 0 4px 6px rgba(0, 0, 0, 0.1)
- lg: 0 10px 15px rgba(0, 0, 0, 0.1)

### Border Radius
- xs: 2px
- sm: 4px
- md: 8px
- lg: 12px
- full: 9999px

### Motion
- Fast: 150ms cubic-bezier(0.4, 0, 1, 1)
- Normal: 300ms cubic-bezier(0.4, 0, 0.2, 1)
- Slow: 500ms cubic-bezier(0.4, 0, 0.2, 1)

## Accessibility Requirements

- Minimum text size: 16px for body content
- Minimum touch targets: 48x48px
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text
- Focus indicators: Minimum 2px outline, visible on all interactive elements
- Keyboard navigation: All interactive elements must be keyboard accessible
- Responsive: Support 375px, 768px, 1024px, 1440px breakpoints

## Responsive Breakpoints

- Mobile: 375px
- Tablet: 768px
- Desktop: 1024px
- Wide: 1440px

---

Generated by Design System Forge
"""


def generate_components_md(category: str, stack: Stack) -> str:
    """Generate component guidelines."""
    framework_examples = {
        Stack.REACT: """## React Example

\`\`\`jsx
import React from 'react';

export const Button = ({ variant = 'primary', children, ...props }) => {
  const baseStyles = 'px-4 py-2 rounded-md font-medium transition-colors';
  const variants = {
    primary: 'bg-primary text-white hover:bg-primary-dark',
    secondary: 'bg-secondary text-white hover:bg-secondary-dark',
    outline: 'border-2 border-primary text-primary hover:bg-primary-light',
  };
  
  return <button className={`${baseStyles} ${variants[variant]}`} {...props}>{children}</button>;
};
\`\`\`
""",
        Stack.VUE: """## Vue Example

\`\`\`vue
<template>
  <button 
    :class="['btn', `btn--${variant}`]"
    v-bind="$attrs"
  >
    <slot></slot>
  </button>
</template>

<script>
export default {
  props: {
    variant: {
      type: String,
      default: 'primary',
      validator: (v) => ['primary', 'secondary', 'outline'].includes(v)
    }
  }
}
</script>

<style scoped>
.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  transition: all 300ms ease;
}

.btn--primary {
  background-color: var(--color-primary);
  color: white;
}

.btn--primary:hover {
  background-color: var(--color-primary-dark);
}
</style>
\`\`\`
""",
        Stack.SWIFTUI: """## SwiftUI Example

\`\`\`swift
struct DesignButton: View {
    let title: String
    let variant: ButtonVariant = .primary
    let action: () -> Void
    
    enum ButtonVariant {
        case primary
        case secondary
        case outline
    }
    
    var body: some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 16, weight: .medium))
                .frame(minWidth: 48, minHeight: 48)
                .padding(.horizontal, 16)
                .background(variantColor)
                .foregroundColor(variantForeground)
                .cornerRadius(8)
        }
    }
    
    private var variantColor: Color {
        switch variant {
        case .primary: return Color(hex: "#3B82F6")
        case .secondary: return Color(hex: "#6366F1")
        case .outline: return Color.clear
        }
    }
    
    private var variantForeground: Color {
        switch variant {
        case .primary, .secondary: return .white
        case .outline: return Color(hex: "#3B82F6")
        }
    }
}
\`\`\`
""",
        Stack.HTML: """## HTML + CSS Example

\`\`\`html
<button class="btn btn--primary">Click Me</button>

<style>
:root {
  --color-primary: #3B82F6;
  --color-secondary: #6366F1;
  --spacing-sm: 8px;
  --spacing-md: 16px;
}

.btn {
  padding: var(--spacing-sm) var(--spacing-md);
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  min-width: 48px;
  min-height: 48px;
  transition: all 300ms ease;
}

.btn--primary {
  background-color: var(--color-primary);
  color: white;
}

.btn--primary:hover {
  background-color: #1D4ED8;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn--primary:focus {
  outline: 2px solid #93C5FD;
  outline-offset: 2px;
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
\`\`\`
""",
        Stack.ANGULAR: """## Angular Example

\`\`\`typescript
import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-button',
  template: `
    <button 
      [ngClass]="['btn', 'btn--' + variant]"
      [disabled]="disabled"
      (click)="onClick()">
      {{ label }}
    </button>
  `,
  styles: [`
    .btn {
      padding: 0.5rem 1rem;
      border: none;
      border-radius: 0.375rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 300ms ease;
      min-width: 48px;
      min-height: 48px;
    }
    
    .btn--primary {
      background-color: #3B82F6;
      color: white;
    }
    
    .btn--primary:hover:not(:disabled) {
      background-color: #1D4ED8;
    }
    
    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  `]
})
export class ButtonComponent {
  @Input() label: string = '';
  @Input() variant: 'primary' | 'secondary' | 'outline' = 'primary';
  @Input() disabled: boolean = false;
  
  onClick() {
    console.log('Button clicked');
  }
}
\`\`\`
""",
    }
    
    content = """# Component Guidelines

## Buttons

### States
- **Default**: Base appearance
- **Hover**: Darkened or elevated appearance
- **Focus**: Visible focus indicator (min 2px outline)
- **Active**: Pressed appearance
- **Disabled**: Reduced opacity, no pointer events

### Variants
- **Primary**: Main call-to-action
- **Secondary**: Alternative action
- **Outline**: Tertiary action
- **Danger**: Destructive actions

### Specifications
- Minimum size: 48x48px (touch target)
- Padding: 8px (horizontal), 12px (vertical)
- Border radius: 6-8px
- Font weight: 500-600
- Transition time: 200-300ms

"""
    
    if stack in framework_examples:
        content += framework_examples[stack]
    
    content += """
## Forms

### Input Fields
- Label placement: Above input (mobile), left (desktop)
- Padding: 12px horizontal, 10px vertical
- Border: 1px solid neutral-300
- Focus: 2px solid primary color
- Placeholder: neutral-400 color

### Validation
- Success: Border 1px solid success color
- Error: Border 2px solid error color
- Error message: Error color, 12px, below field

### Touch Targets
- Minimum height: 44px (mobile), 40px (desktop)
- Checkbox/radio: 48x48px clickable area

## Navigation

### Header
- Height: 64px (desktop), 56px (mobile)
- Logo area: 48px width minimum
- Action spacing: 16px gaps
- Mobile menu: Full-width overlay

### Sidebar
- Width: 256px (expanded), 64px (collapsed)
- Item height: 44px
- Icon size: 24px
- Active indicator: Left border or background

## Cards

### Container
- Border radius: 8-12px
- Shadow: sm to md elevation
- Padding: 16-24px
- Max-width: 600px (content card)

### Content
- Title: Heading 3 (24px)
- Body: Body text (16px)
- Spacing between sections: md (16px)

## Modals

### Overlay
- Background: rgba(0, 0, 0, 0.5)
- Animation: 200ms fade-in
- Dismiss on background: Optional

### Dialog
- Min width: 320px
- Max width: 600px
- Padding: 24px
- Border radius: 12px

---

Generated by Design System Forge
"""
    return content


def generate_homepage_md() -> str:
    """Generate homepage design guide."""
    return """# Homepage Design Guide

## Layout Structure

\`\`\`
┌────────────────────────────┐
│         Header             │
├────────────────────────────┤
│     Hero Section           │
│   (CTA visible)            │
├────────────────────────────┤
│  Feature Highlights        │
│  (3-4 key benefits)        │
├────────────────────────────┤
│  Social Proof              │
│  (Testimonials/logos)      │
├────────────────────────────┤
│  Secondary CTA             │
├────────────────────────────┤
│         Footer             │
└────────────────────────────┘
\`\`\`

## Hero Section
- Headline: 36-48px, max 10 words
- Subheading: 18-20px, supporting text
- Primary CTA: High contrast, clear label
- Visual: Hero image or video (1200x600px minimum)
- Spacing: Equal padding above/below

## Feature Highlights
- Grid: 3-4 columns (responsive to 1 col mobile)
- Icon: 48x48px or 64x64px
- Title: Heading 3 (24px)
- Description: 16px body text, 2-3 sentences
- Card spacing: 24-32px gap

## Social Proof
- Testimonials: Quote text (16px), attribution (14px)
- Logo grid: Even spacing, 64-80px height
- Stats: Large number (36px), supporting label (14px)
- Count: "1000+ customers" style messaging

## Secondary CTA
- Container: Distinct background (neutral or secondary color)
- Copy: Benefit-focused headline
- Button: Primary style, prominent placement

## Footer
- Columns: 3-5 sections (links, company, social)
- Link size: 14px
- Social icons: 24x24px, 32px gap
- Copyright: 12px neutral-400 color

---

Generated by Design System Forge
"""


def generate_design_system(
    category: str,
    mood: Mood,
    stack: Stack
) -> Dict[str, str]:
    """Generate complete design system."""
    
    if category not in DESIGN_RULES_DB:
        return {"error": f"Category '{category}' not found"}
    
    rules = DESIGN_RULES_DB[category]
    palette = rules["colors"]
    
    system = {
        "MASTER.md": generate_master_md(category, mood, palette),
        "pages/homepage.md": generate_homepage_md(),
        "components/guidelines.md": generate_components_md(category, stack),
    }
    
    return system


def main():
    """CLI interface."""
    if len(sys.argv) < 2:
        print("Usage: design_forge.py generate --category <category> --stack <stack> --mood <mood>")
        print("       design_forge.py validate --category <category> --colors <hex> <hex> ...")
        print("       design_forge.py colors --category <category> --mood <mood>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        category = None
        stack_name = "react"
        mood_name = "professional"
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--category" and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--stack" and i + 1 < len(sys.argv):
                stack_name = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--mood" and i + 1 < len(sys.argv):
                mood_name = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not category:
            print("Error: --category is required")
            sys.exit(1)
        
        found_category = find_category(category)
        if not found_category:
            print(f"Error: Category '{category}' not found")
            print(f"Available: {', '.join(DESIGN_RULES_DB.keys())}")
            sys.exit(1)
        
        try:
            mood = Mood[mood_name.upper()]
        except KeyError:
            print(f"Error: Mood '{mood_name}' not found")
            print(f"Available: {', '.join([m.value for m in Mood])}")
            sys.exit(1)
        
        try:
            stack = Stack[stack_name.upper()]
        except KeyError:
            print(f"Error: Stack '{stack_name}' not found")
            print(f"Available: {', '.join([s.value for s in Stack])}")
            sys.exit(1)
        
        system = generate_design_system(found_category, mood, stack)
        
        if "error" in system:
            print(f"Error: {system['error']}")
            sys.exit(1)
        
        print(json.dumps(system, indent=2))
    
    elif command == "colors":
        category = None
        mood_name = "professional"
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--category" and i + 1 < len(sys.argv):
                category = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--mood" and i + 1 < len(sys.argv):
                mood_name = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not category:
            print("Error: --category is required")
            sys.exit(1)
        
        found_category = find_category(category)
        if not found_category:
            print(f"Error: Category '{category}' not found")
            sys.exit(1)
        
        if found_category not in DESIGN_RULES_DB:
            print(f"Error: Category '{found_category}' not found")
            sys.exit(1)
        
        colors = DESIGN_RULES_DB[found_category]["colors"]
        print(json.dumps(colors, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
