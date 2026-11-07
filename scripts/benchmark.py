"""Reproducible seeded experiment, not an accuracy or competitor benchmark."""
import json
import platform
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from releaseproof.core import verify, suite_digest
ROOT=Path(__file__).resolve().parents[1]
results=[]
for name in ('baseline','hardcoded','receipt_mismatch','correct'):
    source=(ROOT/'examples'/f'{name}.py').read_text()
    for seed in range(20):
        r=verify(source,challenge_seed=seed)
        results.append({k:r[k] for k in ('candidate_sha256','suite_sha256','status','gate','duration_ms','checks_run','challenge_seed')}
                       | {'fixture':name,'checks_passed':sum(c['passed'] for c in r['checks'])})
report={'generated_at':datetime.now(timezone.utc).isoformat(),'python':platform.python_version(),
        'scope':'Four seeded candidates, 20 replay seeds each. No live AI, customers or competitor comparisons.',
        'suite_sha256':suite_digest(),'trials':len(results),'defective_trials':60,'correct_trials':20,
        'false_passes':sum(r['status']=='pass' for r in results if r['fixture']!='correct'),
        'correct_rejections':sum(r['status']!='pass' for r in results if r['fixture']=='correct'),
        'median_verification_ms':round(statistics.median(r['duration_ms'] for r in results),3),
        'provider_calls':0,'results':results}
print(json.dumps(report,indent=2))
