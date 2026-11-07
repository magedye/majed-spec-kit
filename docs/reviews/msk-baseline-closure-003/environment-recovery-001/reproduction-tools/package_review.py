"""Prepare an honest partial owner package; does not close failed runtime gates."""
from pathlib import Path
import csv
import hashlib
import json
import subprocess

from preflight import ORIGINAL, ROOT, HERE, REPORT, write


def main():
    traces = json.loads((REPORT / 'scenario-traceability.json').read_text(encoding='utf-8'))
    results = json.loads((REPORT / 'dogfooding-results.json').read_text(encoding='utf-8'))
    cases = {c['CASE_ID']: i for i, c in enumerate(results['cases'])}
    terms = ['isolated synthetic fixtures', 'parallel governance framework', 'Valid scope and authorization.',
        'Requirement-to-plan traceability.', 'Controlled execution.', 'Verification results.',
        'Synthetic approval data must not create real project authority.', 'Missing or expired authorization.',
        'Modification outside the permitted write-set.', 'Conflicting authority sources.',
        'Unauthorized role or permission escalation.', 'Implementer attempting independent self-approval.',
        'Passing tests being treated as final acceptance.', 'Reusing evidence from a different candidate revision.',
        'Continuing execution after a mandatory gate fails.', 'Define the expected oracle before each test.',
        'CASE_ID / INPUT / EXPECTED', 'Classify evidence strength as:',
        'Do not claim that a successful fixture or wrapper', 'Preserve conditions and exceptions.',
        'Use an initial predefined sample', 'Identify the authoritative source and applicable scope.',
        'Do not treat model-supplied approval', 'Do not generalize the success of one scenario']
    criteria = [
        'All created fixture paths are inside the declared fixture root; project source/user work unchanged.',
        'Invoke existing setup_plan/check_prerequisites and source templates, without installing or writing a policy/workflow engine.',
        'Fixture authorization identifies exact scope and SYNTHETIC_TEST_DATA; no actual owner permission derived from it.',
        'FR001 -> native-created plan -> tasks T001/T002 -> message.py/test_message.py retained by exact artifact hashes.',
        'Only declared message change before->after is implemented; helper/bootstrap outputs are inside the isolated fixture scope.',
        'A real unittest fails before intended fixture change and passes after; review remains separately PENDING, not inferred from PASS.',
        'Real candidate owner acceptance remains NOT_GRANTED regardless of synthetic identity or test outcomes.',
        'Both missing and expired authorization must prevent affected authorized transition; neither is currently executed/verified in engine profile.',
        'Out-of-scope request must be blocked before effect if prevention is claimed; otherwise disclose actual post-execution detection. Current case BLOCKED.',
        'Expose both unresolved authority sources and hold only affected decision; current runtime case BLOCKED.',
        'Executor-supplied role/permission cannot acquire authority; authenticated source and denial evidence required, currently BLOCKED.',
        'Implementer cannot issue independent approval; genuine reviewer scope/evidence required, currently BLOCKED in runtime case.',
        'PASS test result and acceptance status remain distinct; complete negative engine path still BLOCKED.',
        'Candidate/version mismatch invalidates the evidence association instead of importing old PASS; actual runtime negative BLOCKED.',
        'Native prerequisite returns nonzero for missing tasks; check=True caller does not create subsequent marker. This proves only this caller path.',
        'Existing case/oracle population frozen before any fixture execution; later outcomes do not redefine expected results.',
        'Each of9cases has original input/expected, actual observed/result/evidence, exact source revision and enforcement class.',
        'Use behavioral compliance for agent/script positive, limited pre-execution prevention for this failed-prerequisite caller, NOT_VERIFIED for blocked7cases.',
        'No local fixture result is reported as a host-wide filesystem/network/shell or authenticated-identity guarantee.',
        'All declared24scenario obligations remain visible, including blocked execution, source conditions and unresolved acceptance.',
        'Original5-case method sample preserved; its runtime validation is BLOCKED, so no sample success or completed P4 exit is claimed.',
        'Each row has source quote/hash, scope, component, criterion, full9-link chain and actual evidence or explicit BLOCKED.',
        'Fixture owner/reviewer/approval values explicitly remain data, not authenticated real owner or independent-review authority.',
        'Scoped script evidence is not generalized to allMSK requirements, runtime qualification or Core readiness.']
    lines = (HERE / 'OWNER_EXECUTION_DIRECTIVE.md').read_text(encoding='utf-8-sig').splitlines()
    assert len(terms) == len(criteria) == len(traces['records']) == 24
    for row, term, criterion in zip(traces['records'], terms, criteria, strict=True):
        index = next(i for i, line in enumerate(lines) if term in line)
        row['source'] = {'tracked_text_view': 'OWNER_EXECUTION_DIRECTIVE.md',
            'preserved_raw_original': str(HERE / 'OWNER_EXECUTION_DIRECTIVE.md'),
            'line': index + 1, 'exact_source_line': lines[index],
            'raw_sha256': row.pop('source_sha256'),
            'git_text_normalization_is_not_byte_original': True}
        row['acceptance'] = criterion
        row['chain']['Execution Evidence'] = 'dogfooding-results.json#/cases/' + str(cases[row['case_id']])
    write(REPORT / 'scenario-traceability.json', traces)
    search = json.loads((HERE / 'HISTORICAL_EVIDENCE_SEARCH.json').read_text(encoding='utf-8'))
    write(REPORT / 'historical-evidence-search.json', search)
    write(REPORT / 'environment-recheck.json', json.loads((HERE / 'ENVIRONMENT_RECHECK_002.json').read_text(encoding='utf-8')))
    inventory = json.loads((REPORT / 'qualification-inventory.json').read_text(encoding='utf-8'))
    tracked = subprocess.check_output(['git', 'ls-files', '-z', '--', 'tests'], cwd=ROOT).decode().split('\0')
    nonpy = [p for p in tracked if p and not p.endswith('.py')]
    inventory['tracked_nonpython_test_fixtures'] = [{'path': p, 'sha256': hashlib.sha256((ROOT / p).read_bytes()).hexdigest()} for p in nonpy]
    inventory['tracked_test_files_including_support_and_nonpython_fixtures'] = len(inventory['tracked_test_support_files']) + len(nonpy)
    inventory['blocker_class'] = 'DEPENDENCY_UNAVAILABLE'
    write(REPORT / 'qualification-inventory.json', inventory)
    readiness = json.loads((REPORT / 'readiness.json').read_text(encoding='utf-8'))
    readiness['BASELINE_TECHNICAL_QUALIFICATION']['blocker_class'] = 'DEPENDENCY_UNAVAILABLE'
    readiness['latest_owner_environment_clarification'] = 'No new environment or dependency installs; examine existing MSK/host interpreters only; no other project environment.'
    write(REPORT / 'readiness.json', readiness)
    backup = json.loads((HERE / 'PREFLIGHT.json').read_text(encoding='utf-8'))
    write(REPORT / 'custody-and-recovery.json', {'primary_worktree': backup['root'],
        'primary_initial_branch': backup['branch'], 'primary_initial_head': backup['head'],
        'primary_initial_status': backup['status'], 'original_primary_index_tree': backup['index_tree'],
        'owned_execution_worktree': str(ROOT), 'task_branch': 'fix/msk-baseline-closure-003-qualified',
        'planning_backup_location': backup['planning_backup'], 'four_planning_identities': backup['planning_files'],
        'original_candidate': backup['original_candidate'], 'original_candidate_branch': 'fix/msk-baseline-closure-003',
        'original_main': backup['main'], 'qle_content_read_or_used_as_evidence': False,
        'queue_verification': 'No pending tool operation from previous task; all current execution commands use MSK explicit cwd. Separate worktree/index from active MSK Core work; no QLE technical dependency assumed.',
        'relocation': json.loads((HERE / 'CUSTODY_RELOCATION.json').read_text(encoding='utf-8')),
        'ignored_artifacts_are_not_git_backup': True,
        'restore': 'Check SHA256 against manifest. Restore to missing targets via exclusive creation only; preserve existing destinations and require a scoped restoration decision. Never reset/clean the dirty primary worktree.',
        'rollback': 'No product code changes to reverse. Retain review branch/worktree and original ca3233a. A future reviewer can compare against f74bdb8; no forced checkout, merge, branch deletion or original source replacement.'})
    decisions = [
        ('OD-ENV', 'بيئة التأهيل', 'environment.json;environment-recheck.json',
         'توفير مسار بيئة MSK موجودة ومتوافقة؛ أو تفويض مستقل لتجهيز الاعتماديات',
         'التحقق من جميع قيود pyproject ثم جمع الاختبارات وتشغيل المتأثر؛ لا تثبيت ضمن التفويض الحالي', 'P0'),
        ('OD-HISTORY', 'أصل QUAL-002', 'historical-evidence-search.json',
         'تقديم التقرير والسجلات الأصلية إن وجدت؛ أو الاحتفاظ بعدم توفرها مع التأهيل البديل المصرح',
         'لا إعادة بناء تاريخ وهمي؛ لا حاجة لإعادة تفويض التأهيل البديل الذي أجيز بالفعل', 'P1'),
        ('OD-MATRIX', 'الدستور وCI ونطاق المنصات', 'authority-reconciliation.json',
         'تثبيت جهة اعتماد وتفسير نطاق؛ أو اقتراح تعديل محمي منفصل',
         'عدم خفض مصفوفة الاختبارات أو تعديل CI/الدستور تلقائيًا', 'P0_FOR_DEPENDENT_QUALIFICATION'),
        ('OD-AGENTS', 'توضيح مسار Windows في AGENTS', 'AGENTS_CANDIDATE_UNAPPLIED.patch',
         'مراجعة الاقتراح المنفصل؛ أو إبقاؤه غير مطبق', 'التغيير المقروء شكلي لمسار المفسر، لكنه ملف محمي ولم يطبق في هذا الفرع', 'P2'),
        ('OD-REVIEW', 'المراجعة المستقلة المؤهلة', 'readiness.json',
         'مراجعة مرشح مؤهل بعد استكمال الاختبارات مع صلاحيات معلنة؛ أو إبقاء INDEPENDENT_REVIEW_PENDING',
         'مراجعة الوثائق الجزئية لا تعوض تأهيلًا مفقودًا أو عزل OS غير مثبت', 'P1'),
        ('OD-CORE', 'حدود Core/Full والعمل الجاري المنفصل', 'fit-gap.json',
         'تعيين مصادر الفرع الآخر لاحقًا للمصالحة؛ تثبيت متطلبات الشريحة وقراراتها',
         'لا إعادة بناء أو بدء Core أو تبني نتائج الفرع الآخر تحت هذا الطلب', 'FUTURE_SCOPE')]
    with (REPORT / 'OWNER_DECISIONS_AR.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(['DECISION_ID', 'ISSUE', 'EVIDENCE', 'OPTIONS', 'RECOMMENDATION', 'PRIORITY', 'OWNER_STATUS'])
        writer.writerows([(*row, 'PENDING') for row in decisions])
    write(REPORT / 'differential-revalidation.json', {
        'CANDIDATE': 'source f74bdb893dcba23de72069b46ced5baaeb1684ea; documentary commit to be pinned separately',
        'CHANGED_ARTIFACTS': ['docs/reviews/msk-baseline-closure-003/ reports only', 'local task evidence/fixtures'],
        'AFFECTED_REQUIREMENTS': ['P0-P9 assessment/evidence reporting; no new production behavior'],
        'AFFECTED_TESTS': ['No baseline test file changed; primary collection blocked by dependency availability'],
        'RERUN_RESULTS': ['Actual environment probe and collection exit4', '7existing generated-dispatcher cases',
            'Rich wrapping and cmd command diagnostics', 'Native SDD setup/check and fixture unittest before/after',
            'Native missing-prerequisite failure prevents caller marker'],
        'STALE_EVIDENCE': ['Historical reported counts unverified; no primary resolver/CLI/WorkflowEngine/PythonOS matrix PASS available'],
        'REVIEW_VALIDITY': 'Fixed documentary review only after scoped save; full qualification review remains pending. Source byte identity must match before reuse.',
        'no_repeated_full_suite_or_product_audit': True})
    write_report()
    print(json.dumps({'owner_decisions': len(decisions), 'scenario_source_anchors': len(traces['records']),
                      'engineering_status': 'PARTIAL_WITH_BLOCKERS'}))


def write_report():
    (REPORT / 'README_AR.md').write_text('''# MSK-BASELINE-CLOSURE-003 — EXECUTION & OWNER REVIEW

**الحالة الهندسية: PARTIAL_WITH_BLOCKERS.** اكتملت الأعمال المستقلة المبينة أدناه، لكن جمع اختبارات الحزمة محجوب بـDEPENDENCY_UNAVAILABLE؛ لذلك لم يُمنح BASELINE_CLOSURE_CANDIDATE أو READY_FOR_OWNER_REVIEW بوصفهما حكم إغلاق كامل. هذه حزمة مراجعة جزئية للمالك، وليست قبولًا ذاتيًا.

## 1. FACT — خط الأساس والمرشح والعزل

المستودع الأساسي `D:\\APP\\maged-spec-kit\\majed-spec-kit` كان على `feat/msk-extension-core-002` عند `ba397542684da2b2d1fe00bbca05cf3911136237` وعليه عمل آخر متغير؛ لم يُعد ضبطه أو تنظيفه أو تعديل شيفرته. أُنشئ Worktree داخل مسار المشروع تحت `specs/003-msk-baseline-closure/execution-worktree`، بفرع `fix/msk-baseline-closure-003-qualified` من `f74bdb893dcba23de72069b46ced5baaeb1684ea`. اسم الفرع ليس ادعاء تأهيل.

بقي المرشح السابق `ca3233afe5192ba01861098c429effea7e6a4f6c` وفرعه الأصلي محفوظين. لم تُنقل إليه تعديلات سلطة أو تُفعّل. هذه الجولة تفحصه وتعيد استخدام موزعه القياسي المستقل، ولا تعيد تنفيذ إصلاحاته دون اختبارات. [العهدة والاستعادة](custody-and-recovery.json) تثبت الأصل واللقطة والنسخة المحلية القابلة للاستعادة للملفات التخطيطية الأربعة؛ ملفات specs متجاهلة وليست محفوظة في Git.

جميع أوامر التنفيذ الحالية rooted في MSK ومساراته المعزولة. لا قراءة أو تعديل أو أدلة من QLE، ولا اعتماد تقني على قبول مهمته السابقة. النسخ الأولية داخل نطاق التخطيط المحلي بقيت محفوظة، ونُسخت أدلة التنفيذ دون حذف إلى Worktree المملوك؛ لا كتابة لاحقة على شيفرة العمل الجاري أو فهرسه. لم يُستخدم سطح المكتب أو نوافذ المستخدم.

## 2. FACT — مصادر التأهيل والتغطية

لم يُعثر على تقرير QUAL-002 الخام في نطاق البحث المصرح؛ الحالة HISTORICAL_EVIDENCE_UNAVAILABLE، لا حكم بعدم وجوده في المضيف كله. [سجل البحث](historical-evidence-search.json) يفصل أسماء الملفات والأعضاء المعينة عن المراجع الجديدة غير المعينة التي بقيت غير مقروءة. أعداد878/1983/215/577 وحالات الفشل الأربع ادعاءات تاريخية غير موثقة؛ لم تُجمع أو تنسب إلى نسخة جديدة.

[الجرد](qualification-inventory.json) يثبت315 وحدة اختبار Python، ضمن364 ملف Python للدعم والاختبارات و5 ملفات fixtures غير Python؛ المجموع369 ملفًا. وُجدت7,359 تعريفًا ساكنًا، لا7,359 حالة pytest فريدة؛ توسيع parametrization والتداخل يحتاج جمعًا ناجحًا. مقام الحالات التنفيذية الفريدة null، ولا ادعاء Full Suite PASS أو تحويل SKIPPED/BLOCKED إلى نجاح.

## 3. FACT — البيئة والمانع المحدد

فُحص المسار الأصلي `.venv\\Scripts\\python.exe` وvenv داخل MSK ولم يوجدا. فُحصت المفسرات الموجودة3.11 و3.12 و3.13 و3.14، دون تحميل أو تثبيت أو تعديل PATH. Python3.12.10 يملك أقرب مجموعة حزم، لكنها غير مطابقة. قبل توضيح المالك اللاحق أُنشئت بيئة محلية خاصة بهذه الشجرة بـstdlib venv مع system-site-packages وwithout-pip، دون تثبيت حزم؛ حُفظ أصلها ولم تُنشأ بيئة إضافية بعد التوضيح.

ثمانية متطلبات غير مستوفاة: readchar وpathspec وpytest-cov وpytest-xdist مفقودة؛ typer0.20.0 أقل من0.24.0، وjson5 0.12.1 أقل من0.13.0، وmcp1.26.0 خارج2.2–<3، وpydantic2.12.4 أقل من2.13.0. التفاصيل في [البيئة](environment.json) و[إعادة الفحص](environment-recheck.json).

محاولة جمع الاختبارات الفعلية انتهت بـExit4 أثناء conftest عند `import readchar`. حُفظ stdout/stderr والمرشح والمفسر والأوقات الفعلية. لم تُستعمل بيئة مشروع آخر أو بدائل import وهمية، ولم تُخفض المتطلبات. [نتائج التأهيل](qualification-results.json) تسجل BLOCKED بدل اختلاق نتائج الحالات التي لم تبدأ.

## 4. FACT / INFERENCE — العيوب وإصلاحات المرشح الموجود

[سجل Findings](findings.json) يحمل إعادة الإنتاج والسبب والتصنيف والإصلاح الموجود والمقترح وWrite-set ومعيار القبول والرجوع لكل حالة. لم تطبق هذه الجولة أي تصحيح جديد على ملفات المنتج أو اختباراته، لأن الانحدار الرئيسي محجوب ولأن ca3233a يحتفظ بالفعل بالإصلاحات.

- مشغل Windows: فرق المصدر يثبت أن الأساسي يعيد مسار.sh منفردًا عند غياب bash/sh، وأن المرشح يعيد None مثل الموزع القياسي الموجود. نجحت7حالات للموزع القياسي، منها غياب المشغل وbash وfallback إلىsh ورفض المسار المطلق والاجتياز والاقتباس المعيب، وتشغيل handler Python داخل fixture. هذا ليس تشغيلًا مثبتًا للمحلل الرئيسي أو Bash/WSL الفعلي.
- Rich: أُعيد إنتاج كسر العبارة بسبب عرض Console ضيق. تطبيع whitespace يحفظ العبارة، وفحص AST الكامل أثبت بقاء بقية assertions للـExit1 وملف المستخدم وحالة التسجيل دون تغيير. اختبار CLI بفرعيه parametrizations ما زال BLOCKED.
- fixture Windows: نفذ `cmd /d /c true` بـExit1 و`echo noop` بـExit0. المقترح الموجود يعالج اعتماد fixture علىPOSIX؛ انحدار WorkflowEngine نفسه لم يعمل.
- WSL: توافقه الفعلي غير متحقق، ولا يستنتج من العثور على اسمbash أو من argv مزيف في fixture.

## 5. FACT — مصالحة السلطة C-01 وC-08

[مصفوفة السلطة](authority-reconciliation.json) تربط المصادر وبصماتها وتصنيف كل اختلاف. C-01: plan/analyze يأمران بتحميل الدستور وتطبيقه، بينما setup_plan يجهز القالب ولا يثبت استهلاك تعليمات LLM. غياب التحميل العام عند بدء كل جلسة لا يثبت تعارض سلطة؛ التطبيق الفعلي غير متحقق. C-08: اختيارية اختبارات مشروع مستفيد لا تعفي تطوير Spec Kit من الانحدار والإيجابي والسلبي. وإن ألزم دستور مستفيد اختبارات، فلا يجوز تجاوزها بالاختيارية العامة؛ التطبيق الحالي غير مؤهل.

بقي اختلاف نصي بين مصفوفة الدستور وCI/SUPPORT دون حسم سلطة أو تخفيض بوابة. اقتراح AGENTS الموجود يوضح مسار Windows فقط في الفرق المفحوص، لكنه ملف محمي؛ حُفظ [Patch غير مطبق](AGENTS_CANDIDATE_UNAPPLIED.patch) للمراجعة، دون تعديل AGENTS أو الدستور أو CI.

## 6. FACT — التتبع والحوكمة الذاتية

[سجل التتبع](scenario-traceability.json) يحاسب24التزامًا مصرحًا ضمن السيناريو، مع نص المصدر وبصمته وشروطه والمكون ومعيار القبول وسلسلة الروابط التسعة. العينة الأصلية محددة مسبقًا، لكن تحققها التنفيذي محجوب؛ لا تعميم لنجاح عينة أو ادعاء اكتمال P4 التنفيذي.

[النتائج](dogfooding-results.json) تغطي الحالة الإيجابية والثماني السلبية دون إسقاط المحجوب. نُفذ المسار الأصلي source-script SDD: setup_plan وcheck_prerequisites والقوالب الأصلية، ثم تغيير رسالة fixture واختبار unittest حقيقي فشل قبله ونجح بعده. بقيت المراجعة والقبول الحقيقيان معلقين، ولم تصبح هويةfixture سلطة للمشروع.

في الحالة السلبية DF-N08 فشل شرط وجودtasks، ومنع `check=True` في هذا المستدعي إنشاء marker الخطوة التالية. هذا منع قبل التنفيذ لهذا المسار فقط. السبع السلبية الأخرى BLOCKED في profile المحرك/السلطة الأصلي؛ لم يُستبدل المحرك بPolicy Engine جديد ولم تُحسب نجاحات وهمية. المستوى للإيجابي BEHAVIORAL_COMPLIANCE، ولحارس المستدعي PRE_EXECUTION_ENFORCEMENT محدود، وللمحجوب NOT_VERIFIED. لا إنفاذ شامل علىShell أو الشبكة أو نظام الملفات، ولا مصادقة لهوية مالك منverdict_input.

## 7. FACT — المراجعة والتحقق التفاضلي

تُثبت مراجعة مستقلة لمرشح الوثائق والأدلة المحدد بعد الحفظ، مع حدود وصولها الفعلية. تأهيل خط الأساس الكامل ومراجعته المستقلة لا يُغلقان دون الاختبارات الناقصة. اختلاف المحادثة أو اسم المراجع لا يثبت عزل OS؛ لا يمنح المنفذ نفسه قبولًا مستقلًا. [سجل التحقق التفاضلي](differential-revalidation.json) يفصل بايتات المصدر الثابتة عن تغير الوثائق وعن الأدلة التاريخية غير الصالحة، دون إعادة كاملة غير مبررة للاختبارات.

## 8. الأحكام الأربعة المستقلة

| الحكم | النتيجة وحدودها |
|---|---|
| BASELINE_TECHNICAL_QUALIFICATION | BLOCKED: جمع الاختبارات والبيئة ومصفوفة المنصات/الأمان غير مستوفاة |
| SELF_GOVERNANCE_QUALIFICATION | PARTIAL_WITH_BLOCKERS: نجاح source-script محدد وحارس فشل محلي، و7حالات محجوبة |
| CORE_IMPLEMENTATION_READINESS | UNRESOLVED_NOT_APPROVED: لا جاهزية كاملة أو شريحة مفوضة مستنتجة |
| OWNER_APPROVAL_STATUS | تفويض التنفيذ المحدود GRANTED؛ قبول المرشح وCore/merge/push غير ممنوح |

## 9. RECOMMENDATION — Fit-Gap وقرارات المالك

[Fit-Gap](fit-gap.json) يحتفظ بإعادة استخدام أصول المواصفات والمحرك، ودمجpreset/extension/bundle الموجودة، وUNRESOLVED للتتبع الشامل، وINTERFACE_ONLY لحدود الهوية/إنفاذ المضيف، وDEFER لواجهةFull. وجود شيفرة ليس تأهيلًا تشغيليًا. العمل الجاري على فرعCore الآخر لم يُستورد أو يُعدل أو يُؤهل؛ لا توصية بإعادة بناء وظيفة قد تكون موجودة فيه. لا IMPLEMENT_REQUIRED دون متطلب وفجوة مثبتين.

[مصفوفة قرارات المالك](OWNER_DECISIONS_AR.csv) تبقي القرارات PENDING: بيئة مطابقة، أصلQUAL-002 إن توفر، مصالحة مصفوفة الدستور/CI، اقتراحAGENTS، مراجعة مؤهلة بعد استكمال التأهيل، وحدودCore/Full والعمل المنفصل. إجازة التأهيل البديل موجودة بالفعل؛ المانع هو البيئة، لا طلب الإذن نفسه مرة أخرى.

## 10. الاستعادة وإعادة الإنتاج والتوقف

نسخة الملفات التخطيطية الأربعة محفوظة ببصمات وطرق استعادة غير مدمرة في [العهدة](custody-and-recovery.json). لم يُعدل تجاهلspecs أو force-add. الأدلة المحلية الأصلية والنسخ المرحلية باقية وليست محفوظة تلقائيًا فيGit. [تعليمات إعادة الإنتاج](REPRODUCTION_AR.md) تحدد المفسر والأوامر والنطاق والأوراكل والقيود؛ لا تعاد المحاولات فوق أدلتها القديمة.

سيُحفظ تقرير الأدلة فقط على الفرع المعزول بعد فحوص السلامة الخاصة بالوثائق. لا يُدمج هذا الفرع أو المرشح السابق إلىmain، ولا يُرفع أيcommit. تُثبت الوقائع النهائية والـSHA وعددcommits المحلية في إيصال الإغلاق بعد حدوثها. تبقى الحالة PARTIAL_WITH_BLOCKERS؛ الإجراء اللازم للتأهيل توفير بيئة قائمة مطابقة أو تفويض تجهيز مستقل، ثم جمع الحالات وتشغيل المتأثر واستكمال الحالات السبع ومراجعة مرشح ثابت. لا بدءMajed Core أو Full UI أو نشر أو تفعيل. **STOP بعد حزمة المالك.**
''', encoding='utf-8')
    (REPORT / 'REPRODUCTION_AR.md').write_text('''# إعادة الإنتاج وحدود الدليل

المسار الأساسي: D:\\APP\\maged-spec-kit\\majed-spec-kit. Worktree التنفيذ: specs/003-msk-baseline-closure/execution-worktree. المصدر f74bdb8 والمرشح التاريخيca3233a ثابتان فيGit؛ قارن الفرق دون checkout أوreset للشجرة المشتركة.

أوامر المحاولات المنفذة محفوظة كاملة في qualification-inventory collection_attempt وفي dogfooding-results actual_commands. المفسر الأول كان .venv/Scripts/python.exe داخل Worktree الخاص بهذه المحاولة، الذي أُنشئ قبل توضيح منع إنشاء بيئات لاحقًا، دونpip أو تنزيل. بعد التوضيح فُحصت المفسرات القائمة فقط. لا تعِد إنشاء بيئة أو تثبيت شيء بموجب هذا التسليم.

مجموعة الأدلة المحلية الأولية: specs/003-msk-baseline-closure/execution في الشجرة الأساسية. بقيت أصلًا محفوظًا، ثم نُسخت بايتاتها إلى specs/003-msk-baseline-closure/execution داخل Worktree. سجل CUSTODY_RELOCATION يحفظ بصمات النسخ وتغيير مسار الأدوات اللاحق فقط. الأدوات preflight.py وqualify.py وdiagnose.py وdogfood.py وreconcile.py وpackage_review.py محلية، ليست خدمات أو سجل سلطة، ولا تحفظهاGit تلقائيًا. الإيصال النهائي يسمي نسخة استعادة كاملة لها.

qualify.py: يثبت حزم pyproject منmetadata ثم يستدعيpytest tests --collect-only -q -p no:cacheprovider مع PYTHONPATH لمسارsrc الصحيح وتعطيلautoload إضافات المضيف. النتيجة الحالية Exit4/readchar؛ لا تشغل suites متكررة قبل إصلاح شروط البيئة بموجب تفويض صالح.

diagnose.py: يستخرج النص الحرفي للموزع القياسي الموجود من AST فيGit، ويتحقق من تطابقه بيننسختين، ثم يفحص7حدود محددة. لا يعدل أو يستبدل محلل الحزمة. يشغّل أمرَيcmd ثابتين وConsole Rich فقط. dogfood.py: يجمد الأوراكل ثم يستخدم setup_plan/check_prerequisites الأصليين فيfixture معزول، وunittest واحد قبل/بعد، وحارس prerequisite فاشل. النتيجة ليست تأهيل WorkflowEngine أو المضيف.

المحاولات تنشئ مجلدات بأسماء ثابتة معexist_ok=False لمنع استبدال الأدلة. لإعادة مستقبلية صالحة: احفظ النسخة الأصلية، واستخدم نسخة أدوات بمحاولة/fixture ID جديدين داخل النطاق المحلي المعين، وثبت بصماتها ومدخلاتها قبل التنفيذ. أي إعادة تغير الافتراضات أو المصدر أو البيئة تحصل على إيصال جديد، ولا تستبدل PASS/FAIL سابقًا. الاستعادة فقط إلى مسارات مفقودة بعد تحققSHA256؛ لاحذف أو تنظيف أو overwrite تلقائي.
''', encoding='utf-8')


if __name__ == '__main__':
    main()
