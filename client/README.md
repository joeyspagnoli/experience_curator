# ExperienceCurator client

React 19 + TypeScript (strict) + Vite 7 frontend for the ExperienceCurator API. Three-pane app at `/app` (library/upload, ask, resume) plus a run-inspection view at `/debug/:traceId`.

```bash
npm install
VITE_API_BASE=http://localhost:8000 npm run dev   # http://localhost:5173
npm run build                                     # tsc -b && vite build
npm run lint
```

There is no Vite proxy, so `VITE_API_BASE` must point at the running FastAPI server.

Full setup instructions and API examples are in the [root README](../README.md).
