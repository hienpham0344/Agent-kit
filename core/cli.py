"""
CLI Helper Utilities and Subprocess Execution Wrapper.
Ensures subprocess exit codes are reliably propagated and output formatting is consistent.
"""

import sys
import subprocess
from typing import List, Optional

def safe_run_subprocess(cmd: List[str], check: bool = False, capture_output: bool = False) -> int:
    """
    Execute subprocess command, ensuring exit codes are properly returned and handled.
    """
    try:
        res = subprocess.run(cmd, check=check, capture_output=capture_output, text=True)
        return res.returncode
    except subprocess.CalledProcessError as e:
        return e.returncode
    except Exception as e:
        sys.stderr.write(f"Command execution error: {e}\n")
        return 1
