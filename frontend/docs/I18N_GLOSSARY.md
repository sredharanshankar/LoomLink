# LoomLink i18n Glossary

Every status value, action button, unit label and error code used in the UI,
translated into English, Hindi, Telugu and Tamil.
Strings are short and natural for factory-floor workers.

---

## 1. Machine Status (`MachineStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `idle` | Idle | बंद | ఆగి ఉంది | நின்று இருக்கும் |
| `running` | Running | चल रहा है | నడుస్తోంది | ஓடுகிறது |
| `breakdown` | Breakdown | खराब | పాడైంది | பழுதாகியது |
| `maintenance` | Maintenance | मरम्मत | మెయింటనెన్స్ | பராமரிப்பில் உள்ளது |

---

## 2. Job Status (`JobStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `queued` | Queued | कतार में | క్యూలో ఉంది | வரிசையில் உள்ளது |
| `in_progress` | In Progress | चल रहा है | జరుగుతోంది | நடக்கிறது |
| `paused` | Paused | रुका हुआ | ఆపబడింది | இடைநிறுத்தப்பட்டது |
| `completed` | Completed | पूरा हुआ | పూర్తయింది | முடிந்தது |
| `cancelled` | Cancelled | रद्द | రద్దు | ரத்து |

---

## 3. Order Status (`OrderStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `draft` | Draft | मसौदा | డ్రాఫ్ట్ | வரைவு |
| `confirmed` | Confirmed | पक्का | నిర్ధారించబడింది | உறுதிப்படுத்தப்பட்டது |
| `in_production` | In Production | उत्पादन में | ఉత్పత్తిలో ఉంది | உற்பத்தியில் உள்ளது |
| `completed` | Completed | पूरा | పూర్తయింది | முடிந்தது |
| `dispatched` | Dispatched | भेजा गया | పంపబడింది | அனுப்பப்பட்டது |
| `closed` | Closed | बंद | మూసివేయబడింది | மூடப்பட்டது |
| `cancelled` | Cancelled | रद्द | రద్దు | ரத்து |

---

## 4. Order Priority (`OrderPriority`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `low` | Low | कम | తక్కువ | குறைந்த |
| `normal` | Normal | सामान्य | సాధారణ | சாதாரண |
| `high` | High | अधिक | ఎక్కువ | அதிக |
| `urgent` | Urgent | जरूरी | అత్యవసరం | அவசரம் |

---

## 5. Roll / QC Status (`RollStatus`, `QcDecision`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `pending_qc` | Pending QC | जाँच बाकी | QC పెండింగ్ | QC நிலுவையில் உள்ளது |
| `passed` | Passed | पास | పాస్ | தேர்ச்சி |
| `rework` | Rework | दोबारा काम | రీవర్క్ | மறுவேலை |
| `rejected` | Rejected | अस्वीकार | తిరస్కరించబడింది | நிராகரிக்கப்பட்டது |
| `pass` | Pass | पास | పాస్ | தேர்ச்சி |
| `rework` | Rework | दोबारा काम | రీవర్క్ | மறுவேலை |
| `reject` | Reject | अस्वीकार | తిరస్కరించు | நிராகரி |

---

## 6. Defect Severity (`DefectSeverity`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `minor` | Minor | मामूली | చిన్న | சிறிய |
| `major` | Major | बड़ा | పెద్ద | பெரிய |
| `critical` | Critical | गंभीर | తీవ్రమైన | தீவிரமான |

---

## 7. Dispatch Status (`DispatchStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `pending` | Pending | बाकी | పెండింగ్ | நிலுவையில் உள்ளது |
| `dispatched` | Dispatched | भेजा गया | పంపబడింది | அனுப்பப்பட்டது |
| `delivered` | Delivered | पहुँचाया | అందించబడింది | வழங்கப்பட்டது |

---

## 8. Invoice Status (`InvoiceStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `unpaid` | Unpaid | बकाया | చెల్లించబడలేదు | செலுத்தப்படவில்லை |
| `partial` | Partial | आधा | పాక్షిక | பகுதியளவு |
| `paid` | Paid | भुगतान हुआ | చెల్లించబడింది | செலுத்தப்பட்டது |
| `overdue` | Overdue | देर से | గడువు దాటింది | காலதாமதமானது |

---

## 9. Yarn Batch Status (`BatchStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `in_use` | In Use | उपयोग में | వాడుతున్నారు | பயன்பாட்டில் உள்ளது |
| `exhausted` | Exhausted | खत्म | అయిపోయింది | தீர்ந்துவிட்டது |

---

## 10. Attendance Status (`AttendanceStatus`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `present` | Present | उपस्थित | హాజరు | வருகை |
| `absent` | Absent | अनुपस्थित | గైరుహాజరు | வருகையில்லை |
| `half_day` | Half Day | आधा दिन | సగం రోజు | அரை நாள் |

---

