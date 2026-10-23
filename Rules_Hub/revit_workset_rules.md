---
trigger: model_open, workshared_model, batch_automation, sync_model
description: Revit Central Models සැකසීමේදී, Batch Automation සහ Sync කිරීමේදී Worksets ස්වයංක්‍රීයව AllWorksets ලෙස තබාගැනීම පිළිබඳ නීති.
---

# Revit Central Models සහ Workset Automation නීති

## 1. පරිශීලකයාගේ Open Workflow එකට ගරු කිරීම (Respect User Open Workflow)
- පරිශීලකයා නිතරම Revit හි `File -> Open -> Project` හරහා Central Model එක තෝරා `Create New Local` ටික් කර File එක විවෘත කරයි.
- කිසි විටෙකත් පරිශීලකයාට Open dialog එකේදී Workset Option එක වෙනස් කිරීමට හෝ Specify කිරීමට උපදෙස් නොදිය යුතුය.
- ඒ වෙනුවට, අපගේ Batch Scripts මඟින් Central Model එක Save කරන සෑම අවස්ථාවකදීම, එහි Internal Workset Configuration එක ස්වයංක්‍රීයව `AllWorksets` බවට පත් කළ යුතුය.

## 2. Central Model Save සහ Sync කිරීමේදී AllWorksets අනිවාර්ය කිරීම (Mandatory AllWorksets on Open, Save & Sync)

1. **Open Options සැකසීම**:
   Model එක විවෘත කරන ඕනෑම අවස්ථාවක සියලුම Worksets Open වන ලෙස Configuration එක සකස් කළ යුතුය:
   ```python
   ws_config = DB.WorksetConfiguration(DB.WorksetConfigurationOption.OpenAllWorksets)
   open_opts.SetOpenWorksetsConfiguration(ws_config)
   ```

2. **Save / Central සැකසීම (`OpenWorksetsDefault = AllWorksets`)**:
   Central Model එකක් Save කරන විට හෝ Local Save කරන විට, පෙරනිමි Workset තත්ත්වය `AllWorksets` ලෙස නියම කළ යුතුය:
   ```python
   ws_opts = DB.WorksharingSaveAsOptions()
   ws_opts.SaveAsCentral = True
   ws_opts.OpenWorksetsDefault = DB.SimpleWorksetConfiguration.AllWorksets
   save_opts.SetWorksharingOptions(ws_opts)
   ```

3. **Synchronize & Relinquish**:
   සියලුම Worksets Open කර සකස් කළ පසු `doc.SynchronizeWithCentral` මඟින් `RelinquishOptions(True)` සමඟ Central වෙත Sync කළ යුතුය:
   ```python
   transact_opts = DB.TransactWithCentralOptions()
   sync_opts = DB.SynchronizeWithCentralOptions()
   relinquish_opts = DB.RelinquishOptions(True)
   sync_opts.SetRelinquishOptions(relinquish_opts)
   doc.SynchronizeWithCentral(transact_opts, sync_opts)
   ```

## 3. Location Plan Graphic Settings සහ Detail Item Parameters
- Location Plan එක Drafting View එකක් තුළ Detail Item Family එකක් ලෙස පවතින විට:
  - Drafting View එකේ Scale එක නිරන්තරයෙන්ම `1:4000` ලෙස තහවුරු කළ යුතුය.
  - Sheet එක මත Viewport එකේ Location Center එක සහ Title Block Label Offset එක නිශ්චිත අගයන්ට අනුව පිහිටුවිය යුතුය.
  - Detail Item එකේ Family Type Properties තුළ අදාළ ගොඩනැගිල්ල (උදා: `02 W-SB`) සහ Main Location Plan (`00 THUVARU - LOCATION PLAN`) පරාමිතීන් `1` (Checked) කළ යුතුය. එවිට පමණක් රතු පාටින් අදාළ විලාස් (Villas) හයිලයිට් වේ.
