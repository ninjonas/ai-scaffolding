# Code generation utilities.

set working-directory := '..'

# Generate TypeScript types from OpenAPI schema
types:
    cd src/web && pnpm exec openapi-typescript http://localhost:${API_PORT:-8000}/openapi.json -o src/api/types.ts
