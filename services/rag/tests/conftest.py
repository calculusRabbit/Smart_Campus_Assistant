import sys
import os

# add the rag folder to path so tests can do "from config import X" etc
# just like the real scripts do when you run them normally
this_folder = os.path.dirname(__file__)
rag_folder = os.path.join(this_folder, "..")
sys.path.insert(0, rag_folder)