## 11. Wage Type (`WageType`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `daily` | Daily | रोज | రోజువారి | தினமும் |
| `piece` | Per Piece | प्रति नग | ముక్కకు | ஒரு நிறைக்கு |
| `hourly` | Per Hour | प्रति घंटा | గంటకు | ஒரு மணி நேரத்திற்கு |

---

## 12. Production Stage (`Stage`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `spinning` | Spinning | कताई | వడకడం | நூற்பு |
| `weaving` | Weaving | बुनाई | నేత | நெசவு |
| `dyeing` | Dyeing | रंगाई | రంగు వేయడం | சாயமிடல் |
| `finishing` | Finishing | फिनिशिंग | ముగింపు | முடிப்பு |

---

## 13. Health / Ripple (`Health`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `green` | On Track | ठीक है | సరిగ్గా ఉంది | சரியாக உள்ளது |
| `amber` | At Risk | खतरे में | ప్రమాదంలో ఉంది | ஆபத்தில் உள்ளது |
| `red` | Late | देरी | ఆలస్యం | தாமதம் |

---

## 14. Shift (`Shift`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `A` | Shift A (6am–2pm) | पाली A | షిఫ్ట్ A | பாளி A |
| `B` | Shift B (2pm–10pm) | पाली B | షిఫ్ట్ B | பாளி B |
| `C` | Shift C (Night) | पाली C (रात) | రాత్రి షిఫ్ట్ C | இரவு பாளி C |

---

## 15. Stock Movement Kind (`MovementKind`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `receive` | Received | प्राप्त | స్వీకరించింది | பெறப்பட்டது |
| `issue` | Issued | जारी | జారీ చేయబడింది | வழங்கப்பட்டது |
| `return` | Returned | वापसी | వాపసు | திரும்பியது |
| `adjust_in` | Adjust In | जमा | అడ్జస్ట్ జమ | சேர்க்கை |
| `adjust_out` | Adjust Out | कटौती | అడ్జస్ట్ తీసివేత | கழிக்கை |

---

## 16. Role (`Role`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `owner` | Owner | मालिक | యజమాని | உரிமையாளர் |
| `manager` | Manager | मैनेजर | మేనేజర్ | மேலாளர் |
| `storekeeper` | Storekeeper | स्टोर कीपर | స్టోర్ కీపర్ | கிடங்கு காப்பாளர் |
| `operator` | Operator | ऑपरेटर | ఆపరేటర్ | இயக்குநர் |
| `qc_inspector` | QC Inspector | QC निरीक्षक | QC తనిఖీదారు | QC ஆய்வாளர் |
| `dispatch` | Dispatch | डिस्पैच | డిస్పాచ్ | அனுப்பீடு |
| `accounts` | Accounts | खाता | అకౌంట్స్ | கணக்கு |
| `buyer` | Buyer | खरीदार | కొనుగోలుదారు | வாங்குபவர் |

---

## 17. Unit Labels (`Unit`)

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `kg` | kg | किलो | కిలో | கிலோ |
| `m` | m | मीटर | మీటర్ | மீட்டர் |
| `roll` | roll | रोल | రోల్ | ரோல் |
| `piece` | piece | नग | ముక్క | நிறை |
| paise | ₹ (paise) | पैसे | పైసలు | பைசா |
| `cm` | cm | सेमी | సెంటీమీటర్ | செ.மீ |
| `g` | g (grams) | ग्राम | గ్రాములు | கிராம் |
| `m/h` | m/h | मीटर/घंटा | మీటర్/గంట | மீ/மணி |
| `kg/h` | kg/h | किलो/घंटा | కిలో/గంట | கிலோ/மணி |
| `/day` | /day | /दिन | /రోజు | /நாள் |
| `/hour` | /hour | /घंटा | /గంట | /மணி |
| `/m` | /m | /मीटर | /మీటర్ | /மீட்டர் |

---

## 18. Action Buttons

