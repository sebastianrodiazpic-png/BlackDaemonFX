"""Compatibility entry point for canonical SNR candidate training."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.train_msnr_canonical import main

if __name__ == '__main__':
    main()
