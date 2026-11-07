"""Correct independent R1; preserve blocked runtime and exact source wording."""
import json

from preflight import ROOT, HERE, REPORT, write


def main():
    path = REPORT / 'scenario-traceability.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    row = next(r for r in data['records'] if r['REQUIREMENT_ID'] == 'SG-13')
    lines = (HERE / 'OWNER_EXECUTION_DIRECTIVE.md').read_text(encoding='utf-8-sig').splitlines()
    term = 'Avoid treating a Git commit or passing test as proof of owner acceptance.'
    line = next(i for i, text in enumerate(lines) if term in text)
    row['meaning'] = 'Neither a Git commit nor a passing test proves owner acceptance.'
    row['acceptance'] = 'A commit identity or PASS may be evidence of saved work/test outcome only. Owner acceptance requires an explicit decision tied to candidate and scope. The runtime negative remains BLOCKED, not newly tested.'
    row['source']['line'] = line + 1
    row['source']['exact_source_line'] = lines[line]
    row['documentary_correction'] = {'review': 'INDEPENDENT_REVIEW_001.md', 'finding': 'R1',
        'reason_no_new_row': 'One homogeneous acceptance-boundary obligation now preserves both disjunctive triggers, commit OR passing test;24rows retained, no new runtime case invented.',
        'runtime_verification': 'BLOCKED', 'owner_acceptance': 'NOT_GRANTED'}
    write(path, data)
    start = next(i for i, text in enumerate(lines) if text.startswith('## 7. P4'))
    end = next(i for i, text in enumerate(lines) if text.startswith('## 9. P6'))
    # Explicit source-specific clause assignments. A line not covered by this
    # manual table or a structural heading remains unresolved and stops output.
    assignments = [
        ('Establish at least one complete', ['SG-01', 'SG-02']),
        ('Required traceability chain:', ['SG-22']), ('Owner Instruction → Requirement', ['SG-22']),
        ('For every mandatory obligation', ['SG-20', 'SG-22']),
        ('Preserve its original meaning', ['SG-20']), ('Preserve conditions and exceptions.', ['SG-20']),
        ('Identify the authoritative source', ['SG-22']), ('Link the obligation', ['SG-22']),
        ('Define its acceptance criterion.', ['SG-22']), ('Reference appropriate execution', ['SG-06', 'SG-22']),
        ('Preserve unresolved ambiguities.', ['SG-20']), (term, ['SG-13']),
        ('Use an initial predefined sample', ['SG-21']), ('Do not generalize the success', ['SG-24']),
        ('**P4 Exit Gate:**', ['SG-20', 'SG-22']),
        ('Execute one complete positive scenario', ['SG-01', 'SG-17']),
        ('Demonstrate a small, authorized engineering change', ['SG-02', 'SG-05']),
        ('The evidence must show:', ['SG-03', 'SG-04', 'SG-05', 'SG-06', 'SG-07']),
        ('Valid scope and authorization.', ['SG-03']), ('Requirement-to-plan traceability.', ['SG-04']),
        ('Controlled execution.', ['SG-05']), ('Verification results.', ['SG-06']),
        ('Separate review and acceptance status.', ['SG-06', 'SG-07']),
        ('Synthetic approval data must not', ['SG-07']), ('Test at least:', [f'SG-{i:02d}' for i in range(8, 16)]),
        ('Missing or expired authorization.', ['SG-08']), ('Modification outside the permitted', ['SG-09']),
        ('Conflicting authority sources.', ['SG-10']), ('Unauthorized role or permission', ['SG-11']),
        ('Implementer attempting independent', ['SG-12']), ('Passing tests being treated', ['SG-13']),
        ('Reusing evidence from a different', ['SG-14']), ('Continuing execution after', ['SG-15']),
        ('Define the expected oracle before', ['SG-16']), ('For every case, record:', ['SG-17']),
        ('CASE_ID / INPUT / EXPECTED', ['SG-17']), ('Classify evidence strength as:', ['SG-18']),
        ('`BEHAVIORAL_COMPLIANCE`', ['SG-18']), ('`POST_EXECUTION_DETECTION`', ['SG-18']),
        ('`PRE_EXECUTION_ENFORCEMENT`', ['SG-18']), ('`NOT_VERIFIED`', ['SG-18']),
        ('Do not claim that a successful fixture', ['SG-19']),
        ('Do not treat model-supplied approval', ['SG-23']), ('**P5 Exit Gate:**', ['SG-17', 'SG-18', 'SG-19'])]
    units, unresolved = [], []
    for index in range(start, end):
        text = lines[index]
        if not text.strip():
            continue
        matches = [refs for phrase, refs in assignments if phrase in text]
        structural = text.startswith('#') or text == '---'
        refs = sorted({r for match in matches for r in match})
        if not refs and not structural:
            unresolved.append({'line': index + 1, 'exact_text': text})
        units.append({'line': index + 1, 'exact_text': text,
                      'classification': 'SOURCE_STRUCTURE' if structural else 'MANUAL_OBLIGATION_OR_BOUND_CONTEXT_ASSIGNMENT',
                      'requirement_refs': refs, 'runtime_satisfaction_not_inferred': True})
    if unresolved:
        print(json.dumps({'unresolved_source_lines': unresolved}))
        raise ValueError('Unassigned P4/P5 source clause')
    write(REPORT / 'scenario-source-coverage-checklist.json', {
        'scope': 'Every nonblank physical source line of ownerP4/P5, structure distinguished from obligations/bound fields; line count is not an independent-rule count.',
        'source': data['records'][0]['source']['preserved_raw_original'],
        'source_sha256': data['records'][0]['source']['raw_sha256'],
        'nonblank_source_line_denominator': len(units), 'unresolved_source_lines': [], 'units': units,
        'manual_review': 'Root rechecked original P4/P5 full text after demonstrated R1 gap; does not certify actual runtime tests or allMSK requirements.'})
    write(REPORT / 'review-remediation.json', {'reviewed_candidate': 'e174dbbde4968fa0f0573163f262626889b84d20',
        'raw_review': 'INDEPENDENT_REVIEW_001.md', 'finding': 'R1',
        'correction': 'SG13 now preserves both commit and passing-test triggers with exact P4 source anchor; own criterion/status; all nonblank P4/P5 source lines rechecked against manual assignments.',
        'scenario_denominator': 24, 'new_runtime_tests_claimed': False,
        'status': 'CORRECTED_PENDING_DIFFERENTIAL_DOCUMENTARY_REVIEW', 'full_closure_status': 'PARTIAL_WITH_BLOCKERS'})
    p = REPORT / 'README_AR.md'
    text = p.read_text(encoding='utf-8')
    text += '''

## مراجعة المرشح الجزئي وتصحيحها

طلبت [المراجعة المستقلة الأولى](INDEPENDENT_REVIEW_001.md) على `e174dbb` إضافة التمييز الصريح بين وجودCommit وقبول المالك إلى التتبع. صُحح SG-13 ليحفظ شرطيCommit أوPASS في قيد القبول نفسه، ببقاء24سجلًا، وأُعيد فحص نص P4/P5 كله في [قائمة تغطية المصدر](scenario-source-coverage-checklist.json). هذه مصالحة معنى، لا اختبار محرك جديد؛ بقيت حالته التنفيذية BLOCKED وقبول المالك NOT_GRANTED. [سجل التصحيح](review-remediation.json) ينتظر مراجعة تفاضلية مثبتة على المرشح الجديد. لا اعتماد إغلاق كامل.
'''
    p.write_text(text, encoding='utf-8')
    print(json.dumps({'corrected': 'SG-13', 'scenario_obligations': 24, 'source_lines_accounted': len(units), 'runtime_negative_still': 'BLOCKED'}))


if __name__ == '__main__':
    main()
