"""Generate/sample matching online DEMs; see --help."""
import sys
from pathlib import Path
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from reproduction.dem import main
    main()
