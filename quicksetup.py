import subprocess
import sys

def pip_install(package):
    subprocess.call([sys.executable, "-m", "pip", "install", package])

print("installing PySide6...")
pip_install("PySide6")

print("installing PyBass3...")
pip_install("pybass3")
