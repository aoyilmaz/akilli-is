## 2025-10-26 - [Enhance Action Buttons Accessibility]
**Learning:** Icon-only buttons often lack accessible names, making them invisible to screen readers. Tooltips can double as accessible names if no better label exists.
**Action:** Automatically set `accessibleName` from `toolTip` for icon-only buttons in the base component to ensure coverage across the entire app. Also added `PointingHandCursor` for better affordance.
