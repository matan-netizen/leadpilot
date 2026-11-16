# פריסה ב-Railway – מדריך מלא

<div dir="rtl">

המדריך מתאר את הפריסה כפי שהיא רצה בפועל: שירות `web` אחד (UI + API) ו-Postgres, נבנה על ידי Railpack מ-`requirements.txt` ו-`.python-version`, בלי Dockerfile.

## 1. פרויקט ושירותים
1. ב-Railway: **New Project → Deploy from GitHub repo** → `matan-netizen/leadpilot`. השירות שנוצר הוא `web`.
   - אם הריפו לא מופיע: Account Settings → Integrations → GitHub, ולתת לאפליקציית Railway גישה לריפו.
2. **+ New → Database → PostgreSQL**.

## 2. הגדרות השירות `web` (Settings)
| הגדרה | ערך |
|---|---|
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Healthcheck Path | `/health` (timeout 120) |
| Restart Policy | On Failure, 5 ניסיונות |
| Networking | **Generate Domain** |

אפשר לקבל את אותן הגדרות מהקוד: `npm install --prefix .railway` ואז `railway config plan` / `railway config apply` (הקובץ `.railway/railway.ts`).

## 3. משתנים (Variables) של `web`
| משתנה | ערך | חובה |
|---|---|---|
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` | כן |
| `APP_ENV` | `production` | כן |
| `APP_PASSWORD` | סיסמת הצוות | כן |
| `APP_SECRET` | `openssl rand -hex 32` | כן |
| `ANTHROPIC_API_KEY` | מפתח מ-platform.claude.com | לא – בלעדיו "מצב כללים" |
| `MODEL` | `claude-opus-5-5` (או `claude-sonnet-5-5` לחיסכון) | לא |
| `BUSINESS_NAME` | שם העסק | לא |
| `DAILY_CAP_USD` | `3.00` | לא |
| `TIMEZONE` | `Asia/Jerusalem` | לא |

אחרי שינוי משתנים Railway מציג פס סגול **"Apply changes"** – צריך ללחוץ **Deploy** כדי שהשינוי ייכנס לתוקף.

## 4. בדיקה אחרי פריסה
1. בלוגים של הפריסה: `seed report: … templates_seeded: 7, leads_seeded: 32` (בפריסה הראשונה), ו-`GET /health 200`.
2. באתר: כניסה עם סיסמה שגויה → "סיסמה שגויה."; עם הנכונה → הדאשבורד.
3. בכותרת: תגית כחולה **"מענה חכם: Claude"** (או צהובה "מצב כללים" אם אין מפתח, או כתומה עם סיבה אם יש בעיה בחשבון ה-API).
4. עוזר AI → "מה לטפל היום?" → תשובה עם תגי כלים ירוקים.
5. לשונית מענה חכם → **צור מענה** → "נוסח ע״י Claude".

## 5. פריסה רציפה ו-Rollback
- כל push ל-`main` נבנה ונפרס אוטומטית; CI ב-GitHub מריץ lint ו-55 בדיקות על אותו commit.
- Rollback: Deployments → פריסה קודמת → **Redeploy**.

## 6. תקלות נפוצות
| מה רואים | סיבה | פתרון |
|---|---|---|
| הבנייה נכשלה עם `504 Gateway Timeout` בהורדת mise | תקלה זמנית אצל GitHub/Railway | Redeploy |
| `/health` מחזיר 503 עם `db: …` | `DATABASE_URL` לא מוגדר כהפניה ל-Postgres | להגדיר `${{Postgres.DATABASE_URL}}` |
| הודעה "אין מספיק קרדיט בחשבון ה-API" | אין יתרה בחשבון Anthropic | להוסיף קרדיט ב-Plans & Billing |
| "מפתח ה-API לא תקין" | מפתח שגוי או עם רווח | לעדכן `ANTHROPIC_API_KEY` |
| השירות לא התעדכן אחרי push | ה-webhook של GitHub לא הגיע | Settings → Source → לחבר מחדש, או Deploy ידני |

## 7. עלות (נובמבר 2026)
| רכיב | הערכה |
|---|---|
| Railway – web + Postgres | ‎$4–6 לחודש |
| Claude – 300 פניות ביום | ‎~$18 לחודש ב-Opus, ‎~$9 ב-Sonnet |

הבלמים: `DAILY_CAP_USD` (תקרה יומית), `RATE_LIMIT_PER_HOUR` (למשתמש), `HISTORY_LIMIT` (גודל ההקשר).

</div>
