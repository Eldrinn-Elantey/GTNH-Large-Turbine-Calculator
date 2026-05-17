const TRANSLATIONS = {
  en: {
    nav_calculator:     "⚡ Calculator",
    nav_ehe:            "🔥 EHE Planner",
    nav_steam_gen:      "💧 Steam Gen",
    nav_fuels:          "⛽ Fuels",
    nav_rotors:         "🔩 Rotors",
    nav_settings:       "⚙ Settings",

    title_calculator:   "⚡ Calculator",
    title_ehe:          "🔥 EHE Planner",
    title_steam_gen:    "💧 Steam Gen",
    title_fuels:        "⛽ Fuels",
    title_rotors:       "🔩 Rotors",
    title_settings:     "⚙ Settings",

    label_mode:         "Mode:",
    label_fuel:         "Fuel:",
    label_flow:         "Flow:",
    label_rotor:        "Rotor:",
    label_blade_size:   "Blade Size:",
    label_dynamos:      "Dynamos:",
    label_plasma_type:  "Plasma type:",
    label_recipe_out:   "Recipe output (L):",
    label_recipe_time:  "Recipe time (s):",
    label_parallels:    "Parallels:",
    label_hot_fluid:    "Hot fluid:",

    result_opt_flow:       "Optimal flow:",
    result_output:         "Output EU/t:",
    result_dynamo_hatches: "Dynamo hatches:",
    result_eff_flow:       "Eff. flow:",
    result_eff_output:     "Eff. output:",
    result_rotor_eff:      "Rotor eff.:",
    result_lifetime:       "Lifetime:",
    result_plasma_ls:      "Plasma output L/s:",
    result_ehe_count:      "EHE count:",
    result_dense_sc_steam: "Dense SC steam L/t:",
    result_xl_turb:        "XL turbine count:",
    result_power_turb:     "Power/turbine EU/t:",
    result_dynamo_tier:    "Dynamo tier:",
    result_sc_steam:       "SC steam L/t:",
    result_sh_steam:       "SH steam L/t:",
    result_sc_turb:        "SC turbines:",
    result_sh_turb:        "SH turbines:",
    result_power_sc:       "Power/SC turb EU/t:",
    result_power_reg:      "Power/reg turb EU/t:",
    result_dynamo_sc:      "Dynamo (SC):",
    result_dynamo_reg:     "Dynamo (reg):",

    col_name:       "Display Name",
    col_tier:       "Tier",
    col_base_dur:   "Base Dur",
    col_overflow:   "Overflow",
    col_eff_tight:  "Eff Tight",
    col_eff_loose:  "Eff Loose",
    col_flow_tight: "Flow Tight (L/t)",
    col_flow_loose: "Flow Loose (L/t)",

    settings_font_size: "Font size:",
    settings_language:  "Language:",
    settings_small:     "Small",
    settings_medium:    "Medium",
    settings_large:     "Large",
    settings_en:        "English",
    settings_ru:        "Русский",
  },
  ru: {
    nav_calculator:     "⚡ Калькулятор",
    nav_ehe:            "🔥 EHE Планировщик",
    nav_steam_gen:      "💧 Генерация пара",
    nav_fuels:          "⛽ Топливо",
    nav_rotors:         "🔩 Роторы",
    nav_settings:       "⚙ Настройки",

    title_calculator:   "⚡ Калькулятор",
    title_ehe:          "🔥 EHE Планировщик",
    title_steam_gen:    "💧 Генерация пара",
    title_fuels:        "⛽ Топливо",
    title_rotors:       "🔩 Роторы",
    title_settings:     "⚙ Настройки",

    label_mode:         "Режим:",
    label_fuel:         "Топливо:",
    label_flow:         "Поток:",
    label_rotor:        "Ротор:",
    label_blade_size:   "Размер лопастей:",
    label_dynamos:      "Динамо:",
    label_plasma_type:  "Тип плазмы:",
    label_recipe_out:   "Выход рецепта (L):",
    label_recipe_time:  "Время рецепта (с):",
    label_parallels:    "Параллели:",
    label_hot_fluid:    "Горячая жидкость:",

    result_opt_flow:       "Оптим. поток:",
    result_output:         "Выход EU/t:",
    result_dynamo_hatches: "Лючки динамо:",
    result_eff_flow:       "Эфф. поток:",
    result_eff_output:     "Эфф. выход:",
    result_rotor_eff:      "КПД ротора:",
    result_lifetime:       "Ресурс:",
    result_plasma_ls:      "Выход плазмы L/s:",
    result_ehe_count:      "Кол-во EHE:",
    result_dense_sc_steam: "Густой SC пар L/t:",
    result_xl_turb:        "Кол-во XL турбин:",
    result_power_turb:     "Мощность/турбина EU/t:",
    result_dynamo_tier:    "Уровень динамо:",
    result_sc_steam:       "SC пар L/t:",
    result_sh_steam:       "SH пар L/t:",
    result_sc_turb:        "SC турбины:",
    result_sh_turb:        "SH турбины:",
    result_power_sc:       "Мощность/SC турб EU/t:",
    result_power_reg:      "Мощность/об. турб EU/t:",
    result_dynamo_sc:      "Динамо (SC):",
    result_dynamo_reg:     "Динамо (об.):",

    col_name:       "Название",
    col_tier:       "Уровень",
    col_base_dur:   "Базовый ресурс",
    col_overflow:   "Перегрузка",
    col_eff_tight:  "КПД Tight",
    col_eff_loose:  "КПД Loose",
    col_flow_tight: "Поток Tight (L/t)",
    col_flow_loose: "Поток Loose (L/t)",

    settings_font_size: "Размер шрифта:",
    settings_language:  "Язык:",
    settings_small:     "Маленький",
    settings_medium:    "Средний",
    settings_large:     "Большой",
    settings_en:        "English",
    settings_ru:        "Русский",
  },
};

const STORAGE_KEY = "gtnh-lang";
const SUPPORTED = ["en", "ru"];

let _lang = localStorage.getItem(STORAGE_KEY) ?? "en";
if (!SUPPORTED.includes(_lang)) _lang = "en";

export function getLang() { return _lang; }

export function setLang(lang) {
  if (!SUPPORTED.includes(lang)) return;
  _lang = lang;
  localStorage.setItem(STORAGE_KEY, lang);
}

export function t(key) {
  return TRANSLATIONS[_lang]?.[key] ?? TRANSLATIONS.en[key] ?? key;
}
