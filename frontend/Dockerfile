# Build the React app, then serve it with a lightweight web server.
# This is a "multi-stage build" — two steps in one file:
#   Stage 1 (build): Install Node, compile TypeScript, bundle everything
#   Stage 2 (serve): Copy the compiled files into nginx to serve them

# --- STAGE 1: Build ---
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .

# The REACT_APP_API_URL tells the frontend where the backend lives.
# This is "baked in" at build time, so it must be set when building the image.
# Default: empty string means "same server" (frontend and backend on the same domain).
ARG REACT_APP_API_URL=""
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

# --- STAGE 2: Serve with Nginx ---
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
