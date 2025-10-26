# Cost Vision Insight - Frontend

> React + TypeScript frontend for AI-powered cost estimation

## Overview

Modern, responsive web application for managing articles, viewing cost breakdowns, and analyzing price trends.

## Tech Stack

- **React 18.3** + **TypeScript 5.8** + **Vite 5.4**
- **Tailwind CSS 3.4** + **shadcn/ui** - Styling & components
- **React Query 5.90** - Data fetching & caching
- **React Router 6.30** - Routing
- **Recharts 2.15** - Data visualization
- **React Hook Form 7.61** + **Zod 3.25** - Form handling & validation

## Quick Start

```bash
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

**Access:** http://localhost:5173

### With Docker

```bash
docker-compose up frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                      # shadcn/ui components (40+)
│   │   ├── ArticleInput.tsx         # Article creation form
│   │   ├── CostBreakdown.tsx        # Cost display
│   │   ├── MaterialCompositionChart.tsx
│   │   ├── PriceTrendChart.tsx
│   │   └── SimilarArticles.tsx
│   ├── pages/
│   │   ├── Index.tsx                # Main page
│   │   └── NotFound.tsx
│   ├── lib/
│   │   ├── api.ts                   # API client
│   │   └── utils.ts                 # Utilities
│   └── hooks/
├── public/                          # Static assets
├── package.json
├── vite.config.ts
└── tailwind.config.ts
```

## Key Components

### ArticleInput
Form for creating articles with file upload support.

### CostBreakdown
Displays material, labor, and overhead costs with totals.

### MaterialCompositionChart
Interactive pie chart showing material composition.

### PriceTrendChart
Line chart for price trends over time.

### SimilarArticles
List of semantically similar articles from RAG search.

### UI Components (shadcn/ui)
40+ pre-built components including Button, Card, Dialog, Table, Chart, Form components, etc.

**Add new component:**
```bash
npx shadcn@latest add [component-name]
```

## Development

### Environment Variables

Create `.env.local`:
```bash
VITE_API_URL=http://localhost:8000/api/v1
```

### Common Commands

```bash
pnpm dev          # Development server
pnpm build        # Production build
pnpm preview      # Preview production build
pnpm lint         # Run ESLint
```

### API Integration

API client in `src/lib/api.ts` uses fetch with React Query for caching and state management.

**Example:**
```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

const { data, isLoading } = useQuery({
  queryKey: ['articles'],
  queryFn: api.getArticles
});
```

### Styling

**Tailwind CSS** for utility classes + **CSS variables** for theming:

```tsx
<div className="flex items-center p-4 bg-white rounded-lg shadow">
  <Button variant="outline" size="sm">Action</Button>
</div>
```

## Building

```bash
# Development build
pnpm build:dev

# Production build
pnpm build

# Output in dist/
```

## Deployment

### Static Hosting

Deploy `dist/` folder to Vercel, Netlify, AWS S3, etc.

```bash
# Vercel
vercel --prod

# Netlify
netlify deploy --prod --dir=dist
```

### Docker

```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

### Environment Variables

Set `VITE_API_URL` to your production API endpoint.

## Resources

- **React**: https://react.dev/
- **Vite**: https://vitejs.dev/
- **Tailwind CSS**: https://tailwindcss.com/
- **shadcn/ui**: https://ui.shadcn.com/
- **React Query**: https://tanstack.com/query/

---

See [main README](../README.md) for full project documentation.
