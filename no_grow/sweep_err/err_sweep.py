"""Compatibility entry point. Use --help; --output is required."""
import sys
from pathlib import Path
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from reproduction.run import main
    main(['no-grow-error', '--decoder', 'pymatching', *sys.argv[1:]])
