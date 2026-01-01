
import os
import sys
from pyngrok import ngrok
from django.core.management import execute_from_command_line

def main():
    """Run the server with ngrok."""
    # Set the Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

    # Open a ngrok tunnel to the dev server
    public_url = ngrok.connect(8000).public_url
    print(f" * ngrok tunnel \"{public_url}\" -> \"http://127.0.0.1:8000\"")

    # Update BASE_URL in settings if needed (optional implementation detail)
    # For now, we just print the URL for the user

    # Start the Django server
    # We use 'runserver' by default
    args = sys.argv
    if len(args) == 1:
        args.append('runserver')
        args.append('0.0.0.0:8000') # Force 8000 to match ngrok
        args.append('--noreload') # Prevent auto-reload from trying to open a second tunnel
    
    execute_from_command_line(args)

if __name__ == '__main__':
    main()
