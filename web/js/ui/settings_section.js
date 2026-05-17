import { t, getLang, setLang } from "../i18n.js";
import { getFontSize, setFontSize } from "../settings.js";

export function initSettings(el) {
  const curFont = getFontSize();
  const curLang = getLang();

  el.innerHTML = `
    <h2 class="section-title">${t("title_settings")}</h2>
    <div class="card card-narrow">
      <div class="setting-row">
        <span class="setting-label">${t("settings_font_size")}</span>
        <select id="setting-font">
          <option value="small"  ${curFont === "small"  ? "selected" : ""}>${t("settings_small")}</option>
          <option value="medium" ${curFont === "medium" ? "selected" : ""}>${t("settings_medium")}</option>
          <option value="large"  ${curFont === "large"  ? "selected" : ""}>${t("settings_large")}</option>
        </select>
      </div>
      <div class="setting-row">
        <span class="setting-label">${t("settings_language")}</span>
        <select id="setting-lang">
          <option value="en" ${curLang === "en" ? "selected" : ""}>${t("settings_en")}</option>
          <option value="ru" ${curLang === "ru" ? "selected" : ""}>${t("settings_ru")}</option>
        </select>
      </div>
    </div>
  `;

  el.querySelector("#setting-font").addEventListener("change", e => {
    setFontSize(e.target.value);
  });

  el.querySelector("#setting-lang").addEventListener("change", e => {
    setLang(e.target.value);
    document.dispatchEvent(new CustomEvent("gtnh:lang-change"));
  });
}
