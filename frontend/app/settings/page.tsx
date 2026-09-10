"use client";
import { useLang } from "@/app/providers";
import { t } from "@/lib/i18n";

export default function SettingsPage() {
  const { lang, setLang } = useLang();
  return (
    <div>
      <h1>{t("settings", lang)}</h1>
      <div className="card">
        <label>
          {t("language", lang)}{" "}
          <select value={lang} onChange={(e) => setLang(e.target.value as "en" | "ar")}>
            <option value="en">English</option>
            <option value="ar">العربية</option>
          </select>
        </label>
        <p className="muted" style={{ marginTop: 12 }}>
          Risk profile, investment objectives, and KYC-lite onboarding are captured here and drive
          model-portfolio suggestions and suitability checks (advisory-only; no personalized
          buy/sell language unless licensed and segmented).
        </p>
      </div>
    </div>
  );
}
