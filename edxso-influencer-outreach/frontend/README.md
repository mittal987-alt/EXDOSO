# EDXSO Influencer Outreach — Frontend Command Center

A modern, high-performance web dashboard for the **EDXSO Influencer Outreach Platform**. It provides an intuitive, real-time command center to orchestrate the entire influencer pipeline: automated YouTube discovery, metadata enrichment, criteria qualification, personalized multi-channel copy generation (Email & Instagram DMs), simulated sending, and live delivery audit tracking.

---

## Key Features

- **Real-Time Pipeline Orchestration**: Trigger each pipeline stage with one click:
  - Stage 1: Discover YouTube Creators (custom target channel input)
  - Stage 2: Enrich Channel Metadata & Themes
  - Stage 3: Evaluate & Qualify Candidates
  - Stage 4: Generate Personalized Outreach Drafts
  - Stage 5: Simulate Dispatch & Log Deliveries
- **Influencer Directory**:
  - Live search by creator name, category, or content themes
  - Status filters (`All`, `Qualified`, `Pending`, `Rejected`)
  - Grid card view and structured table view toggle
  - Modal viewer with full channel stats, engagement rate, email/social links, and rejection reasons
- **Outreach Studio**:
  - Filter by channel (`Email` vs `Instagram DM`) and status (`Draft` vs `Sent`)
  - Real-time word count badges verifying platform constraints (**60–90 words** for Email, **15–30 words** for Instagram DM)
  - Single message dispatch simulation and bulk pending dispatch
- **Delivery Audit Logs**:
  - Live timestamped event logs for every dispatch simulation
- **One-Click CSV Exports**:
  - Direct download links for `influencers.csv`, `outreach_messages.csv`, and `delivery_logs.csv`
- **Manual Influencer Intake Form**:
  - Register custom influencer profiles directly into the pipeline with instant validation.

---

## Technology Stack

- **Framework**: Vite 6 + Vanilla JavaScript (ES modules)
- **Styling**: Vanilla CSS design system with custom CSS variables, glassmorphism, responsive grid, and Google Fonts (`Outfit`, `Plus Jakarta Sans`, `JetBrains Mono`)
- **Backend Communication**: RESTful JSON API requests to `http://127.0.0.1:8000` with CORS support

---

## Getting Started

### Prerequisites

- Node.js v18+ (tested on Node v24.14+)
- EDXSO Backend running on `http://127.0.0.1:8000`

### Installation & Run

1. Navigate to the `frontend` directory:
   ```bash
   cd c:\projects\edxso\edxso-influencer-outreach\frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

   The application will be live at:
   **[http://127.0.0.1:3000](http://127.0.0.1:3000)**

4. Build for production:
   ```bash
   npm run build
   ```
