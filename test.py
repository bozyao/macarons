# coding: utf-8
__author__ = "bozyao"

import sys
import os

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    from main import run, current_path
    path = os.path.join(current_path())
    sys.path.append(path)
    run(path, use_session=False, debug=True)
