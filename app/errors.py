"""Every error the user can see, explained in plain Hebrew: what happened, whose side it is on, what to do.

The point: someone testing the app (a lecturer, a client) must be able to tell
a payment or account setting apart from a bug in the system. Each explanation
names the source (Anthropic, the API account, a limit we set on purpose, or
the system itself) and the fix.
"""
from __future__ import annotations

from dataclasses import dataclass

from .config import settings

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Explained:
    code: str        # stable id, also stored in runs.error
    title: str       # what happened
    source: str      # whose side: "תשלום" / "הגדרות חשבון" / "Anthropic" / "רשת" / "מגבלה מכוונת" / "המערכת"
    action: str      # what to do
    account: bool = False   # the API account itself is unusable → stop calling it for a while
    transient: bool = False  # will likely pass by itself

    @property
    def not_a_bug(self) -> bool:
        return self.source != "המערכת"

    def text(self) -> str:
        tail = "זו לא תקלה במערכת." if self.not_a_bug else "השגיאה נרשמה בטבלת runs."
        return f"{self.title}. מקור: {self.source}. {tail} {self.action}"

    def short(self) -> str:
        return f"{self.title} ({self.source})"


def _msg(exc: Exception) -> str:
    return str(getattr(exc, "message", "") or exc).lower()


def explain(exc: Exception) -> Explained:
    """Classify any exception from the model call into a human explanation."""
    model = settings.model
    if anthropic is not None:
        m = _msg(exc)
        if isinstance(exc, anthropic.BadRequestError) and ("credit" in m or "billing" in m or "balance" in m):
            return Explained("no_credit", "אין מספיק קרדיט בחשבון ה-API של Anthropic", "תשלום",
                             "בעל החשבון צריך להוסיף קרדיט ב-platform.claude.com ← Plans & Billing. "
                             "בינתיים המערכת עונה במצב כללים, ו-Claude יחזור לבד תוך 5 דקות מהתשלום.", account=True)
        if isinstance(exc, anthropic.AuthenticationError):
            return Explained("bad_key", "מפתח ה-API של Anthropic לא תקין או בוטל", "הגדרות חשבון",
                             "יש לעדכן את המשתנה ANTHROPIC_API_KEY ב-Railway. בינתיים המערכת עונה במצב כללים.", account=True)
        if isinstance(exc, getattr(anthropic, "PermissionDeniedError", ())):
            return Explained("no_permission", f"למפתח ה-API אין הרשאה להשתמש במודל {model}", "הגדרות חשבון",
                             "יש לבדוק את הרשאות המפתח ב-platform.claude.com, או לשנות את MODEL ב-Railway.", account=True)
        if isinstance(exc, getattr(anthropic, "NotFoundError", ())):
            return Explained("model_not_found", f"המודל {model} לא זמין בחשבון הזה", "הגדרות חשבון",
                             "יש לשנות את המשתנה MODEL ב-Railway למודל זמין (למשל claude-sonnet-5-5).", account=True)
        if isinstance(exc, anthropic.RateLimitError):
            return Explained("rate_limited", "חרגנו ממגבלת הקצב של חשבון ה-API", "Anthropic",
                             "זו מגבלה של Anthropic לפי רמת החשבון. מספיק לנסות שוב בעוד דקה.", transient=True)
        status = getattr(exc, "status_code", None)
        if status == 529 or "overloaded" in m:
            return Explained("overloaded", "השרתים של Anthropic עמוסים כרגע", "Anthropic",
                             "עומס זמני אצל Anthropic. מספיק לנסות שוב בעוד דקה.", transient=True)
        if isinstance(exc, getattr(anthropic, "APITimeoutError", ())):
            return Explained("timeout", "Anthropic לא ענתה בזמן", "Anthropic",
                             "עיכוב זמני. מספיק לנסות שוב.", transient=True)
        if isinstance(exc, anthropic.APIConnectionError):
            return Explained("no_connection", "אין חיבור לשרתי Anthropic", "רשת",
                             "תקלת רשת זמנית בין השרת ל-Anthropic. מספיק לנסות שוב בעוד רגע.", transient=True)
        if isinstance(status, int) and status >= 500:
            return Explained("anthropic_down", "תקלה זמנית בשרתי Anthropic", "Anthropic",
                             "אפשר לבדוק ב-status.anthropic.com. מספיק לנסות שוב בעוד כמה דקות.", transient=True)
        if isinstance(exc, anthropic.BadRequestError):
            return Explained("rejected", "Anthropic דחתה את הבקשה", "Anthropic",
                             "לרוב זה בגלל תוכן ההודעה או תמונה לא נתמכת. נסו לנסח אחרת.")
    return Explained("internal", "שגיאה לא צפויה בשרת", "המערכת", "נסו שוב; אם זה חוזר, הפרטים נמצאים בלוגים.")


# Our own limits: deliberate brakes, not bugs.
def daily_cap_text(cap: float) -> str:
    return (f"התקציב היומי לשימוש ב-Claude (${cap:.2f}) נוצל. מקור: מגבלה מכוונת. זו לא תקלה במערכת – "
            "זה בלם עלויות שהוגדר מראש (DAILY_CAP_USD) ומתאפס בחצות. הדאשבורד ממשיך לעבוד כרגיל.")


def rate_limit_text(used: int, limit: int) -> str:
    return (f"שלחת {used} הודעות לעוזר בשעה האחרונה; המגבלה היא {limit}. מקור: מגבלה מכוונת. זו לא תקלה במערכת – "
            "זו הגנה מפני שימוש יתר (RATE_LIMIT_PER_HOUR). אפשר לנסות שוב מאוחר יותר.")
