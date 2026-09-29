# Tailwind CSS Customization

Custom design tokens, utilities, variants and plugins in **Tailwind CSS v4**, where
configuration lives in CSS. There is no `tailwind.config.js` in a v4 project: tokens go in
`@theme`, source files are detected automatically, plugins load with `@plugin`, and dark
mode is a custom variant. Projects that still carry a JavaScript config are on v3 or use
the `@config` compatibility directive — treat them as legacy and do not mix the two
conventions in one project.

Theme tokens of shadcn/ui and the component layer: `references/shadcn-theming.md`.
Utility catalogue: `references/tailwind-utilities.md`. Breakpoints and container queries:
`references/tailwind-responsive.md`.

Verified against the Tailwind CSS v4 release notes
(https://tailwindcss.com/blog/tailwindcss-v4) and the directives reference
(https://tailwindcss.com/docs/functions-and-directives) on 2026-09-03. Treat version
numbers as indicative — check the project itself.

## @theme Directive

Modern approach to customize Tailwind using CSS:

```css
@import "tailwindcss";

@theme {
  /* Custom colors */
  --color-brand-50: oklch(0.97 0.02 264);
  --color-brand-500: oklch(0.55 0.22 264);
  --color-brand-900: oklch(0.25 0.15 264);

  /* Custom fonts */
  --font-display: "Satoshi", "Inter", sans-serif;
  --font-body: "Inter", system-ui, sans-serif;

  /* Custom spacing */
  --spacing-18: calc(var(--spacing) * 18);
  --spacing-navbar: 4.5rem;

  /* Custom breakpoints */
  --breakpoint-3xl: 120rem;
  --breakpoint-tablet: 48rem;

  /* Custom shadows */
  --shadow-glow: 0 0 20px rgba(139, 92, 246, 0.3);

  /* Custom radius */
  --radius-large: 1.5rem;
}
```

**Usage:**
```html
<div class="bg-brand-500 font-display shadow-glow rounded-large">
  Custom themed element
</div>

<div class="tablet:grid-cols-2 3xl:grid-cols-6">
  Custom breakpoints
</div>
```

## Color Customization

### Custom Color Palette

```css
@theme {
  /* Full color scale */
  --color-primary-50: oklch(0.98 0.02 250);
  --color-primary-100: oklch(0.95 0.05 250);
  --color-primary-200: oklch(0.90 0.10 250);
  --color-primary-300: oklch(0.85 0.15 250);
  --color-primary-400: oklch(0.75 0.18 250);
  --color-primary-500: oklch(0.65 0.22 250);
  --color-primary-600: oklch(0.55 0.22 250);
  --color-primary-700: oklch(0.45 0.20 250);
  --color-primary-800: oklch(0.35 0.18 250);
  --color-primary-900: oklch(0.25 0.15 250);
  --color-primary-950: oklch(0.15 0.10 250);
}
```

### Semantic Colors

```css
@theme {
  --color-success: oklch(0.65 0.18 145);
  --color-warning: oklch(0.75 0.15 85);
  --color-error: oklch(0.60 0.22 25);
  --color-info: oklch(0.65 0.18 240);
}
```

```html
<div class="bg-success text-white">Success message</div>
<div class="border-error">Error state</div>
```

## Typography Customization

### Custom Fonts

```css
@theme {
  --font-sans: "Inter", system-ui, sans-serif;
  --font-serif: "Merriweather", Georgia, serif;
  --font-mono: "JetBrains Mono", Consolas, monospace;
  --font-display: "Playfair Display", serif;
}
```

```html
<h1 class="font-display">Display heading</h1>
<p class="font-sans">Body text</p>
<code class="font-mono">Code block</code>
```

### Custom Font Sizes

```css
@theme {
  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  --font-size-4xl: 2.25rem;
  --font-size-5xl: 3rem;
  --font-size-jumbo: 4rem;
}
```

## Spacing Customization

```css
@theme {
  /* Add custom spacing values */
  --spacing-13: calc(var(--spacing) * 13);
  --spacing-15: calc(var(--spacing) * 15);
  --spacing-18: calc(var(--spacing) * 18);

  /* Named spacing */
  --spacing-header: 4rem;
  --spacing-footer: 3rem;
  --spacing-section: 6rem;
}
```

```html
<div class="p-18">Custom padding</div>
<section class="py-section">Section spacing</section>
```

## Custom Utilities

Create reusable utility classes:

```css
@utility content-auto {
  content-visibility: auto;
}

@utility tab-* {
  tab-size: var(--tab-size-*);
}

@utility glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
}
```

**Usage:**
```html
<div class="content-auto">Optimized rendering</div>
<pre class="tab-4">Code with 4-space tabs</pre>
<div class="glass">Glassmorphism effect</div>
```

## Custom Variants

Create custom state variants:

```css
@custom-variant theme-midnight (&:where([data-theme="midnight"] *));
@custom-variant aria-checked (&[aria-checked="true"]);
@custom-variant required (&:required);
```

**Usage:**
```html
<div data-theme="midnight">
  <div class="theme-midnight:bg-navy-900">
    Applies in midnight theme
  </div>
</div>

<input class="required:border-red-500" required />
```

## Layer Organization

Organize CSS into layers:

```css
@layer base {
  h1 {
    @apply text-4xl font-bold tracking-tight;
  }

  h2 {
    @apply text-3xl font-semibold;
  }

  a {
    @apply text-blue-600 hover:text-blue-700 underline-offset-4 hover:underline;
  }

  body {
    @apply bg-background text-foreground antialiased;
  }
}

@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }

  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-900 hover:bg-gray-300;
  }

  .card {
    @apply bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow;
  }

  .input {
    @apply w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent;
  }
}

@layer utilities {
  .text-balance {
    text-wrap: balance;
  }

  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }
  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }
}
```

## @apply Directive

Extract repeated utility patterns:

```css
.btn-primary {
  @apply bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-semibold px-6 py-3 rounded-lg shadow-md hover:shadow-lg transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-blue-300;
}

.input-field {
  @apply w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed;
}

.section-container {
  @apply container mx-auto px-4 sm:px-6 lg:px-8 max-w-7xl;
}
```

**Usage:**
```html
<button class="btn-primary">Click me</button>
<input class="input-field" />
<div class="section-container">Content</div>
```

## Plugins

### Official plugins

Container queries are part of the v4 core — the separate `@tailwindcss/container-queries`
plugin is no longer installed. Use the `@container` class with `@sm:` / `@lg:` variants
(`references/tailwind-responsive.md`).

```bash
npm install -D @tailwindcss/typography @tailwindcss/forms
```

Plugins are loaded from CSS, next to the import:

```css
@import "tailwindcss";
@plugin "@tailwindcss/typography";
@plugin "@tailwindcss/forms";
```

**Typography plugin:**
```html
<article class="prose lg:prose-xl">
  <h1>Styled article</h1>
  <p>Automatically styled prose content</p>
</article>
```

**Forms plugin:**
```html
<!-- Automatically styled form elements -->
<input type="text" />
<select></select>
<textarea></textarea>
```

### Custom utilities and variants without a plugin

Most of what a v3 plugin did is now a CSS directive, so no JavaScript file is needed:

```css
@import "tailwindcss";

/* utility usable with variants: hover:text-shadow, lg:text-shadow-lg */
@utility text-shadow {
  text-shadow: 2px 2px 4px --alpha(var(--color-black) / 10%);
}
@utility text-shadow-lg {
  text-shadow: 4px 4px 8px --alpha(var(--color-black) / 20%);
}

/* custom variant */
@custom-variant pointer-coarse (@media (pointer: coarse));
```

### JavaScript plugin, when it is unavoidable

A plugin written against the v3 API still loads through `@plugin`, pointing at a local
file. The file itself is a module, so it uses `import`, not `require` — `require` in a file
with `export default` does not run at all:

```js
// plugins/text-shadow.js
import plugin from "tailwindcss/plugin"

export default plugin(({ addUtilities }) => {
  addUtilities({
    ".text-shadow": { textShadow: "2px 2px 4px rgb(0 0 0 / 10%)" },
  })
})
```

```css
@plugin "./plugins/text-shadow.js";
```

Prefer `@utility` and `@custom-variant`; reach for a JavaScript plugin only when the
generated utilities depend on data computed at build time.

## Complete stylesheet example

Everything a v3 `tailwind.config.ts` carried — palette, fonts, spacing, radius, keyframes,
dark mode, plugins — expressed as one CSS file. This is the whole configuration of a v4
project; there is no second file to keep in sync.

```css
/* src/index.css */
@import "tailwindcss";
@plugin "tw-animate-css";

/* dark mode driven by a class on <html>, not by @media */
@custom-variant dark (&:is(.dark *));

:root {
  --radius: 0.625rem;
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  --primary: oklch(0.205 0 0);
  --primary-foreground: oklch(0.985 0 0);
  --border: oklch(0.922 0 0);
}

.dark {
  --background: oklch(0.145 0 0);
  --foreground: oklch(0.985 0 0);
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --border: oklch(1 0 0 / 10%);
}

@theme inline {
  /* semantic colours follow the variables above, also after a theme switch */
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-border: var(--border);

  /* fixed brand scale */
  --color-brand-50: oklch(0.97 0.02 250);
  --color-brand-500: oklch(0.62 0.19 250);
  --color-brand-900: oklch(0.35 0.12 250);

  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --font-display: "Playfair Display", ui-serif, serif;

  --spacing-18: 4.5rem;
  --spacing-88: 22rem;

  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);

  --breakpoint-3xl: 120rem;

  --animate-slide-in: slide-in 0.5s ease-out;
}

@keyframes slide-in {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(0); }
}
```

Notes on what disappeared from the v3 config:

| v3 config key | v4 equivalent |
|---|---|
| `content: [...]` | nothing — source files are detected automatically; add `@source "..."` only for files outside the project tree, e.g. a library in `node_modules` |
| `darkMode: ["class"]` | `@custom-variant dark (&:is(.dark *));` |
| `theme.extend.colors` | `--color-*` tokens in `@theme` (use `@theme inline` when the token points at another variable) |
| `theme.extend.fontFamily` | `--font-*` tokens |
| `theme.extend.spacing` | `--spacing-*` tokens |
| `theme.extend.borderRadius` | `--radius-*` tokens |
| `theme.extend.screens` | `--breakpoint-*` tokens |
| `theme.extend.animation` | `--animate-*` tokens plus a plain `@keyframes` rule |
| `plugins: [require(...)]` | `@plugin "..."` |
| `safelist` | `@source inline("bg-red-500 bg-green-500")` |
| `container: { center, padding }` | a `@utility container` of your own — the v3 `container` options are gone |

## Dark mode

Dark mode is a variant declared in CSS. The class form is the default in shadcn/ui,
because it allows a user-visible switch:

```css
@custom-variant dark (&:is(.dark *));
```

```html
<html class="dark">
  <div class="bg-white dark:bg-gray-900">Responds to the .dark class</div>
</html>
```

To follow the system setting instead, declare the variant against the media query and
drop the class:

```css
@custom-variant dark (@media (prefers-color-scheme: dark));
```

## Source detection and safelisting

Tailwind v4 scans the project by itself: it walks the tree, skips anything in
`.gitignore` and skips binary files. Two cases still need a directive:

```css
/* a package outside the scanned tree */
@source "../node_modules/@my-company/ui-lib";

/* classes assembled at runtime and therefore absent from the source */
@source inline("bg-red-500 bg-green-500 bg-blue-500");
```

A hand-written `content` array is a v3 relic; in v4 it has no effect unless loaded through
`@config`.

## Best Practices

1. **Use @theme for simple customizations**: Prefer CSS-based customization
2. **Extract components sparingly**: Use @apply only for truly repeated patterns
3. **Leverage design tokens**: Define custom tokens in @theme
4. **Layer organization**: Keep base, components, and utilities separate
5. **Directives before plugins**: `@utility` and `@custom-variant` cover most of what
   a v3 JavaScript plugin did; load a plugin only for build-time computed output
6. **Test dark mode**: Ensure custom colors work in both themes
7. **Document custom utilities**: Add comments explaining custom classes
8. **Semantic naming**: Use descriptive names (primary not blue)
