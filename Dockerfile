FROM gdssingapore/airbase:python-3.13

# Install system dependencies (CA certs, curl)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl \
 && curl -sSLj -o "/usr/local/share/ca-certificates/cloudflare.crt" \
      "https://seed-general-public-files.s3.ap-southeast-1.amazonaws.com/seed-cloudflare-root-certs/Cloudflare_CA.pem" \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Environment settings
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV PYTHONUNBUFFERED=TRUE

# Install Python dependencies
COPY --chown=app:app requirements.txt ./
RUN pip install -r requirements.txt

# Copy application code
COPY --chown=app:app . ./

# Run as non-root
USER app

# Streamlit entrypoint (⚠️ update to app_ans.py)
CMD ["bash", "-c", "streamlit run completed_codebase/app_ans.py --server.port=$PORT --server.address=0.0.0.0"]