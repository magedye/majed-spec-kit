"""Owner-facing execution annex assembled only from completed current evidence."""
from recover_environment import ROOT,LOCAL,REPORT,dump,sha
from datetime import datetime,timezone
from pathlib import Path
import csv
import json
import subprocess
import shutil
import os

def main():
    parent=REPORT.parent
    load=lambda name:json.loads((REPORT/name).read_text(encoding='utf-8'))
    out=load('qualification-outcomes.json')
    current=load('readiness-current.json')
    rec=load('collection-reconciliation.json')
    assert out['unique_denominator']==14402
    assert not rec['missing'] and len(rec['added'])==1
    lint_path='lint-authorized-002/receipt.json' if (REPORT/'lint-authorized-002/receipt.json').exists() else 'lint-001/receipt.json'
    lint=load(lint_path)
    current['mandatory_lint']={'result':lint['result'],'evidence':lint_path,
        'required_version':'0.15.0','no_silent_substitution':True}
    current['baseline_source_candidate']=load('fix-checkpoint.json')['after']
    current['remaining_blockers']=['11 unresolved observations:7unmocked externalcatalog expectations and4Rich hardwrap assertions outside current write-set',
       'Parallel stdio initialize timed out; native initialize diagnostic and original complete stdio test passed serially. Concurrency/rootcause unresolved; no globalPASS transfer.',
       'Native gate does not provide authenticated grant/role/independent review/write-set/evidence-candidate controls',
       'Protected constitution/CI matrix reconciliation and broader CI/security evidence not supplied by this local profile',
       'Historical QUAL-002 raw provenance remains unavailable']
    if lint['result']!='PASSED':current['remaining_blockers'].append('CI-pinned Ruff0.15.0 check not passed; exact missing/cache or check result disclosed')
    dump(REPORT/'readiness-current.json',current)
    # Retain old derived views as explicit historical snapshots before current pointers change.
    snapshots=REPORT/'historical-98e6269'
    snapshots.mkdir(exist_ok=False)
    for name in ['readiness.json','phase-status.json','write-set.json','OWNER_DECISIONS_AR.csv']:
        shutil.copyfile(parent/name,snapshots/name)
    dump(parent/'readiness.json',{**current,'current_evidence_prefix':'environment-recovery-001/',
        'previous_snapshot':'environment-recovery-001/historical-98e6269/readiness.json',
        'source_candidate':load('fix-checkpoint.json')['after']})
    ws=json.loads((parent/'write-set.json').read_text(encoding='utf-8'))
    ws['authorization_updates']=[{'source':'environment-recovery-001/OWNER_ENVIRONMENT_RECOVERY_AUTHORIZATION.txt',
        'sha256':load('recovery-state.json')['authorization_sha256'],
        'scope':'Isolated local/cache-only environment recovery and previously blocked qualification; external downloads require separate authorization'}]
    ws['local_environment']='New isolated environment-recovery-001/venv with no system-site-packages; earlier nonqualified .venv retained. External download authorization separate.'
    ws['qualification_temp_write_set']=load('external-temp-write-set.json')
    dump(parent/'write-set.json',ws)
    phase=json.loads((parent/'phase-status.json').read_text(encoding='utf-8'))
    phase['phase_dispositions'].update(P1='BASELINE14401COLLECTED; CURRENT14402ACCOUNTED; initial13639PASS730SKIP33FAIL; scoped differential then latest13661PASS730SKIP11FAIL with explicit env/parallelMCP limits',
        P2='FOUR_EXISTING_CA3233A_FIX_FILES_REUSED_EXACTLY; actual before regression FAIL and516 affected checks PASS',
        P5='SEVEN_PREVIOUSLY_BLOCKED_NATIVE_ENGINE_CASES_EXECUTED_WITH_CONTROL_GAPS; older positive preserved',
        P6='NEW_INDEPENDENT_TECHNICAL_REVIEW_PENDING_FIXED_CURRENT_PACKAGE',
        P7='Source hash equivalence and environment change recorded; interrupted unsafe-temp attempt excluded; remaining cases rerun externally')
    phase['next_action']='Owner review of actual blockers and requested narrow remedies; no Core/main merge/push or protected authority edits.'
    phase['current_evidence']='environment-recovery-001/readiness-current.json'
    dump(parent/'phase-status.json',phase)
    trace=json.loads((parent/'scenario-traceability.json').read_text(encoding='utf-8'))
    native=load('dogfooding-assessment.json')
    overlay=[]
    for requirement in trace['records']:
        overlay.append({'REQUIREMENT_ID':requirement['REQUIREMENT_ID'],'case_id':requirement['case_id'],
            'meaning_and_source_preserved':True,'older_observation_remains_historical':requirement['execution_result'],
            'current_native_variants':[r for r in native['variants'] if r['case']==requirement['case_id']],
            'positive_prior_source_script_evidence_preserved':requirement['case_id']=='DF-POS',
            'acceptance_status':'NOT_GRANTED','requirement_fulfillment_not_inferred_from_case_execution':True})
    dump(REPORT/'scenario-current-overlay.json',{'denominator':24,'records':overlay,
        'status':'PARTIAL_WITH_CONTROL_GAPS','raw_source_meaning_and_50line_accounting_unchanged':True,
        'limits':'Executing all named variants is not proof of all24 broad obligations or host enforcement; original method sample limitations preserved'})
    trace['historical_record_scope']='Prior source-script/blocked-engine evidence at98e6269 retained; current observations are separate, not retroactive fulfillment'
    trace['current_execution_overlay']='environment-recovery-001/scenario-current-overlay.json'
    trace['actual_scenario_qualification']='PARTIAL_WITH_CONTROL_GAPS'
    dump(parent/'scenario-traceability.json',trace)
    decisions=[
      ['OD-ENV','البيئة المعزولة','OWNER_ENVIRONMENT_RECOVERY_AUTHORIZATION.txt;environment-verified.json','تفويض البيئة المحلية صدر ونُفذ؛ لا تنزيل إضافي تلقائي','الحفاظ على البيئة السابقة وإعادة الإنتاج بالبصمات','CLOSED_OFFLINE_SCOPE','GRANTED_OFFLINE_ONLY'],
      ['OD-LINT','نسخة Ruff المطلوبة',lint_path,'تفويض Ruff0.15.0 المحدد صدر؛ لا يعمم على حزم أو مصادر أخرى','لا استبدال إصدار CI أو خفضه','COMPLETED_PINNED_CHECK' if lint['result']=='PASSED' else 'P0_FOR_LINT_GATE','GRANTED_SINGLE_PACKAGE_ONLY'],
      ['OD-QUAL','إخفاقات التأهيل المتبقية','qualification-outcomes.json','طلب إصلاح محدود بملفاته بعد التصنيف؛ أو إبقاء الفحص المتأثر محجوبًا','لا تعديل خارج الملفات الأربعة بموجب هذا التسليم','P0','PENDING'],
      ['OD-TRUST','حدود Gate وسلطة الدستور/CI','dogfooding-assessment.json;../authority-reconciliation.json','تحديد الملف الوظيفي المطلوب وحدود الثقة؛ حسم القرارات المحمية بطلب مستقل','لا إنشاء Policy Engine أو تطبيق Core بدعوى إكمال التأهيل','P0_FOR_DEPENDENT_GATES','PENDING'],
      ['OD-HISTORY','أصل QUAL-002','../historical-evidence-search.json','تقديم الأصل إن وجد؛ أو إبقاء نتائجه التاريخية غير متحققة مع الأدلة البديلة الجديدة','لا اختلاق أصل أو جمع الأعداد القديمة','P1','PENDING'],
      ['OD-CORE','حدود Core/Full','../fit-gap.json;readiness-current.json','مراجعة متطلبات شريحة لاحقة بقرار مستقل','لا استنتاج التفويض من نجاح بيئة أو اختبارات أو مراجعة','FUTURE_SCOPE','NOT_GRANTED']]
    with (REPORT/'OWNER_DECISIONS_AR.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['DECISION_ID','ISSUE','EVIDENCE','OPTIONS','RECOMMENDATION','PRIORITY','OWNER_STATUS']);writer.writerows(decisions)
    with (parent/'OWNER_DECISIONS_AR.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['DECISION_ID','ISSUE','EVIDENCE','OPTIONS','RECOMMENDATION','PRIORITY','OWNER_STATUS'])
        writer.writerows([[r[0],r[1],';'.join(os.path.relpath(REPORT/ref,parent).replace('\\','/') for ref in r[2].split(';')),*r[3:]] for r in decisions])
    versions={d['name']:d['version'] for d in load('environment-verified.json')['installed_distributions']}
    counts=out['counts']
    readme=f'''# MSK-BASELINE-CLOSURE-003 — استكمال البيئة والتأهيل المحلي

**الحالة: `PARTIAL_WITH_BLOCKERS`.** زال مانع اعتماديات Python في الملف المحلي المحدد؛ لم يمنح ذلك إغلاق خط الأساس أو قبول المالك أو جاهزية Core تلقائيًا. هذا ملحق استئناف للمهمة القائمة، وليس طلبًا أو سجل سلطة بديلًا.

## البيئة والتحقق

Python **3.12.10**، مطابق لقيد `>=3.11` في pyproject الأصلي غير المعدل. البيئة الخاصة بهذه المهمة هي `specs/003-msk-baseline-closure/execution/environment-recovery-001/venv` داخل Worktree. أُنشئت دون system-site-packages أو user-site، وحُفظت البيئة السابقة غير المؤهلة.

حُلَّت وثُبّتت **50 حزمة** مباشرة وتابعة من مخبأ uv المحلي، دون شبكة أو تثبيت عام أو استخدام بيئة مشروع آخر. استخدم الحل `--offline --no-config --no-python-downloads`، والتثبيت `--require-hashes --only-binary :all: --strict --link-mode copy`. اجتازت الحزم فحص القيود المباشرة والانتقالية و2,654 بصمة RECORD. هذه أدلة اتساق مصدر المخبأ والتثبيت، وليست تدقيق ثغرات أو إثبات أصالة مستقلًا أو حظر شبكة على مستوى نظام التشغيل.

أبرز الإصدارات: pytest {versions['pytest']}، pydantic {versions['pydantic']}، typer {versions['typer']}، rich {versions['rich']}، mcp {versions['mcp']}، readchar {versions['readchar']}، pathspec {versions['pathspec']}. جميع الإصدارات ومواضعها في [فحص البيئة](environment-verified.json)، والبصمات المقفلة في [متطلبات هذه المحاولة](requirements-offline.txt). لا ملف قفل Python معتمد في الأصل؛ ملف هذه المحاولة دليل إعادة إنتاج، وليس تعديلًا لمواصفات الاعتماديات.

كشفت المجموعة الأولية غياب تثبيت المشروع نفسه ونقطة `specify`؛ لا يكفي استيراد المصدر لتأهيل المسار المنفصل. بعد انتهاء العملية، ثُبت المشروع نفسه محليًا بالطريقة canonical لـuv editable، دون شبكة أو تغيير أي اعتماديات تشغيل أخرى، مع تثبيت وبصمات اعتماديات backend المعلنة وديناميكيات editable في بيئة بناء منفصلة. احتُفظ بفشل build الأول لغياب editables ثم استُخدم تصريح backend نفسه لتوفيره من المخبأ. التوزيعات النهائية51، منها50 اعتمادًا ثابت الإصدار والمشروع نفسه1.3.3.dev0. [التحقق النهائي](environment-final-verified.json) يفحص RECORD والتوافق؛ و[فحص التثبيت](project-install-verification/receipt.json) يثبت direct_url editable=true، نقطة specify_cli:main والاستيراد من خارج المستودع بـ-I دونPYTHONPATH، ونجاح help/version. لا ادعاء بمقارنة بصمات قديمة لكل ملف حين لم توجد لقطة منفصلة لها؛ التثبيت طلب no-deps، والإصدارات السابقة ثابتة وفحص RECORD النهائي سليم.

## الاختبارات ومقامها

نجح الجمع الأصلي: **14,401 معرفًا فريدًا**، دون تكرار أو خطأ جمع. بعد إضافة اختبار الانحدار الموجود في ca3233a أصبح المقام **14,402**. جرد315 ملف اختبار ساكن لا يساوي315 ملفًا يجمع حالات مباشرة: أربعة ملفات Integration Base تحتوي Mixins يعاد استخدامها في أصناف التكامل. بقي اختلاف التعريفات الساكنة عن الوراثة وparametrization ظاهرًا في [المصالحة](collection-reconciliation.json).

قبل التصحيح: **511 نجاحًا و4 إخفاقات** في515 حالة متأثرة. فشل اختبار الانحدار الجديد على مصدر الحدث القديم. بعد إعادة استخدام الملفات الأربعة من ca3233a حرفيًا: **516 نجاحًا**. يحتفظ اختبار Rich بمعنى رسالة الرفض وفحص Exit Code وحماية الملف المعدل وسجل enabled؛ يطبع المسافات فقط. استُبدل `true` الخاص بـPOSIX بـ`echo noop` في Fixtures التركيب، ولم يُخفض عقد المنتج. فحص Bash الإيجابي يثبت بناء argv بlauncher اصطناعي؛ لا يثبت تشغيل Bash/WSL الحقيقي.

الحصيلة الأولية من ثلاث مجموعات متباينة غطت14,402معرفًا:13,639نجاحًا و730متخطاة و33إخفاقًا. أُعيد استخدام516نجاحًا، وأُضيفت حالتا تحقق سلامة، ونُفذ13,884من البقية. بعد تثبيت المشروع أُعيدت285حالة متأثرة ببيانات الإصدار ونقطة التشغيل:275نجاحًا و8متخطاة وإخفاقان. اجتازت الحالات21التي كانت تفشل لغياب specify إعادة التحقق؛ بقي إخفاق عرض Rich وإخفاق stdio متوازٍ. التشخيص المحلي للمصافحة نجح، ثم اجتاز الاختبار الأصلي الكامل لـstdio منفردًا دون تغيير الأوراكل أو المهلة أو الشيفرة. السبب الدقيق لفشل التوازي غير محسوم؛ النجاح المنفرد لا يغلقه.

حصيلة **آخر الملاحظات المسجلة لكل معرف**: **{counts}**. لا تجمع المحاولات المتداخلة؛ [سجل الحالات](case-accounting.json) يربط كل نتيجة بمحاولتها وبيئتها. تبقى نجاحات غير متأثرة ضمن نطاق بيئتها الأولى50اعتمادًا، والاختبارات المتأثرة مثبتة على البيئة النهائية51توزيعًا. **لا ادعاء بإعادة كل الحالات في البيئة النهائية أو نجاح Full Suite موحد.** لا تُحوّل SKIPPED أو NOT_RUN إلى PASSED. [النتائج والأخطاء وأسباب التخطي](qualification-outcomes.json).

الإخفاقات11الباقية موزعة إلى7توقعات لكاتالوجات خارجية بلا Mock حتمي، و4Assertions لمسارات يلفها Rich. None من فاحص المراجع قد يعني «غير متحقق لتعذر الكاتالوج»؛ لا يثبت وحده تسرب community step. إصلاح Fixtures هذه الحالات أو ضبط عرض Console بصورة حتمية مع إبقاء Assertions المعنى والمسار والملفات يحتاج Write-set صالحًا للملفات الأخرى؛ لم يُنفذ. يبقى تعثر stdio المتوازي مخاطرة تحقق مستقلة رغم نجاحه المنفرد. لا نتيجة منتج نهائية تُستنتج من تلك التصنيفات.

أعداد QUAL-002 القديمة ما زالت غير موثقة بأصلها الخام؛ لم تُنسب النتائج الجديدة إليها. ملف Windows/Python3.12 لا يعوض مصفوفة Linux/macOS/Python الأخرى أو CodeQL، ولا يحسم التعارض المحمي بين الدستور وCI.

## حادثة عزل مسار الاختبارات

وُضع temp الأول داخل شجرة Git، فوصلت حالة بلا مستودع محلي إلى مستودع المهمة الأعلى عبر Git. تحوّل الفرع إلى `001-no-git` عند نفس10b5862. أُوقفت شجرة عمليات pytest المملوكة فقط عند اكتشاف ذلك. المحاولة `full-windows-001` هي `INCONCLUSIVE / SAFETY_INTERRUPTED`؛ لا تُستنتج أعداد نتائج من النقاط الظاهرة في stdout.

ثُبتت سلامة1,017 ملفًا خارج التصحيحات الأربعة وبقاء main والمرشح التاريخي، ثم أُعيد التبديل للفرع الأصلي دون reset أو تنظيف أو حذف. بقي الفرع العارض محفوظًا. صُحح مسار temp إلى نطاق المهمة الخارجي المحدد في [Write-set](external-temp-write-set.json)، وثُبت عدم وجود أي Git ancestor، ثم اجتاز اختبار PowerShell بلا Git دون تغير الفرع؛ تخطى نظيره Bash لعدم توفر مشغّل صالح. أُضيفت مراقبة توقف الاختبار عند انتقال غير متوقع لفرع المهمة. هذا إصلاح لمسار التحقق المحلي وليس تعديلًا لأدوات المنتج المشتركة.

## الحوكمة والحدود

اكتملت الحالات السلبية السبع المحجوبة سابقًا على WorkflowEngine الأصلي، مع8حالات أصلية و9متغيرات تشغيل بما فيها الرفض. الإيجابي القديم محفوظ ولم يُكرر لأنه غير متأثر. حققت البوابات المكوَّنة Pause عند غياب verdict، وفصلت نجاح check عن اختيار القبول، وأوقفت الأثر التالي عند reject/abort. لا تُعمم هذه النتيجة خارج المسارات المكوَّنة.

كشفت الحالات قدرة غير متوفرة للتحقق من صلاحية التفويض المنتهي، ودور يرسله المنفذ، واستقلال المراجع، وWrite-set، وربط نسخة الدليل. قبول `approve` في Gate هو مدخل تحكم، وليس إثبات هوية أو قبول مالك. رُصد أثر Fixture خارج نطاقه المعلن بعد التنفيذ وبقي داخل نطاق التجربة المصرح؛ هذا كشف بعدي من أداة التقييم، وليس sandbox في المنتج. [التقييم](dogfooding-assessment.json) يحتفظ بكل فجوة ويصنف حدودها، دون Policy Engine أو تنفيذ Core.

حُفظت محاولتا Headless الفاشلتان: الأولى وصلت إلى prompt وواجهت ترميز cp1252، والثانية أثبتت أن Windows NUL قد يعيد isatty=true. المحاولة الناجحة استخدمت stdin PIPE فارغًا. وحُفظت تسمية DF-N08 الخام FAIL مع [تصحيح تصنيف مستقل](dogfood-classification-correction.json): run هو aborted وGate نفسها failed والأثر التالي غائب، وهو الأوراكل الأصلي؛ لم يتغير الأوراكل أو تُعد الحالة.

## الفحوص المتبقية والقرارات

فحص Ruff المثبت في CI يتطلب **0.15.0**. لم تكن النسخة في المخبأ. صدر تفويض المالك اللاحق بتنزيل هذه الحزمة فقط من `https://pypi.org/simple/ruff/` و`https://files.pythonhosted.org`. طوبقت بصمة الملف و6بصمات RECORD داخل wheel، ثم ثُبت offline في بيئة أدوات مستقلة، دون تغيير بيئة pytest. نتيجة `ruff check src tests`: **{lint['result']}**. [الإيصال]({lint_path}). حُفظ فشل محاولة offline الأولى وفشل مساعد التدقيق الأول بسبب فواصل مسارات Windows داخل RECORD؛ صُحح تفسير المسارات الآمن دون إعادة تنزيل أو تخطي أي بصمة.

الأحكام الأربعة منفصلة في [الجاهزية](readiness-current.json): التأهيل التقني جزئي، الحوكمة جزئية مع فجوات، Core غير معتمد، وقبول المالك غير ممنوح. توجد [مصفوفة قرارات محدثة](OWNER_DECISIONS_AR.csv)، دون موافقات محددة سلفًا. إصلاح حالات جديدة خارج الملفات الأربعة أو تعديل سلطة/دستور/CI يحتاج نطاقًا صالحًا مستقلًا؛ لم تُعدل تلك الملفات.

## إعادة الإنتاج والمراجعة والحفظ

استخدم المفسر الصريح لهذه البيئة. ملفات stdout/stderr وreceipts وpytest-results تحفظ الأوامر وExit Codes والنسخ وبصمات المصادر. محاولة الاختبارات المتأثرة بدأت على98e6269 مع تصحيحات غير محفوظة بعد؛ بصماتها الأربعة تطابق commit10b5862 المثبت، ولا يُدعى أنها بدأت على Commit لاحق. محاولة البقية بدأت على10b5862. تغييرات الأدلة اللاحقة لا تغير المصدر المختبر.

المراجعة الوثائقية السابقة لا تعوض المراجعة التقنية الجديدة. ستثبت نتيجة المراجع المنفصل على مرشح الأدلة المحفوظ، مع حدود وصول إجرائية فقط، دون ادعاء عزل OS. الأدوات المحلية وFixtures تحفظها نسخة استعادة لاحقة؛ البيئات المعزولة نفسها ليست محتوى Git. لا Merge أو Push أو Release أو نشر أو تعديل إعدادات عامة أو بدء Majed Core.
'''
    (REPORT/'README_AR.md').write_text(readme,encoding='utf-8')
    # Existing detailed report is explicitly historical rather than silently current.
    old=(parent/'README_AR.md').read_text(encoding='utf-8')
    title,rest=old.split('\n',1)
    banner='\n**الحالة الحالية:** `PARTIAL_WITH_BLOCKERS` بعد تجهيز البيئة وتشغيل التأهيل. التفاصيل والأعداد الحالية في [ملحق الاستئناف](environment-recovery-001/README_AR.md) و[قرارات المالك الحالية](environment-recovery-001/OWNER_DECISIONS_AR.csv).\n\n> الأقسام أدناه سجل الجولة السابقة عند98e6269؛ أوصاف مانع Python والحفظ والمراجعة فيها تاريخية. لا تُستعمل بدل الملحق الحالي.\n'
    (parent/'README_AR.md').write_text(title+'\n'+banner+rest,encoding='utf-8')
    dump(ROOT/'specs/003-msk-baseline-closure/execution/STATE.json',{
        'request_id':'MSK-BASELINE-CLOSURE-003','status':'PARTIAL_WITH_BLOCKERS',
        'source_candidate':load('fix-checkpoint.json')['after'],'environment':'OFFLINE_DEPENDENCY_SCOPE_VERIFIED',
        'current_evidence':'docs/reviews/msk-baseline-closure-003/environment-recovery-001/readiness-current.json',
        'next_action':'Review actual failure/control/matrix/lint blockers; only separately scoped remedies. No Core/main merge/push.',
        'safe_stop':'All owned launched qualification processes finished; no running test left',
        'incidental_branch':'001-no-git retained; main and original ca3233a preserved',
        'updated_at_utc':datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'owner_report':str(REPORT/'README_AR.md'),'status':current['engineering_status'],'counts':counts}))

if __name__=='__main__':main()
