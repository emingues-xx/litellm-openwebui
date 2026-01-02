# Dockerfile para Open WebUI customizado com UI de Agents
FROM ghcr.io/open-webui/open-webui:main

# Install dependencies
USER root

# Copy custom files
COPY ./custom-ui /app/custom-ui

# Set permissions
RUN chmod -R 755 /app/custom-ui

USER $UID:$GID

# The custom UI will be injected via volume mounts and environment variables
