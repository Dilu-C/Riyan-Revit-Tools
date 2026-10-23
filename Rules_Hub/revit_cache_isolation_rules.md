---
trigger: revit_cache, multi_model, batch_export, preview_generation, temp_files, workset_open
description: Multi-model Revit automation වලදී cross-model cache collisions, stale memory leaks සහ workset geometry deletion වැළැක්වීමේ නීති.
---

# Revit Model Cache Isolation & Anti-Contamination Rules

## 1. Compound Scoped Cache Keys (No Solo GUID Keys)
- Revit models cloned from the same template or created via "Save As" share identical `UniqueId` values for common sheets, views, and levels.
- In-memory cache dictionaries (`preview_cache`, `data_cache`) must **NEVER** use `element.UniqueId` or `SheetNumber` alone as a key.
- Always use a composite key incorporating the absolute model path:
  ```python
  cache_key = (os.path.abspath(model_path).lower(), element.UniqueId)
  ```

## 2. Model-Isolated Disk Filenames (Hash & Prefix Scoping)
- Temporary files saved to disk (`%TEMP%`, `AppData`, scratch) must never use bare GUIDs or sheet numbers.
- Always include a sanitized model identifier and a deterministic hash of the model path:
  ```python
  import zlib, re
  model_hash = hex(zlib.crc32(model_path.lower().encode('utf-8')) & 0xffffffff)[2:]
  model_clean = re.sub(r'[^a-zA-Z0-9_]', '', os.path.splitext(os.path.basename(model_path))[0])[:15]
  temp_prefix = "riyan_{}_{}_{}".format(model_clean, model_hash, element.UniqueId)
  ```
- **Zero Loose Matching**: When locating generated files (e.g., exported preview PDFs), match strictly on `temp_prefix`. Never fall back to loose sheet number matches (e.g., `if sheet.SheetNumber in f`) as this matches PDFs from other projects in the temp folder.

## 3. Mandatory `OpenAllWorksets` in Detached Mode (Zero Workset Destruction)
- Detached Central Models background open කිරීමේදී කිසිදු workset එකක් close නොකළ යුතුය (`ws_opt.CloseAllWorksets()` දැඩිව තහනම්ය).
- Detached mode හි worksets close කිරීමෙන් Revit API මඟින් එම worksets වල ඇති සියලුම 3D elements (බිත්ති, දොරවල්, furniture) ස්ථිරවම delete කර දමයි.
- නිරන්තරයෙන්ම `DB.WorksetConfigurationOption.OpenAllWorksets` යෙදිය යුතුය.

## 4. Stale Detached Orphan Documents Memory Purging
- Background model load කිරීමට පෙර, `app.Documents` පරීක්ෂා කර `PathName == ""` වන පැරණි stale detached documents ස්වයංක්‍රීයව `d.Close(False)` කර memory එකෙන් ඉවත් කළ යුතුය.
- Document matching සඳහා කිසි විටෙකත් fuzzy title matching නොයොදා, පරිශීලකයා Revit හි විවෘත කර ඇති files සඳහා `d.PathName` 100% exact match පමණක් භාවිත කළ යුතුය.

## 5. Immediate UI State Flushing on Selection
- පරිශීලකයා list එකෙන් sheet එකක් click කළ වහාම, cache පරීක්ෂාවට පෙර `image.Source = None` කර තිරය clear කළ යුතුය. කලින් sheet එකේ preview එක linger වීමට කිසිදු ඉඩක් නොතැබිය යුතුය.

## 6. Complete Session & In-Memory Cache Invalidation
- When "Clear All", "Reset", or file removal is triggered:
  - Explicitly clear all cache dictionaries: `self.preview_cache.clear()`, `self.doc_cache.clear()`.
  - Close background document instances cleanly (`d.Close(False)`).
  - Reset all detail text blocks and image elements back to default placeholder states (`"-"`).
