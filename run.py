#!/usr/bin/env python3
"""28/06/2025 - This file is used to run the server using Bjoern."""


from bjoern import run
from core.wsgi import application
import os
import sys


def main():
    """Poetry's script configuration requires a function to call."""
    _, *args = sys.argv
    print("Args:", *args)
    if len(args) == 0:
        print(
            "You must specify a unix socket path (e.g. unix:/path/to/socket) or an IP address and port (e.g. 0.0.0.0 8000).",
            file=sys.stderr,
        )
        exit(1)

    print("Updating the database")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.production")
    from django.core.management import call_command

    call_command("migrate", interactive=False)
    call_command("collectstatic", verbosity=0, interactive=False)

    print("Starting the server")
    # Bjoern can't handle port numbers that aren't of integer type.
    if len(args) > 1:
        args[1] = int(args[1])
    run(application, *args)


if __name__ == "__main__":
    # Allow the script to be called from the command line.
    main()
