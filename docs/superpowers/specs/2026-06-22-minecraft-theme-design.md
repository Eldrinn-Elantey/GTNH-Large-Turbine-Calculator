# Minecraft Theme — Design Spec

## Summary

Replace the current dark developer-style theme with an authentic Minecraft GUI aesthetic. The calculator should feel like a native in-game interface panel.

## Design Decisions

| Topic | Choice | Rationale |
|---|---|---|
| Color palette | Classic grey GUI | `#c6c6c6` bg, `#8b8b8b` panels, `#373737` dark — matches Minecraft inventory |
| Font | Press Start 2P (Google Fonts) | Maximum Minecraft authenticity; size bumped to 10-11px for readability |
| Border style | Inventory raised/sunken | White top/left + dark bottom/right border, no border-radius anywhere |
| Sidebar bg | `#555555` | Slightly darker panel to distinguish from main area |

## Color Tokens

```css
--mc-bg:      #c6c6c6;   /* main background */
--mc-panel:   #8b8b8b;   /* cards, raised panels */
--mc-sidebar: #555555;   /* sidebar background */
--mc-dark:    #373737;   /* border shadow side, inputs bg */
--mc-light:   #ffffff;   /* border highlight side */
--mc-text:    #ffffff;   /* primary text (on dark panels) */
--mc-text-bg: #1a1a1a;   /* text on light bg */
--mc-green:   #7ec850;   /* positive values */
--mc-yellow:  #f6c90e;   /* warning values */
--mc-red:     #e05c5c;   /* bad values */
```

## Border Conventions

- **Raised** (panels, buttons): `border-top/left: 3px solid #fff`, `border-bottom/right: 3px solid #373737`
- **Sunken** (inputs, active selection): `border-top/left: 3px solid #373737`, `border-right/bottom: 3px solid #fff`
- **No `border-radius` anywhere** — zero, always
- Button `:active` state: flip raised to sunken

## Typography

- Font: `'Press Start 2P', monospace` loaded from Google Fonts
- Base size: `10px` (up from current 13px system-ui — smaller font needs larger px)
- Text shadow on dark panels: `1px 1px #000`
- Labels above inputs: `7px`, uppercase, muted color `#aaa`
- Result values colored by status: green / yellow / red

## Layout

Current layout (sidebar + main) stays unchanged. Only visual treatment changes:
- Sidebar: darker bg, nav items with active state using raised border
- Cards/panels: raised border, grey fill
- Inputs: sunken border, dark fill (`#373737`) with white text
- Selects: same treatment as inputs
- Buttons: full-width raised, flip on `:active`

## Scope

Only `web/css/style.css` and `web/css/components.css` change. No JS, no HTML structure changes. The mockup file at `.superpowers/brainstorm/19-1782096976/content/full-mockup.html` is the visual reference.
