"use client";
import Link from "next/link";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";

export function Nav() {
  const { lang, setLang } = useLang();
  return (
    <nav className="nav">
      <span className="brand">{t("appName", lang)}</span>
      <Link href="/">{t("dashboard", lang)}</Link>
      <Link href="/portfolios">{t("portfolios", lang)}</Link>
      <Link href="/reports">{t("reports", lang)}</Link>
      <Link href="/settings">{t("settings", lang)}</Link>
      <select
        aria-label={t("language", lang)}
        value={lang}
        onChange={(e) => setLang(e.target.value as "en" | "ar")}
      >
        <option value="en">English</option>
        <option value="ar">العربية</option>
      </select>
    </nav>
  );
}
