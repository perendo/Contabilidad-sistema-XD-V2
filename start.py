import os
import sys
import time
import webbrowser
import subprocess
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"

BACKEND_URL = "http://127.0.0.1:8000/health"
FRONTEND_URL = "http://localhost:3000"
LOGIN_URL = "http://localhost:3000/login"


def wait_for(url, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as r:
                if 200 <= r.status < 400:
                    return True
        except (URLError, Exception):
            pass
        time.sleep(1)
    return False


def main():
    npm = "npm.cmd" if os.name == "nt" else "npm"

    print("Arrancando backend (FastAPI)...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BACKEND),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("Arrancando frontend (Next.js)...")
    frontend_proc = subprocess.Popen(
        [npm, "run", "dev"],
        cwd=str(FRONTEND),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=True,
    )

    print("Esperando al backend...")
    if not wait_for(BACKEND_URL, 90):
        print("ERROR: el backend no respondió. Revisa los logs.")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(1)

    print("Esperando al frontend...")
    if not wait_for(FRONTEND_URL, 120):
        print("ERROR: el frontend no respondió. Revisa los logs.")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(1)

    print("Abriendo navegador en la página de login...")
    webbrowser.open(LOGIN_URL)

    print("\nServidores en marcha. Pulsa Ctrl+C para detener.\n")
    try:
        while True:
            if backend_proc.poll() is not None:
                print("El backend se detuvo.")
                break
            if frontend_proc.poll() is not None:
                print("El frontend se detuvo.")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDeteniendo servidores...")
    finally:
        for p in (backend_proc, frontend_proc):
            try:
                p.terminate()
            except Exception:
                pass
        for p in (backend_proc, frontend_proc):
            try:
                p.wait(timeout=10)
            except Exception:
                p.kill()
    print("Listo.")


if __name__ == "__main__":
    main()
