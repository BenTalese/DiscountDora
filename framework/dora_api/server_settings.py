# Gunicorn
# Run via 'gunicorn -c server_settings.py startup:app' (change directory to framework folder)
workers = 4  # Adjust the number of worker processes based on your server's resources
bind = '0.0.0.0:1809'  # The host and port to bind to #TODO: Investigate making this user defined (appsettings.json?)
timeout = 60  # Timeout for handling requests (in seconds)
