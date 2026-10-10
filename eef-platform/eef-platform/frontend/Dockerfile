# Runs the Vite dev server inside the container. This keeps VITE_API_BASE_URL
# resolvable at container start (a static `vite build` would bake the API URL
# in at build time, which breaks docker-compose's runtime environment
# override) and matches this project's "local development" framing.
# For a real production deploy, build a static bundle (`npm run build`) behind
# a proper CDN/static host instead -- see DEPLOYMENT.md.
FROM node:22-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev"]
