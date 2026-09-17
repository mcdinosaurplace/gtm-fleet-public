# Notion Enhanced Markdown Syntax Reference

This document defines the correct markdown syntax for creating Notion pages via
the Notion MCP `notion-create-pages` and `notion-update-page` tools. It is the
canonical reference for all agents and skills that produce Notion content.

**Why this exists**: Notion uses a proprietary extended markdown format that
differs significantly from GitHub-Flavored Markdown (GFM) and CommonMark. LLMs
will default to GFM patterns (blockquote callouts, `<details><summary>` toggles)
unless explicitly instructed otherwise. Those patterns render as broken raw
markup in Notion.

---

## Critical Rules

1. **Nesting uses TAB characters**, not spaces. Every level of nesting inside
   a toggle, callout, or column must use one additional tab character.
2. **Never use `>` blockquote syntax** for callouts. Notion does not support
   `> [!icon]` or `> [!NOTE]` syntax.
3. **Never use `<details><summary>` HTML** for toggles. Notion does not render
   standard HTML toggle elements.
4. **Never use `---` horizontal rules** inside toggled content. They break
   the toggle nesting.
5. **Content inside tags must be on the next line**, indented one tab deeper
   than the tag itself.

---

## Callouts

Callouts are colored boxes with an icon. They use XML-style tags.

### Syntax

```
<callout icon="🤖" color="purple_bg">
	Content goes here, indented one tab.
	**Bold** and [links](url) work normally inside callouts.
	- Bullet lists work too
	- Each item indented at the same level
</callout>
```

### Available colors

`default` (no color attribute needed), `gray_bg`, `brown_bg`, `orange_bg`,
`yellow_bg`, `green_bg`, `blue_bg`, `purple_bg`, `pink_bg`, `red_bg`

### Wrong (do NOT use)

```
> [!🤖] {color="purple_bg"}        ← GFM callout syntax, NOT supported
> Content in blockquote             ← renders as raw text in Notion

> 🤖 **Summary**                   ← plain blockquote, NOT a callout
```

---

## Toggles

Toggles are collapsible sections. They are created by adding `{toggle="true"}`
to any heading.

### Syntax

```
## Section Name {toggle="true"}
	Content inside the toggle, indented one tab.
	More content at the same indent level.
	<callout icon="💡">
		Callouts can nest inside toggles.
	</callout>
```

### Toggle headings inside callouts

```
<callout icon="☑️" color="gray_bg">
	### Tasks {toggle="true"}
		- Item 1
		- Item 2
	### More Tasks {toggle="true"}
		- Item 3
</callout>
```

### Wrong (do NOT use)

```
<details>                           ← HTML toggle, NOT supported
<summary>Section Name</summary>
Content
</details>

<details open>                      ← also NOT supported
<summary>                           ← also NOT supported
```

---

## Columns

Columns create a side-by-side layout. They use XML-style tags.

### Syntax

```
<columns>
	<column>
		Content in left column, indented two tabs from root.
		<callout icon="📋">
			Callouts work inside columns.
		</callout>
	</column>
	<column>
		Content in right column.
	</column>
</columns>
```

Up to 5 columns are supported. Each `<column>` block becomes one column.

---

## Empty Blocks

Use `<empty-block/>` to add vertical spacing. This is useful inside callouts
and columns to prevent Notion from collapsing whitespace.

```
<callout icon="🗓️" color="green_bg">
	#### Mon 3/23
	No meetings.
	<empty-block/>
</callout>
```

---

## Checkboxes (To-Do Items)

```
- [ ] Unchecked item
- [x] Checked item
```

These work inside callouts:

```
<callout icon="💬">
	- [ ] **Person (Slack DM)** — Description of what they need.
</callout>
```

---

## Inline Formatting

Standard markdown inline formatting works everywhere:

- `**bold**` → **bold**
- `*italic*` → *italic*
- `~~strikethrough~~` → ~~strikethrough~~
- `` `code` `` → `code`
- `[link text](url)` → clickable link
- `<br>` → line break within a block (use sparingly)

---

## Headings with Attributes

Headings can carry attributes in curly braces:

```
# Heading 1 {toggle="true"}
## Heading 2 {toggle="true"}
### Heading 3 {toggle="true"}
#### Heading 4 {toggle="true"}

# Colored Heading {color="blue"}
```

Multiple attributes:

```
#### Person Name {toggle="true"}
```

---

## Complete Nesting Example

This example shows all major patterns combined correctly. Note the tab-based
indentation at every level.

```
# Page Title {toggle="true"}
	<callout icon="🤖" color="purple_bg">
		## Summary
		Two to three sentences of overview text.
	</callout>
	<columns>
		<column>
			<callout icon="📋">
				## Left Column Header
				1. First item
				2. Second item
			</callout>
		</column>
		<column>
			<callout icon="💡">
				## Right Column Header
				- Bullet point one
				- Bullet point two
			</callout>
		</column>
	</columns>
	<callout icon="🚨" color="red_bg">
		## Risks {toggle="true"}
			- Risk one with **bold emphasis**
			- Risk two with [a link](https://example.com)
	</callout>
	## Section with Individual Callouts {toggle="true"}
		<callout icon="💬">
			- [ ] **Person (Source)** — Description of action needed.
		</callout>
		<callout icon="✉️">
			- [ ] **Another Person (Email)** — Another action item.
		</callout>
	## Collaboration Radar {toggle="true"}
		<columns>
			<column>
				<callout icon="👤">
					#### **Person Name** {toggle="true"}
						Context about what you're working on together.
				</callout>
			</column>
			<column>
				<callout icon="👤">
					#### **Other Person** {toggle="true"}
						Context about this collaborator.
				</callout>
			</column>
		</columns>
	## Tasks {toggle="true"}
		<callout icon="☑️" color="gray_bg">
			### 🔎 In Review (1) {toggle="true"}
				- [ISSUE-123](https://linear.app/...) — Issue title
		</callout>
		<callout icon="☑️" color="purple_bg">
			### 🔥 High Priority (3) {toggle="true"}
				- [ISSUE-456](https://linear.app/...) — Issue title
				- [ISSUE-789](https://linear.app/...) — Issue title
			### 🎧 Medium Priority (2) {toggle="true"}
				- [ISSUE-012](https://linear.app/...) — Issue title
			### ⬇️ Low Priority (1) {toggle="true"}
				- [ISSUE-345](https://linear.app/...) — Issue title
				<empty-block/>
		</callout>
		<empty-block/>
```

---

## Common Mistakes and Fixes

| Mistake | Fix |
|---------|-----|
| Using `>` blockquotes for callouts | Use `<callout icon="X">` tags |
| Using `<details><summary>` for toggles | Use `{toggle="true"}` on headings |
| Using spaces for indentation | Use tab characters |
| Putting `---` dividers inside toggles | Remove them; use `<empty-block/>` for spacing |
| Wrapping callout content in `>` prefixes | Indent with tabs instead |
| Nesting `<details>` inside `<callout>` | Use `{toggle="true"}` on headings inside callouts |
| Using `> [!NOTE]` or `> [!TIP]` syntax | Use `<callout icon="ℹ️">` |

---

## Reference

This syntax was validated against a hand-corrected Notion page:
`https://www.notion.so/{{NOTION_PAGE_ID}}`
