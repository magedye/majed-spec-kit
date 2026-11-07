# إعادة الإنتاج وحدود الدليل

المسار الأساسي: D:\APP\maged-spec-kit\majed-spec-kit. Worktree التنفيذ: specs/003-msk-baseline-closure/execution-worktree. المصدر f74bdb8 والمرشح التاريخيca3233a ثابتان فيGit؛ قارن الفرق دون checkout أوreset للشجرة المشتركة.

أوامر المحاولات المنفذة محفوظة كاملة في qualification-inventory collection_attempt وفي dogfooding-results actual_commands. المفسر الأول كان .venv/Scripts/python.exe داخل Worktree الخاص بهذه المحاولة، الذي أُنشئ قبل توضيح منع إنشاء بيئات لاحقًا، دونpip أو تنزيل. بعد التوضيح فُحصت المفسرات القائمة فقط. لا تعِد إنشاء بيئة أو تثبيت شيء بموجب هذا التسليم.

مجموعة الأدلة المحلية الأولية: specs/003-msk-baseline-closure/execution في الشجرة الأساسية. بقيت أصلًا محفوظًا، ثم نُسخت بايتاتها إلى specs/003-msk-baseline-closure/execution داخل Worktree. سجل CUSTODY_RELOCATION يحفظ بصمات النسخ وتغيير مسار الأدوات اللاحق فقط. الأدوات preflight.py وqualify.py وdiagnose.py وdogfood.py وreconcile.py وpackage_review.py محلية، ليست خدمات أو سجل سلطة، ولا تحفظهاGit تلقائيًا. الإيصال النهائي يسمي نسخة استعادة كاملة لها.

qualify.py: يثبت حزم pyproject منmetadata ثم يستدعيpytest tests --collect-only -q -p no:cacheprovider مع PYTHONPATH لمسارsrc الصحيح وتعطيلautoload إضافات المضيف. النتيجة الحالية Exit4/readchar؛ لا تشغل suites متكررة قبل إصلاح شروط البيئة بموجب تفويض صالح.

diagnose.py: يستخرج النص الحرفي للموزع القياسي الموجود من AST فيGit، ويتحقق من تطابقه بيننسختين، ثم يفحص7حدود محددة. لا يعدل أو يستبدل محلل الحزمة. يشغّل أمرَيcmd ثابتين وConsole Rich فقط. dogfood.py: يجمد الأوراكل ثم يستخدم setup_plan/check_prerequisites الأصليين فيfixture معزول، وunittest واحد قبل/بعد، وحارس prerequisite فاشل. النتيجة ليست تأهيل WorkflowEngine أو المضيف.

المحاولات تنشئ مجلدات بأسماء ثابتة معexist_ok=False لمنع استبدال الأدلة. لإعادة مستقبلية صالحة: احفظ النسخة الأصلية، واستخدم نسخة أدوات بمحاولة/fixture ID جديدين داخل النطاق المحلي المعين، وثبت بصماتها ومدخلاتها قبل التنفيذ. أي إعادة تغير الافتراضات أو المصدر أو البيئة تحصل على إيصال جديد، ولا تستبدل PASS/FAIL سابقًا. الاستعادة فقط إلى مسارات مفقودة بعد تحققSHA256؛ لاحذف أو تنظيف أو overwrite تلقائي.
