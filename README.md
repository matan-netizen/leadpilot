# LeadPilot — ניהול לידים + מענה חכם

<div dir="rtl">

דאשבורד לניהול לידים עם **מענה חכם בוואטסאפ** ו**עוזר מכירות AI** (Claude). משפך מכירה, "לטיפול היום", טבלה עם חיפוש וסינון, לוח Kanban עם גרירה, כרטיס ליד עם היסטוריה – ולכל ליד שכתב לנו, טיוטת תשובה מוכנה לשליחה בלחיצה.

> נבנה על בסיס [Bakery Copilot](https://github.com/MaceTenth/bakery-copilot) מהשיעורים (FastAPI · לולאת סוכן עם כלים · Postgres · cron על Railway), בעיצוב ובסגנון של [Dashboard - Leads](https://github.com/seomr2018-del/Dashboard---Leads---3).

| מסמך | תוכן |
|---|---|
| [spec.md](spec.md) | מה בונים – מקור האמת |
| [architecture.md](architecture.md) | איך ואיפה, והחלטות |
| [practice.md](practice.md) · [runbook.md](runbook.md) | תהליך עבודה · כשמשהו נשבר |

## מה יש בפנים

| לשונית | מה עושים בה |
|---|---|
| **סקירה** | 6 כרטיסי KPI, משפך לפי שלב, פילוח לפי סטטוס, לטיפול היום, ממתינים למענה, איכות נתונים |
| **לידים** | טבלה: חיפוש (שם / טקסט / טלפון בכל פורמט), שלב, סטטוס, 🔥 חמים · 💬 ממתינים · ⏳ לא עודכנו · 👥 כפולים, מיון, CSV |
| **לוח** | Kanban של 6 שלבים – גרירה משנה סטטוס ונשמרת |
| **מענה חכם** | ההודעה האחרונה מהליד → Claude מנסח תשובה (חם / קצר / רשמי), מזהה כוונה ומציע סטטוס → עריכה → שליחה בוואטסאפ + עדכון הליד |
| **עוזר AI** | צ'אט שרואה את הלידים בזמן אמת: "מה לטפל היום?", "נסח מענה לדוד", "דיברתי עם רועי, שלחתי הצעה – תעדכן" |
| **תבניות וואטסאפ** | התבניות לפי סוג ליד, עם העתקה |

ועוד: מצב כהה, RTL מלא, מובייל מ-390px, היסטוריית פעילות לכל ליד, סיכום בוקר יומי (cron), מגבלות שימוש ותקציב יומי.

**בלי מפתח API?** הכול עובד – המענה החכם והעוזר עוברים ל"מצב כללים" (מסווג כוונות + תבניות). מוסיפים `ANTHROPIC_API_KEY` ו-Claude נכנס לפעולה.

## הרצה מקומית

```bash
cp .env.example .env         # APP_PASSWORD, APP_SECRET, ואופציונלית ANTHROPIC_API_KEY
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

http://localhost:8000 → שם + הסיסמה. בהפעלה הראשונה נטענים 32 לידי דמה ו-7 תבניות.

## בדיקות

```bash
pytest -q                    # 49 בדיקות, המודל מדומה, בלי מפתח
python -m evals.run          # המודל האמיתי מול evals/cases.yaml
```

## פריסה ב-Railway

1. Project → **Deploy from GitHub repo** → הריפו הזה (שירות `web`). Railpack בונה מ-`requirements.txt` ו-`.python-version`.
2. **+ New → Database → PostgreSQL**.
3. משתני הסביבה של `web`:

| משתנה | ערך |
|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `APP_ENV` | `production` |
| `APP_PASSWORD` | סיסמת הצוות |
| `APP_SECRET` | `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | אופציונלי – בלעדיו מצב כללים |
| `MODEL` | `claude-opus-5-5` (או `claude-sonnet-5-5` לחיסכון) |
| `BUSINESS_NAME` | שם העסק שלכם |

4. Settings: Start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, Healthcheck `/health` (או `railway config apply` מ-`.railway/railway.ts`). Networking → **Generate Domain**.
5. אופציונלי: שירות `digest` מאותו ריפו עם `python -m app.digest` ו-cron `30 4 * * *`.

## מבנה

```
app/            main.py (API) · agent.py (לולאת הסוכן) · offline.py (מצב כללים) · smart_reply.py
                leads_meta.py (סטטוסים, שלבים, טלפונים, מדדים) · tools/ · db.py · digest.py
app/prompts/    system.md (העוזר) · smart_reply.md (המענה החכם)
static/         הממשק: HTML · CSS · JS, בלי build
data/           leads.json · templates.json (נתוני דמה)
tests/ evals/   pytest · מקרי הערכה למודל
```

</div>
