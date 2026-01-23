import inspect
try:
    from trl import SFTConfig, SFTTrainer
    print("SFTConfig arguments:")
    print(inspect.signature(SFTConfig.__init__))
    print("\nSFTTrainer arguments:")
    print(inspect.signature(SFTTrainer.__init__))
except ImportError:
    print("Could not import trl. Please ensure it is installed.")
except Exception as e:
    print(f"Error: {e}")
