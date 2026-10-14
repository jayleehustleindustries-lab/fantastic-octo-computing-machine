# Vercel entrypoint: serves the ASGI app for every path (see vercel.json).
from neuralhud.app import create_app

app = create_app()
