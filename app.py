from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from operations import serve

if __name__ == '__main__':
    serve(Path(__file__).resolve().parent)
