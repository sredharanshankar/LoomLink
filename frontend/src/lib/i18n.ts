import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import enCommon from "../locales/en/common.json";
import hiCommon from "../locales/hi/common.json";
import teCommon from "../locales/te/common.json";
import taCommon from "../locales/ta/common.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng: "en",
    supportedLngs: ["en", "hi", "te", "ta"],
    defaultNS: "common",
    ns: ["common", "ripple"],
    interpolation: { escapeValue: false },
    resources: {
      en: { common: enCommon, ripple: {} },
      hi: { common: hiCommon, ripple: {} },
      te: { common: teCommon, ripple: {} },
      ta: { common: taCommon, ripple: {} },
    },
  });

export default i18n;
