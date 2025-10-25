import sys
from pathlib import Path

if __name__ == "__main__" and not globals().get("__package__"):
    pkg_parent = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(pkg_parent))

from wem2csv.cli import main

if __name__ == "__main__":
    main()