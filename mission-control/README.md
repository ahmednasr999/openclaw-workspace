# Mission Control

A task board for Ahmed & OpenClaw to track all tasks, built with NextJS and Convex.

## Features

- 📋 **Task Board** - Drag and drop tasks across 5 columns
- 📊 **Dashboard** - Stats, charts, and recent activity
- 👥 **Assignee Tracking** - Tasks assigned to Ahmed, OpenClaw, or Both
- 🏷️ **Categories** - Job Search, Content, Networking, Applications, Interviews
- ⚡ **Priority Levels** - High, Medium, Low
- 📅 **Due Dates** - Track deadlines
- 🔄 **Real-time Updates** - Powered by Convex

## Columns

1. 📥 **Inbox** - New tasks
2. 📝 **My Tasks** - Tasks assigned to Ahmed
3. 🤖 **OpenClaw Tasks** - Tasks assigned to OpenClaw
4. 🔄 **In Progress** - Currently working on
5. ✅ **Completed** - Done tasks

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd mission-control

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your Convex project ID
```

### Convex Setup

1. Go to [convex.dev](https://convex.dev)
2. Create a new project
3. Copy your project ID to `.env.local`:
   ```
   NEXT_PUBLIC_CONVEX_PROJECT_ID=your-project-id
   ```

### Run Locally

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

## Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript
- **Backend**: Convex (real-time database)
- **Styling**: TailwindCSS
- **Icons**: Lucide React

## Project Structure

```
mission-control/
├── app/
│   ├── page.tsx           # Main page with view toggle
│   ├── layout.tsx         # Root layout
│   └── globals.css         # Global styles
├── components/
│   ├── TaskBoard.tsx      # 5-column task board
│   ├── TaskCard.tsx        # Individual task card
│   ├── TaskForm.tsx        # Add task modal
│   └── Dashboard.tsx        # Stats and charts
├── convex/
│   ├── schema.ts          # Database schema
│   └── tasks.ts           # Task CRUD operations
└── public/
```

## Usage

### Adding Tasks

1. Click "+ Add Task" button
2. Fill in task details:
   - Title (required)
   - Description (optional)
   - Assignee (Ahmed, OpenClaw, or Both)
   - Priority (High, Medium, Low)
   - Category (Job Search, Content, Networking, Applications, Interviews)
   - Due Date (optional)
3. Click "Add Task"

### Moving Tasks

Drag and drop tasks between columns:
- Inbox → My Tasks / OpenClaw Tasks / In Progress / Completed
- Any column → Any other column

### Dashboard

Click "Dashboard" to view:
- Tasks completed this week
- Tasks in progress
- Overdue tasks
- Tasks by category (chart)
- Tasks by priority (chart)
- Recent activity

## Environment Variables

```env
NEXT_PUBLIC_CONVEX_PROJECT_ID=your-convex-project-id
```

## License

MIT
