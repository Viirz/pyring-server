FROM python:3.12.9-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      gnupg            \
      build-essential  \
      libffi-dev       \
      libgcrypt20-dev  \
      python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV GROUP_ID=1000 \
    USER_ID=1000 \
    USE_GUNICORN=true
 
WORKDIR /var/www/

# Create a non-root user and group
RUN addgroup --gid $GROUP_ID www && \
    adduser --disabled-password --uid $USER_ID --gid $GROUP_ID www

# Copy the application code into the image 
COPY . /var/www/app
COPY ./main.py /var/www/

# Create the .gnupg directory
RUN mkdir -p /var/www/app/.gnupg

# Create the .pgp directory
RUN mkdir -p /var/www/app/.pgp

# Change permissions of the .gnupg and .pgp directories
RUN chmod 700 /var/www/app/.gnupg /var/www/app/.pgp

# Generate server PGP keypair directly in the container (should work with Debian's GnuPG)
RUN echo "Key-Type: RSA\nKey-Length: 2048\nName-Real: Server\nName-Email: server@example.com\nExpire-Date: 0\n%no-protection\n%commit" > /tmp/keyparams && \
    gpg --batch --homedir /var/www/app/.gnupg --generate-key /tmp/keyparams && \
    rm /tmp/keyparams

# Export server public key to .pgp directory for easy access
RUN FPR=$(gpg --homedir /var/www/app/.gnupg --list-keys --with-colons | awk -F: '/^fpr:/ {print $10; exit}') && \
    gpg --homedir /var/www/app/.gnupg --export --armor "$FPR" > /var/www/app/.pgp/server_pub.asc

# Change ownership of the .gnupg and .pgp directories to the non-root user
RUN chown -R www:www /var/www/app/.gnupg /var/www/app/.pgp

RUN pip install -r app/requirements.txt

USER www

EXPOSE 5000

# Use a startup script to choose between Flask dev server and Gunicorn
CMD if [ "$USE_GUNICORN" = "true" ]; then \
        gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 main:application; \
    else \
        python3 main.py; \
    fi