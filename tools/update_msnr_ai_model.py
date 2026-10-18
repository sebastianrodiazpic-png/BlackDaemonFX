"""Read-only validation of SNR model provenance; never manufacture metrics."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy.ai.model import CalibratedLogisticModel
from strategy.malaysian_snr.ai_policy import compatibility
from strategy.malaysian_snr.runtime_settings import normalize_msnr_settings
from strategy.malaysian_snr.config import MalaysianSNRConfig

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True)
    parser.add_argument('--settings',required=True)
    args=parser.parse_args()
    raw=json.loads(Path(args.settings).read_text(encoding='utf-8'))
    raw=raw.get('settings',raw)
    settings=normalize_msnr_settings({k:v for k,v in raw.items() if k not in ('version','updated_at')})
    model=CalibratedLogisticModel.from_dict(json.loads(Path(args.model).read_text(encoding='utf-8')))
    check=compatibility(model,{'strategy_version':MalaysianSNRConfig().strategy_version},settings)
    print(json.dumps({'compatibility':check,'active_model_changed':False},ensure_ascii=False))
    return 0 if check['compatible'] else 2

if __name__=='__main__':
    raise SystemExit(main())
