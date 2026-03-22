# Read file data.json in output folder and automate bins in DaVinci Resolve
import json
import os
import sys
from pathlib import Path

# import DaVinciResolveScript as dvr_script

def main():
    # Read file data.json in output folder
    script_dir = Path(__file__).resolve().parent
    with open(script_dir / "output" / "data.json", "r") as f:
        data = json.load(f)
    print(data)

if __name__ == "__main__":
    main()