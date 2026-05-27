# Semantic Token Taxonomy Reference

Use this taxonomy unless the user or codebase strongly indicates another structure.

```text
primitive
  color
  space
  size
  radius
  border-width
  stroke-style
  opacity
  shadow
  blur
  font
  line-height
  letter-spacing
  duration
  easing
  z-index
  breakpoint
  aspect-ratio

semantic
  color
    fg
    bg
    border
    ring
    icon
    overlay
    shadow
    data
  typography
    display
    heading
    title
    body
    label
    caption
    code
    data
  font
    family
    weight
  space
    inset
    inline
    stack
    gap
    section
    layout
  size
    control
    icon
    avatar
    media
    touch-target
    container
  layout
    breakpoint
    container
    grid
    column
    gutter
    panel
    sidebar
  radius
    surface
    control
    media
    overlay
    pill
  border
    default
    muted
    strong
    focus
    feedback
  elevation
    surface
    overlay
    popover
    modal
  effect
    shadow
    opacity
    blur
    backdrop
  motion
    duration
    easing
    transition
  layer
    base
    raised
    sticky
    popover
    modal
    toast
    tooltip
  interaction
    cursor
    focus
    hit-area
    selection
    drag

component
  button
  input
  select
  checkbox
  radio
  switch
  textarea
  card
  dialog
  popover
  tooltip
  toast
  table
  tabs
  navigation
  menu
  badge
  avatar
  skeleton
  progress
```

## Naming grammar

```text
<layer>.<domain>.<subdomain>.<role>.<variant>.<state>.<scale>
```

Examples:

```text
semantic.color.fg.default
semantic.color.bg.surface.elevated
semantic.color.border.focus
semantic.space.inset.md
semantic.typography.body.md
semantic.motion.transition.fast
component.button.primary.bg.hover
component.input.border.invalid.focus
```

## Design rules

- Product code should consume `semantic.*` and `component.*`, not `primitive.*`.
- Primitive values should be implementation details.
- Component tokens should generally alias semantic tokens.
- Theme overrides should reuse the same semantic paths.
- Prefer logical layout names: `inline`, `block`, `start`, `end`, `inset`, `stack`, `gap`.
- Avoid physical names: `left`, `right`, `top`, `bottom`, unless intentionally physical.
- Use state tokens only when the state has a distinct design decision.
