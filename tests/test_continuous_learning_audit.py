"""Learning audit never promotes candidates or learns from incomplete setups."""
import copy
from strategy.ai.feature_extraction import FEATURE_NAMES
from strategy.ai.training import build_training_dataset, temporal_validation
from strategy.ai.continuous_audit import refresh, snapshot


def trade(i=0, status='CLOSED'):
    return {'id':i, 'instrument':'TEST', 'entry_time':f'2026-09-01T{i:02d}:00:00Z',
            'exit_time':f'2026-09-01T{i:02d}:30:00Z', 'status':status,
            'net_pnl':10 if i%2 else -10, 'realized_rr':1 if i%2 else -1,
            'details':{'metadata':{'bot_profile':'GOLD','strategy_name':'SMC',
            'entry_learning_snapshot':{'feature_names':list(FEATURE_NAMES),
            'features':{n:0.25 for n in FEATURE_NAMES}}}}}


def test_features_are_frozen_and_malformed_captures_excluded():
    row=trade(); row['details']['metadata']['trade_score']=999
    assert build_training_dataset([row])['features'][0]==[0.25]*len(FEATURE_NAMES)
    for bad in ['invalid', {'feature_names':list(FEATURE_NAMES),'features':{n:'bad' for n in FEATURE_NAMES}}]:
        row['details']['metadata']['entry_learning_snapshot']=bad
        assert build_training_dataset([row])['rows']==0


def test_imported_without_context_audited_not_trained(tmp_path):
    row=trade(); row['details']['metadata']={'historical_mt5_import':True}
    assert build_training_dataset([row])['rows']==0
    result=refresh([row],'GOLD','MT5',root=tmp_path)
    assert result['without_entry_snapshot']==1
    assert result['instruments']['TEST']['losses']==1
    assert not result['strategies']
    assert snapshot(tmp_path)[0]['mode']=='CANDIDATE_ONLY'


def test_open_sibling_excludes_entire_setup(tmp_path):
    closed=trade(); opened=trade(1,'OPEN')
    for row in (closed,opened): row['details']['metadata']['parent_execution_key']='same'
    assert build_training_dataset([closed,opened])['rows']==0
    del opened['details']['metadata']['entry_learning_snapshot']
    report=refresh([closed,opened],'GOLD','MT5',root=tmp_path)
    assert not report['strategies']


def test_candidate_path_and_no_retraining_same_results(tmp_path, monkeypatch):
    calls=[]
    def train(self, trades, strategy_name):
        calls.append(self.config.model_directory)
        return {'trained':True,'reason':'MODEL_TRAINED'}
    monkeypatch.setattr('strategy.ai.continuous_audit.MetaLabelingEngine.train',train)
    rows=[trade(i) for i in range(4)]
    first=refresh(rows,'GOLD','MT5',min_samples=4,root=tmp_path)
    refresh(rows,'GOLD','MT5',min_samples=4,root=tmp_path)
    assert len(calls)==1 and 'candidate_models' in calls[0]
    assert first['strategies']['SMC']['eligible_closed_setups']==4


def test_new_capture_requires_close_timestamp_and_purges_overlap():
    row=trade(); row['exit_time']=None
    assert build_training_dataset([row])['rows']==0
    rows=[trade(i) for i in range(24)]
    for row in rows: row['exit_time']='2026-09-02T00:00:00Z'
    report=temporal_validation(rows,worker='GOLD',min_train_samples=4)
    assert not report.valid and report.reason=='NO_VALID_TEMPORAL_FOLDS'
