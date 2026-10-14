import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
uvicorn.run('src.main:app', host='127.0.0.1', port=8000, log_level='info')