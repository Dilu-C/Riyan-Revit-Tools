---
trigger: titleblock_replacement, location_plan_update, batch_automation, keyplan_verification
description: TitleBlock සහ LocationPlan Families Batch Replace කිරීමේදී නිවැරදි (Checkmarked) KeyPlan එක හඳුනාගැනීම සහ Final Model එකට Enforce කිරීම පිළිබඳ නීති.
---

# Revit Family Sync & Smart KeyPlan Verification නීති

## 1. Approved Active Reference එකෙන් Live Family Extract කිරීම (Source of Truth)
- Network Drive (`\\RGLK-Drive\...`) හෝ Local Disk හි ඇති `.rfa` Files වල Date එක හෝ නම මත පමණක් පදනම්ව එය Latest/Approved Family එක යැයි උපකල්පනය නොකළ යුතුය.
- පරිශීලකයා විසින් තහවුරු කරන ලද Reference Model එක (උදා: `01-(W-SBL)`) Revit හි Open කර ඇති විට, එම Model එක තුළ පවතින Live TitleBlock සහ LocationPlan Families `doc.EditFamily(fam).SaveAs(...)` මඟින් සෘජුවම Disk එකට Extract කර Batch Automation එක සඳහා යොදාගත යුතුය.

## 2. පැරණි (Crossed-Out) KeyPlan එක මුළුමනින්ම ඉවත් කිරීම (Zero Tolerance for Outdated KeyPlan)
- වැලිපර/කලපු රේඛා 3 (3 sandbanks/lagoons) නොමැති පැරණි KeyPlan එක කිසිදු Sheet එකක හෝ View එකක නොතිබිය යුතුය.
- අවසන් වශයෙන් Save වන සෑම Revit Model එකකම Title Block සහ Location Plan තුළ තිබිය යුත්තේ පරිශීලකයා තහවුරු කළ, වැලිපර 3 සහිත නව KeyPlan එක පමණි.
- Sheet එක මත TitleBlock එක Pinned කර ඇත්නම්, පළමුව `tb.Pinned = False` කර Type ID එක අලුත් Symbol ID එකට මාරු කළ යුතුය.
- Sheet එකේ අදාළ ගොඩනැගිල්ලට අනුරූප Building Parameter එක (උදා: `39 LHK`, `34 SCK`, `40 FBO`, `38 CLN`, `35 HKB`, `36 HKW`, `37 MSQ`) Type සහ Instance Properties දෙකෙහිම `1` (ON) කර, අනෙකුත් සියලුම ගොඩනැගිලි පරාමිතීන් `0` (OFF) කළ යුතුය.
- Location Plan Sheet එකේදී TitleBlock හි `00 KEY PLAN` අගය `0` (OFF) විය යුතු අතර, Drafting View එක තුළ ඇති Detail Component එකෙහි `00 THUVARU - LOCATION PLAN` අගය `1` (ON) විය යුතුය.

## 3. Workshared Central සහ Local Model Cache පරීක්ෂාව (Local Refresh Enforcement)
- Batch Tool එක මඟින් Central Model එක සාර්ථකව Update කර Save කළද, පරිශීලකයා කලින් විවෘත කර තිබූ Local Model එක (`_dilupa.chathuranga7D32G.rvt`) කෙලින්ම විවෘත කළහොත් එහි පෙනෙන්නේ පැරණි Cached ග්‍රැෆික්ස් විය හැක.
- එබැවින් Central Model එක Update වූ පසු, පරිශීලකයාට `Create New Local` තෝරා Open කරන ලෙස හෝ `Reload Latest` / `Synchronize with Central` කරන ලෙස නිරන්තරයෙන්ම මඟපෙන්විය යුතුය.
