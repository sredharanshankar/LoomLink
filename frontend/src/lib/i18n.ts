import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

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
      en: {
        common: {
          save: "Save",
          cancel: "Cancel",
          confirm: "Confirm",
          loading: "Loading…",
          error: "Error",
          success: "Success",
          search: "Search",
          noResults: "No results",
          login: "Log In",
          logout: "Log Out",
          dashboard: "Dashboard",
          inventory: "Inventory",
          orders: "Orders",
          production: "Production",
          quality: "Quality",
          dispatch: "Dispatch",
          workers: "Workers",
          finance: "Finance",
          ripple: "Ripple",
          admin: "Admin",
          scanPin: "Scan / PIN",
          settings: "Settings",
          employee_code: "Employee ID",
          password: "Password",
          pin: "6-digit PIN",
          loginWith: "Log in with {{method}}",
        },
        ripple: {},
      },
      hi: { common: { login: "लॉग इन", dashboard: "डैशबोर्ड" }, ripple: {} },
      te: { common: { login: "లాగిన్", dashboard: "డాష్‌బోర్డ్" }, ripple: {} },
      ta: { common: { login: "உள்நுழைவு", dashboard: "டாஷ்போர்டு" }, ripple: {} },
    },
  });

export default i18n;