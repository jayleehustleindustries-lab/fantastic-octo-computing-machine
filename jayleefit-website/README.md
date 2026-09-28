# JayLeeFit Coaching Website

A professional Next.js website for JayLeeFit online fitness coaching. Captures qualified leads through an intake form and integrates with Airtable for client data management.

## Stack

- **Next.js 16** (App Router, TypeScript)
- **Tailwind CSS v4** (dark aesthetic, gold accents)
- **Airtable REST API** (Clients table integration)
- **React Hook Form** + **Zod** (form validation)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Airtable API token and base ID
- JayLeeFit Airtable base access

### Setup

1. **Clone & install**

```bash
cd jayleefit-website
npm install
```

2. **Environment variables**

Copy `.env.example` to `.env.local` and fill in:

```bash
cp .env.example .env.local
```

```env
AIRTABLE_API_TOKEN=pat_YOUR_TOKEN
AIRTABLE_BASE_ID=appN8QFsoWJ1fJhxC
AIRTABLE_LEADS_TABLE=Lead Pipeline
NEXT_PUBLIC_SITE_URL=http://localhost:3000
NEXT_PUBLIC_SHOW_STOREFRONT_PROMO=true
NEXT_PUBLIC_STOREFRONT_URL=https://oldlight.shop
```

3. **Run locally**

```bash
npm run dev
```

Visit `http://localhost:3000`

## Features

### Pages

- **Home** (`/`) — Hero + value prop + feature blocks
- **About** (`/about`) — Coach bio + methodology
- **Intake** (`/intake`) — Lead capture form
- **Success** (`/intake/success`) — Confirmation after submission
- **API** (`/api/intake`) — Form submission handler

### Key Components

- **Navbar** — Responsive navigation with mobile menu
- **Footer** — Brand info + cross-promo to Old Light storefront
- **IntakeForm** — Form validation + Airtable submission
- **FeatureBlock** — Reusable feature cards

### Airtable Integration

The intake form writes directly to the `Clients` table in your JayLeeFit base:

**Fields populated:**
- `Name` — from form
- `Email` — from form
- `Phone` — from form (optional)
- `Goals` — array of selected goals
- `Status` — set to "Intake Received" on submit
- `Current Weight (kg)` — optional
- `Timezone` — optional
- `Intake Notes` — optional

**Error handling:** User-friendly messages displayed on form errors (API failures, validation).

## Deployment

### Vercel (recommended)

1. Connect your GitHub repo to Vercel
2. Add environment variables in Vercel dashboard
3. Deploy with one click

### Other platforms

Any Node.js host works (Heroku, Railway, etc.). Ensure env vars are set before deploy.

## Development

### File Structure

```
app/
  page.tsx                (home)
  about/page.tsx          (about)
  intake/page.tsx         (intake form)
  intake/success/page.tsx (success page)
  api/intake/route.ts     (API handler)
  layout.tsx              (root layout)
  globals.css             (Tailwind directives)

components/
  navbar.tsx              (navigation)
  footer.tsx              (footer + promo)
  intake-form.tsx         (form component)
  feature-block.tsx       (feature card)

lib/
  airtable.ts             (Airtable client)
  form-validation.ts      (Zod schema)
```

### Styling

- **Tailwind v4** with custom colors in `tailwind.config.ts`
- Dark theme (`#0f0f0f` background) with gold accents (`#d4af37`)
- Responsive via Tailwind breakpoints (sm, md, lg)
- Utility classes defined in `globals.css` (`.btn-primary`, `.container-max`, etc.)

### Form Validation

Zod schema in `lib/form-validation.ts` defines required/optional fields and error messages. React Hook Form handles submission state.

## Troubleshooting

### "Failed to submit intake to Airtable"

- Check `AIRTABLE_API_TOKEN` is valid (starts with `pat_`)
- Confirm `AIRTABLE_BASE_ID` matches your base URL
- Verify table name in `AIRTABLE_LEADS_TABLE` (exact case match)
- Ensure the Airtable API token has write access to the base

### Form submission hangs

- Check browser console for network errors
- Verify API route (`/api/intake`) is reachable
- Ensure `.env.local` is loaded (restart `npm run dev` after changes)

### Styling looks off

- Tailwind CSS requires a full rebuild after config changes
- Stop dev server (`Ctrl+C`) and restart (`npm run dev`)

## Environment Variables

| Variable | Required | Type | Notes |
|---|---|---|---|
| `AIRTABLE_API_TOKEN` | Yes | String | Airtable personal access token (pat_...) |
| `AIRTABLE_BASE_ID` | Yes | String | JayLeeFit base ID (app...) |
| `AIRTABLE_LEADS_TABLE` | No | String | Table intakes are written to (default `Lead Pipeline`) |
| `NEXT_PUBLIC_SITE_URL` | Yes | URL | Base domain (used for Stripe redirects, etc.) |
| `NEXT_PUBLIC_SHOW_STOREFRONT_PROMO` | No | Boolean | Show Old Light promo in footer (true/false) |
| `NEXT_PUBLIC_STOREFRONT_URL` | No | URL | Link to Old Light storefront |

## Next Steps

- [ ] Deploy to custom domain
- [ ] Add email confirmation after intake
- [ ] Integrate Stripe for paid coaching packages
- [ ] Pull testimonials from Airtable Progress Tracking table
- [ ] Add calendar integration for intro calls

## Support

For questions or issues, reach out to jayleehustle.industries@gmail.com
