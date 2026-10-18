"""Train a candidate artifact only; never overwrite the active SNR model."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from strategy.malaysian_snr.model_training import train_captures
from strategy.malaysian_snr.runtime_settings import normalize_msnr_settings
from strategy.malaysian_snr.config import MalaysianSNRConfig


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--captures',required=True,help='JSONL canonical captures with verified net outcomes')
    parser.add_argument('--settings',required=True,help='JSON containing the replay/runtime settings')
    parser.add_argument('--output',default='storage/analysis/msnr_canonical_model_candidate.json')
    parser.add_argument('--strategy-version',default=MalaysianSNRConfig().strategy_version)
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.captures).read_text(encoding='utf-8').splitlines() if line.strip()]
    raw = json.loads(Path(args.settings).read_text(encoding='utf-8'))
    raw = raw.get('settings',raw)
    settings = normalize_msnr_settings({k:v for k,v in raw.items() if k not in ('version','updated_at')})
    output = Path(args.output).resolve()
    active = Path('storage/ai_models').resolve()
    if output == active or active in output.parents:
        parser.error('El candidato debe guardarse fuera del directorio de modelos activos')
    model,metrics = train_captures(records,settings,strategy_version=args.strategy_version)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(model.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')
    output.with_suffix('.metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    from database.repository import TradingRepository
    TradingRepository().register_msnr_model(output,model.to_dict())
    print(json.dumps({'candidate':str(output),'metrics':metrics,'active_model_changed':False},ensure_ascii=False))


if __name__=='__main__':
    main()
