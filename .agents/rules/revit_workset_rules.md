---
trigger: model_open, workshared_model, batch_automation
description: Revit Central Models සැකසීමේදී සහ Batch Automation ක්‍රියාත්මක කිරීමේදී Worksets ස්වයංක්‍රීයව AllWorksets ලෙස තබාගැනීම පිළිබඳ නීති.
---

# Revit Central Models සහ Workset Automation නීති

## 1. පරිශීලකයාගේ Open Workflow එකට ගරු කිරීම (Respect User Open Workflow)
- පරිශීලකයා නිතරම Revit හි `File -> Open -> Project` හරහා Central Model එක තෝරා `Create New Local` ටික් කර File එක විවෘත කරයි.
- කිසි විටෙකත් පරිශීලකයාට Open dialog එකේදී Workset Option එක වෙනස් කිරීමට හෝ Specify කිරීමට උපදෙස් නොදිය යුතුය.
- ඒ වෙනුවට, අපගේ Batch Scripts මඟින් Central Model එක Save කරන සෑම අවස්ථාවකදීම, එහි Internal Workset Configuration එක ස්වයංක්‍රීයව `AllWorksets` බවට පත් කළ යුතුය.

## 2. Central Model Save කිරීමේදී AllWorksets තහවුරු කිරීම (Enforce AllWorksets on Save)
- Revit API හි `WorksharingSaveAsOptions.OpenWorksetsDefault` අගය පෙරනිමියෙන් (default) හෝ සමහර ගොනුවල `AskUserToSpecify` ලෙස පැවතිය හැක. එවිට පරිශීලකයා `Create New Local` දමා Open කරන විට "Opening Worksets" popup dialog එක පැමිණේ.
- මෙය වැළැක්වීමට, Batch Automation එකේදී හෝ Central Model එකක් Save කරන ඕනෑම තැනකදී:
  ```python
  ws_opts = WorksharingSaveAsOptions()
  ws_opts.SaveAsCentral = True
  ws_opts.OpenWorksetsDefault = SimpleWorksetConfiguration.AllWorksets
  save_as_opts.SetWorksharingOptions(ws_opts)
  doc.SaveAs(file_path, save_as_opts)
  ```
- ඉන්පසු සියලුම Worksets සහ Elements `doc.SynchronizeWithCentral` මඟින් Relinquish කළ යුතුය:
  ```python
  transact_opts = TransactWithCentralOptions()
  sync_opts = SynchronizeWithCentralOptions()
  relinquish_opts = RelinquishOptions(True)
  sync_opts.SetRelinquishOptions(relinquish_opts)
  doc.SynchronizeWithCentral(transact_opts, sync_opts)
  ```

## 3. Location Plan Graphic Settings සහ Detail Item Parameters
- Location Plan එක Drafting View එකක් තුළ Detail Item Family එකක් ලෙස පවතින විට:
  - Drafting View එකේ Scale එක නිරන්තරයෙන්ම `1:4000` ලෙස තහවුරු කළ යුතුය.
  - Sheet එක මත Viewport එකේ Location Center එක සහ Title Block Label Offset එක නිශ්චිත අගයන්ට අනුව පිහිටුවිය යුතුය.
  - Detail Item එකේ Family Type Properties තුළ අදාළ ගොඩනැගිල්ල (උදා: `02 W-SB`) සහ Main Location Plan (`00 THUVARU - LOCATION PLAN`) පරාමිතීන් `1` (Checked) කළ යුතුය. එවිට පමණක් රතු පාටින් අදාළ විලාස් (Villas) හයිලයිට් වේ.
