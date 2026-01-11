# Phase 2: Chat Viewer UI Component

## Overview

Phase 2 implements a professional, interactive Chat Explorer UI that allows users to browse, filter, and analyze messages stored in the backend database. The interface is built with React + TypeScript and integrates seamlessly with the Phase 1 backend APIs.

---

## Features

### 1. Message Table
- Displays all messages in a paginated table
- Columns: Timestamp, Sender, Message Preview, Sentiment Badge, Language, Score, Action
- Hoverable rows with smooth interactions
- Sentiment-colored badges (Green/Positive, Red/Negative, Gray/Neutral)

### 2. Advanced Filtering
- **Date Range**: Start and end dates (ISO format)
- **Participant Filter**: Dropdown of all speakers
- **Sentiment Filter**: Positive / Negative / Neutral
- **Keyword Search**: Full-text search in message content
- **Apply & Reset**: Apply filters together or reset all

### 3. Pagination
- Support for large datasets (100+ messages)
- Configurable limit (default 25 per page)
- Previous/Next navigation buttons
- Page indicator (Page X of Y)

### 4. Statistics Dashboard
- **Total Messages**: Count of all messages
- **Average Sentiment Score**: Aggregate sentiment
- **Top Participant**: Most active user
- Updates dynamically based on applied filters

### 5. Message Detail Modal
- Click "View" on any message to open full details
- Displays:
  - Full message text
  - Original + translated text (if available)
  - Sentiment score and label
  - Detected language
  - Emotion breakdown (joy, anger, sadness, etc.)
  - Keywords extracted
- Smooth animations and dismissible

### 6. Responsive Design
- Mobile-friendly (adapts to tablets/phones)
- Dark mode support
- Professional color scheme
- Loading states and empty states

---

## Component Structure

### ChatViewer.tsx

**Main component** that orchestrates:
1. State management (messages, filters, pagination)
2. API calls to `/messages` and `/stats` endpoints
3. Filter UI rendering
4. Message table rendering
5. Modal logic

**Key State Variables:**
```typescript
- messages: Message[] - Current page of messages
- stats: StatsData | null - Overview statistics
- currentPage: number - Current pagination page
- totalPages: number - Total pages available
- filters: FilterState - Active filters
- selectedMessage: Message | null - Message being viewed in modal
- showDetailModal: boolean - Modal visibility
- users: string[] - List of all participants
```

**Key Methods:**
- `fetchStats()` - Get statistics over filtered data
- `fetchMessages(page)` - Fetch paginated messages with current filters
- `handleFilterChange()` - Update a single filter value
- `applyFilters()` - Apply all filters and refresh data
- `resetFilters()` - Clear all filters and reload

### ChatViewer.css

**Styling** includes:
- Professional card/grid layouts
- Responsive tables
- Modal animations
- Button states (hover, disabled)
- Dark mode support
- Color-coded sentiment badges

---

## API Integration

### GET /messages

Called by `fetchMessages(page)`:
```javascript
const params = new URLSearchParams({
  limit: 25,
  page: 1,
  user: filters.selectedUser,      // optional
  sentiment: filters.sentiment,      // optional
  keyword: filters.keyword,          // optional
  start_date: filters.startDate,    // optional
  end_date: filters.endDate,        // optional
});

const response = await axios.get(`/messages?${params}`);
// Returns: { messages, total, page, limit, total_pages }
```

### GET /stats

Called by `fetchStats()`:
```javascript
const params = new URLSearchParams();
if (filters.startDate) params.append('start_date', filters.startDate);
if (filters.endDate) params.append('end_date', filters.endDate);
if (filters.selectedUser) params.append('user', filters.selectedUser);

const response = await axios.get(`/stats?${params}`);
// Returns: { total_messages, sentiment_distribution, top_participants, ... }
```

---

## Data Model

### Message Interface
```typescript
interface Message {
  id: string;
  timestamp: string;
  sender: string;
  text: string;
  translated_text?: string;
  language: string;
  ensemble_score: number;
  ensemble_label: 'Positive' | 'Negative' | 'Neutral';
  emotions?: Record<string, number>;
  keywords?: string[];
}
```

### FilterState Interface
```typescript
interface FilterState {
  startDate: string;           // YYYY-MM-DD
  endDate: string;             // YYYY-MM-DD
  selectedUser: string;        // Exact name
  sentiment: string;           // Positive|Negative|Neutral
  keyword: string;             // Free text search
}
```

