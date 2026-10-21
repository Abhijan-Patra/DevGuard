"""Actual isolated Gemma/scanner inspections. Metadata only; never change oracles.

This is a small regression/calibration set, not an independent accuracy estimate.
"""
import argparse
import asyncio
from datetime import UTC, datetime
import json
from pathlib import Path
import time

from devguard.config import Settings
from devguard.guard.context import ContextInspector
from devguard.guard.engine import GuardEngine
from devguard.guard.scanner import CredentialScanner
from devguard.models.ollama import OllamaClient
from devguard.schemas.guard import GuardInput
from devguard.storage.audit import AuditStore

ROOT = Path(__file__).resolve().parents[1]

async def run(variants=False):
    model = OllamaClient(Settings('synthetic-local-evaluation-token-1234567890'))
    audit = AuditStore()
    engine = GuardEngine(CredentialScanner(), ContextInspector(model), audit)
    rows = []
    try:
        runtime = await model.inspect()
        if not runtime['model_ready']:
            raise RuntimeError('PINNED_MODEL_UNAVAILABLE')
        cases = json.loads((ROOT/'evals/cases/privacy_cases.json').read_text())[:5]
        if variants:
            cases = json.loads((ROOT/'evals/cases/privacy_variants.json').read_text())
        for case in cases:
            start = time.monotonic()
            record = await engine.evaluate(GuardInput(
                task=case['task'], text=case.get('synthetic_input', case.get('text')),
                surface=case.get('surface', 'explicit_prompt'),
                destination_id='local-preview', content_version=1))
            row = {'case_id': case['id'], 'expected_decision': case['expected_decision'],
                'actual_decision': record.decision.value, 'reason_codes': record.reasons,
                'decision_matches_expectation': record.decision.value == case['expected_decision'],
                'expected_reasons_present': set(case['expected_reason_codes']).issubset(record.reasons),
                'approved_preview_available': record.candidate is not None,
                'elapsed_seconds': round(time.monotonic()-start, 3), 'external_delivery': False}
            rows.append(row)
            print(json.dumps(row), flush=True)
        return {'timestamp': datetime.now(UTC).isoformat(), 'scope':
            'Real pinned local Gemma and Gitleaks; declared synthetic calibration variants' if variants else
            'Real pinned local Gemma and Gitleaks; unchanged original synthetic catalogue P01-P05',
            'runtime': runtime, 'results': rows, 'catalogue_unchanged': True,
            'perfect_accuracy_claimed': False, 'independent_accuracy_benchmark': False}
    finally:
        engine.close()
        await model.close()
        audit.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--variants', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(asyncio.run(run(args.variants)), indent=2)+'\n')

if __name__ == '__main__':
    main()