| Key | English | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `confirm_order` | Confirm Order | ऑर्डर पक्का करें | ఆర్డర్ నిర్ధారించు | ஆர்டர் உறுதிப்படுத்து |
| `start_job` | Start Job | काम शुरू करें | పని మొదలు పెట్టు | வேலை தொடங்கு |
| `pause_job` | Pause Job | काम रोकें | పని ఆపు | வேலை இடைநிறுத்து |
| `resume_job` | Resume Job | काम फिर शुरू करें | పని తిరిగి మొదలు పెట్టు | வேலை மீண்டும் தொடங்கு |
| `complete_job` | Complete Job | काम पूरा करें | పని పూర్తి చేయి | வேலை முடி |
| `report_breakdown` | Report Breakdown | खराबी बताएं | పాడవడం రిపోర్ట్ చేయి | பழுது தெரிவி |
| `log_progress` | Log Progress | प्रगति दर्ज करें | పురోగతి రికార్డ్ చేయి | முன்னேற்றம் பதிவு செய் |
| `create_roll` | Create Roll | रोल बनाएं | రోల్ తయారు చేయి | ரோல் உருவாக்கு |
| `inspect_roll` | Inspect Roll | रोल जाँचें | రోల్ తనిఖీ చేయి | ரோல் ஆய்வு செய் |
| `pass_roll` | Pass | पास करें | పాస్ చేయి | தேர்ச்சி |
| `rework_roll` | Send for Rework | दोबारा भेजें | రీవర్క్ కి పంపించు | மறுவேலைக்கு அனுப்பு |
| `reject_roll` | Reject | अस्वीकार करें | తిరస్కరించు | நிராகரி |
| `dispatch_order` | Dispatch | भेजें | పంపు | அனுப்பு |
| `receive_yarn` | Receive Yarn | धागा लें | దారం స్వీకరించు | நூல் பெறு |
| `issue_yarn` | Issue Yarn | धागा दें | దారం జారీ చేయి | நூல் வழங்கு |
| `save_draft` | Save Draft | मसौदा सेव करें | డ్రాఫ్ట్ సేవ్ చేయి | வரைவு சேமி |
| `cancel` | Cancel | रद्द करें | రద్దు చేయి | ரத்து செய் |
| `close_order` | Close Order | ऑर्डर बंद करें | ఆర్డర్ మూసివేయి | ஆர்டர் மூடு |
| `mark_paid` | Mark Paid | भुगतान हो गया | చెల్లించినట్టు మార్క్ చేయి | செலுத்தியதாக குறி |
| `run_ripple` | Run Ripple | रिपल चलाएं | రిప్పిల్ రన్ చేయి | ரிப்பிள் இயக்கு |
| `apply_fix` | Apply Fix | समाधान लागू करें | పరిష్కారం అమలు చేయి | தீர்வு செயல்படுத்து |
| `check_in` | Check In | हाजिरी दें | హాజరు మార్క్ చేయి | வருகை பதிவு செய் |
| `add_overtime` | Add Overtime | ओवरटाइम जोड़ें | ఓవర్ టైమ్ జోడించు | மேலதிக நேரம் சேர் |

---

## 19. Error Codes (CONTRACT §3.5)

| Code | English message | Hindi | Telugu | Tamil |
|---|---|---|---|---|
| `VALIDATION_ERROR` | Invalid input | गलत इनपुट | తప్పు ఇన్పుట్ | தவறான உள்ளீடு |
| `NOT_FOUND` | Not found | नहीं मिला | కనుగొనబడలేదు | காணப்படவில்லை |
| `FORBIDDEN` | Not allowed | अनुमति नहीं | అనుమతి లేదు | அனுமதி இல்லை |
| `CONFLICT` | Already exists | पहले से है | ఇప్పటికే ఉంది | ஏற்கனவே உள்ளது |
| `MACHINE_BUSY` | Machine is busy | मशीन व्यस्त है | మెషిన్ బిజీగా ఉంది | இயந்திரம் பிஸியாக உள்ளது |
| `YARN_INSUFFICIENT` | Not enough yarn | धागा कम है | దారం తక్కువగా ఉంది | நூல் போதுமானதில்லை |
| `ORDER_NOT_CONFIRMED` | Order not confirmed | ऑर्डर पक्का नहीं | ఆర్డర్ నిర్ధారించబడలేదు | ஆர்டர் உறுதிப்படுத்தப்படவில்லை |
| `JOB_NOT_STARTED` | Job not started | काम शुरू नहीं | పని మొదలవ్వలేదు | வேலை தொடங்கவில்லை |
| `ROLL_ALREADY_INSPECTED` | Roll already inspected | रोल जाँचा गया है | రోల్ ఇప్పటికే తనిఖీ చేయబడింది | ரோல் ஏற்கனவே ஆய்வு செய்யப்பட்டது |
| `DISPATCH_PENDING_QC` | Rolls have pending QC | QC बाकी है | QC పెండింగ్ ఉంది | QC நிலுவையில் உள்ளது |
| `INVOICE_ALREADY_PAID` | Invoice already paid | बिल भुगतान हुआ | ఇన్వాయిస్ ఇప్పటికే చెల్లించబడింది | விலைப்பட்டியல் ஏற்கனவே செலுத்தப்பட்டது |
| `UNAUTHORIZED` | Login required | लॉगिन करें | లాగిన్ చేయండి | உள்நுழைக |
| `SERVER_ERROR` | Something went wrong | कुछ गलत हुआ | ఏదో తప్పు జరిగింది | ஏதோ தவறு நடந்தது |
| `RATE_LIMITED` | Too many requests | बहुत ज़्यादा अनुरोध | చాలా అభ్యర్థనలు | அதிகமான கோரிக்கைகள் |
| `CLOCK_SKEW` | Clock out of sync | समय गलत | సమయం తప్పు | நேரம் பிழையாக உள்ளது |