---

## UI Walkthrough

### 1. Initial Load
- Stats dashboard shows overview (total messages, avg sentiment, top user)
- Message table loads page 1 (25 messages)
- User dropdown populates from top participants

### 2. Applying Filters
- User selects start date (2024-01-15)
- User selects sentiment (Positive)
- User clicks "Apply Filters"
- → Stats recalculate for filtered range
- → Messages table refreshes with matching data
- → Pagination resets to page 1

### 3. Viewing Message Detail
- User clicks "View" button on any row
- Modal opens with full message details
- Displays sentiment scores, emotions, keywords
- User can close modal (click X or overlay)

### 4. Pagination
- User navigates between pages
- URL/state updates
- Table re-fetches messages for new page
- "Previous" button disabled on page 1
- "Next" button disabled on last page

---

## Styling Highlights

### Color Scheme
- **Primary**: `#667eea` (purple/blue for CTA buttons)
- **Positive**: `#10b981` (green)
- **Negative**: `#ef4444` (red)
- **Neutral**: `#6b7280` (gray)
- **Background**: `#f5f5f5` (light gray)

### Component Spacing
- Cards: 20-30px padding
- Grid gaps: 15px
- Modal max-width: 600px
- Table row height: ~50px

### Responsive Breakpoints
- Tablet (≤768px): Single-column filters, smaller tables
- Mobile: Full-width tables, hidden columns on very small screens

---

## Integration with App.tsx

The ChatViewer is now available as a tab in the main dashboard:

```tsx
{/* Tab Navigation */}
<div className="nav nav-tabs mb-4" role="tablist">
  <button onClick={() => setActiveTab('upload')}>📊 Analysis</button>
  <button onClick={() => setActiveTab('viewer')}>💬 Chat Explorer</button>
</div>

{/* Chat Explorer Tab */}
{activeTab === 'viewer' && <ChatViewer />}
```

---

## Performance Considerations

1. **Pagination**: Limits messages per page (25) to avoid loading thousands
2. **Indices**: Backend database uses indices on sender, timestamp, sentiment
3. **Lazy Loading**: Modals only render when opened
4. **Memoization**: Use `useCallback` for API functions to prevent redundant calls

---

## Accessibility

- Semantic HTML (`<table>`, `<label>`)
- ARIA attributes on modal
- Keyboard navigation (Tab, Enter, Escape)
- Color contrast meets WCAG AA standards
- Alt text for icons

---

## Future Enhancements

1. **Infinite Scroll**: Replace pagination with infinite scroll
2. **Export Filtered Data**: Download as CSV/JSON
3. **Advanced Charts**: Sentiment timeline, language distribution pie chart
4. **Message Comparison**: Compare two messages side-by-side
5. **Bulk Actions**: Select multiple messages and perform actions
6. **Search History**: Remember previous searches

---

## Testing

### Manual Testing Checklist
- [ ] Load chat explorer (should show stats + first page of messages)
- [ ] Filter by user (should show only that user's messages)
- [ ] Filter by date range (should respect dates)
- [ ] Filter by sentiment (should show only positive/negative/neutral)
- [ ] Search keyword (should highlight/show matches)
- [ ] Apply multiple filters together
- [ ] Click "View" on a message (modal should open)
- [ ] Close modal (escape key or X button)
- [ ] Paginate to next page
- [ ] Paginate to previous page
- [ ] Reset filters (all messages should return)

---

## File Structure

```
frontend/src/
├── components/
│   ├── ChatViewer.tsx         # Main component
│   ├── ChatViewer.css         # Styles
│   ├── Dashboard.tsx          # Existing dashboard
│   └── FileUpload.tsx         # Existing upload
├── App.tsx                    # Updated with tabs
└── api.ts                     # API calls
```

---

## Getting Started

1. Ensure backend is running with Phase 1 APIs:
   ```bash
   cd backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000 --lifespan off
   ```

2. Install frontend dependencies (if not already):
   ```bash
   cd frontend
   npm install axios
   ```

3. Run frontend dev server:
   ```bash
   npm run dev
   ```

4. Navigate to Chat Explorer tab in the UI
5. Upload a chat file first (Analysis tab) to populate the database
6. Switch to Chat Explorer tab to browse and filter messages

