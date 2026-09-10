// Minimal EN/AR dictionary + direction helper. In production, wire a full i18n
// framework; regulated disclaimers come from the backend already translated.
import type { Lang } from "./api";

type Dict = Record<string, { en: string; ar: string }>;

const STRINGS: Dict = {
  appName: { en: "Wealth Intelligence AI", ar: "الذكاء الاستثماري للثروات" },
  dashboard: { en: "Dashboard", ar: "لوحة التحكم" },
  assets: { en: "Assets", ar: "الأصول" },
  portfolios: { en: "Portfolios", ar: "المحافظ" },
  reports: { en: "Reports", ar: "التقارير" },
  settings: { en: "Settings", ar: "الإعدادات" },
  observed: { en: "Observed facts", ar: "حقائق ملحوظة" },
  derived: { en: "Derived metrics", ar: "مقاييس مشتقة" },
  narrative: { en: "AI narrative", ar: "سرد الذكاء الاصطناعي" },
  source: { en: "Source", ar: "المصدر" },
  methodology: { en: "Methodology", ar: "المنهجية" },
  speculative: { en: "Speculative / scenario", ar: "تقديري / سيناريو" },
  analyze: { en: "Analyze", ar: "تحليل" },
  deepDive: { en: "AI deep-dive", ar: "تحليل معمّق بالذكاء الاصطناعي" },
  riskMetrics: { en: "Risk metrics", ar: "مقاييس المخاطر" },
  language: { en: "Language", ar: "اللغة" },
  auditTrail: { en: "Audit trail", ar: "سجل التدقيق" },
  disclaimer: { en: "Disclaimer", ar: "إخلاء المسؤولية" },
  login: { en: "Log in", ar: "تسجيل الدخول" },
};

export function t(key: keyof typeof STRINGS | string, lang: Lang): string {
  const entry = STRINGS[key as keyof typeof STRINGS];
  return entry ? entry[lang] : (key as string);
}

export function dir(lang: Lang): "rtl" | "ltr" {
  return lang === "ar" ? "rtl" : "ltr";
}
