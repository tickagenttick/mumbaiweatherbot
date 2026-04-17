# Language Indicator — Design Reference

Interactive reference for the top-right language tag used between stitched
videos of different languages. Shows a minimalist, Apple-style indicator that
briefly pulses when the language changes, then settles.

## Files

- `index.html` — **Style 05 variations** (8 riffs on blink frequency, persistence, and color). Default landing page.
- `all-styles.html` — The original 6-style overview (frosted glass, minimal text, solid badge, flag + label, thin outline, Dynamic Island).
- `thumb.jpg` — A frame from the showreel used as the mock video background.

Open `index.html` locally by double-clicking it, or deploy the folder as a
static site.

## Deploying to Render

1. Create a new **Static Site** on Render.
2. Point it at a repo (or use Render's "Deploy from local directory" flow) containing the files in this folder.
3. Leave the **Build Command** blank.
4. Set the **Publish Directory** to `.` (the folder root).

Render will serve `index.html` at the root URL. `all-styles.html` will be
reachable at `/all-styles.html`.

### Optional `render.yaml`

If you want infra-as-code, drop this at the repo root:

```yaml
services:
  - type: web
    name: language-indicator-demo
    runtime: static
    buildCommand: ""
    staticPublishPath: .
```

## Interacting with the demo

- **Simulate Language Change** — triggers all indicators to blink simultaneously.
- Individual language buttons (Marathi / Tamil / Telugu / Thukara ke Mera Pyaar) let you see how each variant handles specific labels, including the longer title (which auto-switches to sentence case to avoid a cramped tag).

## Spec summary (resting state)

- Border: `1px solid rgba(255,255,255,.45)`
- Background: `rgba(0,0,0,.22)` with `backdrop-filter: blur(8px)`
- Font: 11px, uppercase, letter-spacing `0.12em` (short labels)
- Long labels: 11.5px, sentence case, letter-spacing `0.04em`

Animation durations range from 1.2s (fast double blink) to 3.2s (persistent
afterglow). See the comparison table at the bottom of `index.html` for the
full matrix.
