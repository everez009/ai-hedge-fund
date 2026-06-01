import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from the repository root .env before any backend modules import providers
root_path = Path(__file__).resolve().parents[2]
load_dotenv(root_path / ".env")

# Add the src directory to Python path for imports
# This is a temporary solution while we develop the backend
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.append(src_path)
