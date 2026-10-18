"""Read-only comparison of active classifier scales and captured live features."""
import json
import sys
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig
from strategy.ai.feature_extraction import feature_vector

out=Path(sys.argv[1]);audit=json.loads((out/'entry_gate_audit.json').read_text(encoding='utf-8'))
model=MetaLabelingEngine(MetaLabelingConfig(),worker='MALAYSIAN_SNR').load_model('MALAYSIAN_SNR')
features=audit['score_details'][0]['payload']['meta_label']['features']
vector=np.asarray(feature_vector(features),dtype=float)
means=np.asarray(model.model.mean);scales=np.asarray(model.model.scale);weights=np.asarray(model.model.weights)
rows=[]
for name,value,mean,scale,weight in zip(model.model.feature_names,vector,means,scales,weights):
    rows.append({'feature':name,'live':float(value),'training_mean':float(mean),
                 'training_scale':float(scale),'weight':float(weight),
                 'standardized_contribution':float((value-mean)/scale*weight)})
probabilities=[]
for seconds in (0.,19.267227,60.,877.129191):
    changed={**features,'signal_open_age_seconds':seconds}
    probabilities.append({'signal_open_age_seconds':seconds,'probability':model.probability(feature_vector(changed))})
result={'rows':rows,'first_live_probability':model.probability(vector),
        'age_sensitivity_only_not_validated_predictions':probabilities}
(out/'feature_compatibility.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'largest_negative_contributions':sorted(rows,key=lambda r:r['standardized_contribution'])[:8],
    'age_sensitivity':probabilities},indent=2))
