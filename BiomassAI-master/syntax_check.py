import sys
import os

# Add core to path
sys.path.append(r"c:\Users\Khush\Downloads\BiomassAI-master\BiomassAI-master")

try:
    from core.verification.services import vision
    from core.verification import views
    print("Syntax check passed.")
except ImportError as e:
    print(f"Import Error: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
except Exception as e:
    print(f"Error: {e}")
