---
name: content-ui
description: Implement ContentListScreen, ArticleScreen, and rich text display for the content domain
---

# content-ui - Content Domain UI

Implements ContentListScreen, ArticleScreen, and rich text display. Fourth in the content domain chain (4/6).

## Usage
```
/content-ui
```

## Parameters
- None. This skill consumes content-flow outputs and produces UI artifacts.

## What It Does
1. Implements **ContentListScreen** — content grid/list, category filter, search
2. Implements **ArticleScreen** — full article view, rich text rendering
3. Implements **RichTextView** — markdown/HTML rendering, images, links
4. Implements **ContentCard** — thumbnail, title, excerpt, bookmark
5. Handles **loading and error states** — skeletons, empty states
6. Uses **Material 3** — components, theming, typography

## Output
- `content_list_screen.dart` — ContentListScreen widget
- `article_screen.dart` — ArticleScreen widget
- `rich_text_view.dart` — RichTextView widget
- `content_card.dart` — ContentCard widget

## What It Must NOT Do
- Call other agents or use the Task tool (emit `REQUEST:` if delegation needed)
- Write schema/entity/DTO code (content-schema responsibility)
- Write repository or data source code (content-provider responsibility)
- Write flow/state orchestration (content-flow responsibility)
- Write route guards or middleware
- Write tests

## Tech Stack
- **UI:** Material 3 (Flutter)
- **State:** Riverpod (read contentProvider, call ContentNotifier methods)
- **Architecture:** Clean Architecture (presentation layer)
- **Domain:** content (TaskSpec domain)
