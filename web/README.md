# Web UI

React + Vite frontend for single-question interactive runs.

## Features
- question input
- optional context input
- configurable max rounds (assignment-compliant values should be 3 or greater)
- round-by-round debate display
- judge verdict panel
- copy JSON for debugging and transcript inspection

## Local development
```bash
cp .env.example .env
npm ci
npm run dev
```

## Production build
```bash
npm ci
npm run build
```
