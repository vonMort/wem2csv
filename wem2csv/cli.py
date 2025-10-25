import argparse
import locale
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import List, Tuple, Dict, Iterable

import warnings

# Silence a deprecation warning emitted by ctranslate2 importing pkg_resources
# Context: setuptools plans to remove pkg_resources; ctranslate2 may still import it.
# We filter only this specific UserWarning from ctranslate2 to keep other warnings visible.
warnings.filterwarnings(
    "ignore",
    message=r"pkg_resources is deprecated as an API.*",
    category=UserWarning,
    module=r"ctranslate2(\.|$)",
)

import pandas as pd
from tqdm import tqdm
from faster_whisper import WhisperModel

# Supported languages (Whisper ISO codes; UI/audio allowed)
ALLOWED_LANGS = ["en", "fr", "de", "ja", "ru", "es"]

# ----------------------------- i18n -----------------------------
I18N: Dict[str, Dict[str, str]] = {
    "en": {
        "app_desc": "WEM → OGG → CSV pipeline with language-aware CLI (Whisper).",
        "arg_dir": "Directory to recursively search for WEM files",
        "arg_txt": "Text file that contains *.wem tokens",
        "arg_model": "Whisper model: tiny|base|small|medium|large-v3 (default: small)",
        "arg_audio_lang": "Audio language: auto|en|fr|de|ja|ru|es (default: auto).",
        "arg_ui_lang": "CLI language: system|en|fr|de|ja|ru|es (default: system).",
        "arg_transcript_lang": "Translate transcripts to 'en' using Whisper (only English is supported).",
        "found_wem_entries": "Found WEM entries in TXT: {n}",
        "copying": "Copying matching .wem files into wem-collection …",
        "copied_n": "Copied: {n}",
        "none_found_abort": "No WEM files found — aborting.",
        "convert_step": "Converting WEM → OGG via ww2ogg …",
        "revorb_step": "Normalizing OGG via revorb …",
        "move_step": "Moving .ogg into ogg-collection …",
        "transcribe_step": "Transcribing OGG files …",
        "transcribe_mode": "Transcription device: {device} (compute_type={ctype})",
        "using_model": "Whisper model: {model}",
        "whisper_lang_hint": "Audio language hint: {lang}",
        "whisper_auto_lang": "Audio language: auto-detect",
        "csv_written": "Done. CSV written: {path}",
        "cleanup": "Cleaning up: deleting .wem in wem-collection …",
        "cleanup_done": "Cleanup finished.",
        "ww2ogg_err": "ww2ogg failed for {name}: {out}",
        "revorb_err": "revorb failed for {name}: {out}",
        "tools_missing": "{name} not found in {dir}",
        "dir_missing": "Search directory does not exist: {path}",
        "txt_missing": "Text file does not exist: {path}",
        "translating_to_en": "Translating transcripts to English (Whisper task=translate) …",
        "translate_limit": "Note: translation targets other than English are not supported by Whisper.",
        "invalid_audio_lang": "Invalid --audio-lang '{val}'. Allowed: auto, en, fr, de, ja, ru, es.",
    },
    "fr": {
        "app_desc": "Pipeline WEM → OGG → CSV avec CLI multilingue (Whisper).",
        "arg_dir": "Répertoire dans lequel rechercher les fichiers WEM (récursif)",
        "arg_txt": "Fichier texte contenant des jetons *.wem",
        "arg_model": "Modèle Whisper : tiny|base|small|medium|large-v3 (par défaut : small)",
        "arg_audio_lang": "Langue audio : auto|en|fr|de|ja|ru|es (défaut : auto).",
        "arg_ui_lang": "Langue de la CLI : system|en|fr|de|ja|ru|es (défaut : system).",
        "arg_transcript_lang": "Traduire les transcriptions en anglais (Whisper ne supporte que l’anglais).",
        "found_wem_entries": "Entrées WEM trouvées dans le TXT : {n}",
        "copying": "Copie des fichiers .wem correspondants vers wem-collection …",
        "copied_n": "Copiés : {n}",
        "none_found_abort": "Aucun fichier WEM trouvé — abandon.",
        "convert_step": "Conversion WEM → OGG via ww2ogg …",
        "revorb_step": "Normalisation OGG via revorb …",
        "move_step": "Déplacement des .ogg vers ogg-collection …",
        "transcribe_step": "Transcription des fichiers OGG …",
        "transcribe_mode": "Périphérique de transcription : {device} (compute_type={ctype})",
        "using_model": "Modèle Whisper : {model}",
        "whisper_lang_hint": "Indice de langue audio : {lang}",
        "whisper_auto_lang": "Langue audio : détection automatique",
        "csv_written": "Terminé. CSV écrit : {path}",
        "cleanup": "Nettoyage : suppression des .wem dans wem-collection …",
        "cleanup_done": "Nettoyage terminé.",
        "ww2ogg_err": "Échec ww2ogg pour {name} : {out}",
        "revorb_err": "Échec revorb pour {name} : {out}",
        "tools_missing": "{name} introuvable dans {dir}",
        "dir_missing": "Répertoire de recherche inexistant : {path}",
        "txt_missing": "Fichier texte inexistant : {path}",
        "translating_to_en": "Traduction des transcriptions en anglais (task=translate) …",
        "translate_limit": "Remarque : Whisper n’accepte que l’anglais comme langue cible.",
        "invalid_audio_lang": "Valeur --audio-lang invalide '{val}'. Autorisées : auto, en, fr, de, ja, ru, es.",
    },
    "de": {
        "app_desc": "WEM → OGG → CSV Pipeline mit mehrsprachiger CLI (Whisper).",
        "arg_dir": "Verzeichnis, in dem nach WEM-Dateien rekursiv gesucht wird",
        "arg_txt": "Textdatei mit *.wem-Einträgen",
        "arg_model": "Whisper-Modell: tiny|base|small|medium|large-v3 (Standard: small)",
        "arg_audio_lang": "Audiosprache: auto|en|fr|de|ja|ru|es (Standard: auto).",
        "arg_ui_lang": "CLI-Sprache: system|en|fr|de|ja|ru|es (Standard: system).",
        "arg_transcript_lang": "Transkripte nach Englisch übersetzen (nur Englisch wird unterstützt).",
        "found_wem_entries": "Gefundene WEM-Einträge in TXT: {n}",
        "copying": "Kopiere passende .wem in wem-collection …",
        "copied_n": "Kopiert: {n}",
        "none_found_abort": "Keine WEM-Dateien gefunden – Abbruch.",
        "convert_step": "Konvertiere WEM → OGG mit ww2ogg …",
        "revorb_step": "Normalisiere OGG mit revorb …",
        "move_step": "Verschiebe .ogg in ogg-collection …",
        "transcribe_step": "Transkribiere OGG-Dateien …",
        "transcribe_mode": "Transkriptionsgerät: {device} (compute_type={ctype})",
        "using_model": "Whisper-Modell: {model}",
        "whisper_lang_hint": "Audio-Sprache (Hint): {lang}",
        "whisper_auto_lang": "Audio-Sprache: automatische Erkennung",
        "csv_written": "Fertig. CSV geschrieben: {path}",
        "cleanup": "Aufräumen: lösche .wem in wem-collection …",
        "cleanup_done": "Aufräumen abgeschlossen.",
        "ww2ogg_err": "ww2ogg fehlgeschlagen für {name}: {out}",
        "revorb_err": "revorb fehlgeschlagen für {name}: {out}",
        "tools_missing": "{name} nicht gefunden in {dir}",
        "dir_missing": "Suchverzeichnis existiert nicht: {path}",
        "txt_missing": "Textdatei existiert nicht: {path}",
        "translating_to_en": "Übersetze Transkripte nach Englisch (task=translate) …",
        "translate_limit": "Hinweis: andere Zielsprachen als Englisch werden nicht unterstützt.",
        "invalid_audio_lang": "Ungültiges --audio-lang '{val}'. Erlaubt: auto, en, fr, de, ja, ru, es.",
    },
    "ja": {
        "app_desc": "言語対応CLIを備えた WEM → OGG → CSV パイプライン（Whisper）。",
        "arg_dir": "WEMファイルを再帰的に探索するディレクトリ",
        "arg_txt": "*.wem トークンを含むテキストファイル",
        "arg_model": "Whisperモデル: tiny|base|small|medium|large-v3（既定: small）",
        "arg_audio_lang": "音声言語: auto|en|fr|de|ja|ru|es（既定: auto）。",
        "arg_ui_lang": "CLI言語: system|en|fr|de|ja|ru|es（既定: system）。",
        "arg_transcript_lang": "転写を英語に翻訳（Whisperは英語のみ対応）。",
        "found_wem_entries": "TXT内の WEM エントリ: {n}",
        "copying": "一致する .wem を wem-collection にコピー中 …",
        "copied_n": "コピー数: {n}",
        "none_found_abort": "WEM ファイルが見つかりません — 中止。",
        "convert_step": "ww2ogg による WEM → OGG 変換中 …",
        "revorb_step": "revorb による OGG 正規化中 …",
        "move_step": ".ogg を ogg-collection へ移動中 …",
        "transcribe_step": "OGG を転写中 …",
        "transcribe_mode": "転写デバイス: {device} (compute_type={ctype})",
        "using_model": "Whisperモデル: {model}",
        "whisper_lang_hint": "音声言語ヒント: {lang}",
        "whisper_auto_lang": "音声言語: 自動検出",
        "csv_written": "完了。CSV 出力: {path}",
        "cleanup": "クリーンアップ: wem-collection 内の .wem を削除 …",
        "cleanup_done": "クリーンアップ完了。",
        "ww2ogg_err": "ww2ogg 失敗: {name}: {out}",
        "revorb_err": "revorb 失敗: {name}: {out}",
        "tools_missing": "{name} が {dir} に見つかりません。",
        "dir_missing": "探索ディレクトリが存在しません: {path}",
        "txt_missing": "テキストファイルが存在しません: {path}",
        "translating_to_en": "英語へ翻訳中（task=translate） …",
        "translate_limit": "注意：英語以外の翻訳は Whisper が非対応です。",
        "invalid_audio_lang": "無効な --audio-lang '{val}'。利用可能: auto, en, fr, de, ja, ru, es。",
    },
    "ru": {
        "app_desc": "Конвейер WEM → OGG → CSV с многоязычным CLI (Whisper).",
        "arg_dir": "Каталог для рекурсивного поиска файлов WEM",
        "arg_txt": "Текстовый файл, содержащий токены *.wem",
        "arg_model": "Модель Whisper: tiny|base|small|medium|large-v3 (по умолчанию: small)",
        "arg_audio_lang": "Язык аудио: auto|en|fr|de|ja|ru|es (по умолчанию: auto).",
        "arg_ui_lang": "Язык CLI: system|en|fr|de|ja|ru|es (по умолчанию: system).",
        "arg_transcript_lang": "Перевод транскриптов на английский (Whisper поддерживает только английский).",
        "found_wem_entries": "Найдено WEM-элементов в TXT: {n}",
        "copying": "Копирование подходящих .wem в wem-collection …",
        "copied_n": "Скопировано: {n}",
        "none_found_abort": "Файлы WEM не найдены — останов.",
        "convert_step": "Преобразование WEM → OGG через ww2ogg …",
        "revorb_step": "Нормализация OGG через revorb …",
        "move_step": "Перемещение .ogg в ogg-collection …",
        "transcribe_step": "Транскрибирование OGG-файлов …",
        "transcribe_mode": "Устройство транскрибирования: {device} (compute_type={ctype})",
        "using_model": "Модель Whisper: {model}",
        "whisper_lang_hint": "Подсказка языка аудио: {lang}",
        "whisper_auto_lang": "Язык аудио: авто-определение",
        "csv_written": "Готово. CSV записан: {path}",
        "cleanup": "Очистка: удаление .wem в wem-collection …",
        "cleanup_done": "Очистка завершена.",
        "ww2ogg_err": "Сбой ww2ogg для {name}: {out}",
        "revorb_err": "Сбой revorb для {name}: {out}",
        "tools_missing": "{name} не найден в {dir}",
        "dir_missing": "Каталог поиска не существует: {path}",
        "txt_missing": "Текстовый файл не существует: {path}",
        "translating_to_en": "Перевод транскриптов на английский (task=translate) …",
        "translate_limit": "Примечание: Whisper поддерживает только английский как язык перевода.",
        "invalid_audio_lang": "Неверное значение --audio-lang '{val}'. Допустимые: auto, en, fr, de, ja, ru, es.",
    },
    "es": {
        "app_desc": "Canalización WEM → OGG → CSV con CLI multilingüe (Whisper).",
        "arg_dir": "Directorio donde buscar archivos WEM de forma recursiva",
        "arg_txt": "Archivo de texto que contiene tokens *.wem",
        "arg_model": "Modelo Whisper: tiny|base|small|medium|large-v3 (predeterminado: small)",
        "arg_audio_lang": "Idioma del audio: auto|en|fr|de|ja|ru|es (predeterminado: auto).",
        "arg_ui_lang": "Idioma de la CLI: system|en|fr|de|ja|ru|es (predeterminado: system).",
        "arg_transcript_lang": "Traducir transcripciones al inglés (Whisper solo admite inglés).",
        "found_wem_entries": "Entradas WEM encontradas en TXT: {n}",
        "copying": "Copiando .wem coincidentes a wem-collection …",
        "copied_n": "Copiados: {n}",
        "none_found_abort": "No se encontraron archivos WEM — cancelando.",
        "convert_step": "Convirtiendo WEM → OGG con ww2ogg …",
        "revorb_step": "Normalizando OGG con revorb …",
        "move_step": "Moviendo .ogg a ogg-collection …",
        "transcribe_step": "Transcribiendo archivos OGG …",
        "transcribe_mode": "Dispositivo de transcripción: {device} (compute_type={ctype})",
        "using_model": "Modelo Whisper: {model}",
        "whisper_lang_hint": "Idioma de audio (sugerencia): {lang}",
        "whisper_auto_lang": "Idioma de audio: autodetección",
        "csv_written": "Listo. CSV generado: {path}",
        "cleanup": "Limpieza: eliminando .wem en wem-collection …",
        "cleanup_done": "Limpieza completada.",
        "ww2ogg_err": "Fallo de ww2ogg para {name}: {out}",
        "revorb_err": "Fallo de revorb para {name}: {out}",
        "tools_missing": "{name} no encontrado en {dir}",
        "dir_missing": "El directorio de búsqueda no existe: {path}",
        "txt_missing": "El archivo de texto no existe: {path}",
        "translating_to_en": "Traduciendo transcripciones al inglés (task=translate) …",
        "translate_limit": "Nota: Whisper solo admite inglés como idioma de destino.",
        "invalid_audio_lang": "Valor inválido de --audio-lang '{val}'. Permitidos: auto, en, fr, de, ja, ru, es.",
    },
}


def tr(lang: str, key: str, **kw) -> str:
    """Return localized string for key in given language (fallback to English)."""
    if lang not in I18N:
        lang = "en"
    return I18N[lang].get(key, I18N["en"].get(key, key)).format(**kw)


# ----------------------------- helpers -----------------------------

def detect_system_lang() -> str:
    """
    Detect system language and map to supported codes.
    Returns one of: en, fr, de, ja, ru, es (fallback: en).
    """
    # Try locale.getdefaultlocale (newer Python may warn; still usable). Fallback to LANG env.
    code = None
    try:
        loc = locale.getdefaultlocale()[0]  # e.g., 'de_DE'
        if loc:
            code = loc.split("_", 1)[0].lower()
    except Exception:
        pass
    if not code:
        env = os.environ.get("LANG", "") or os.environ.get("LC_ALL", "")
        if env:
            code = env.split("_", 1)[0].split(".", 1)[0].lower()
    return code if code in ALLOWED_LANGS else "en"


def run_cmd(cmd: List[str], cwd: Path = None) -> Tuple[int, str]:
    """Run a subprocess command and capture stdout/stderr."""
    result = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return result.returncode, result.stdout.strip()


def extract_wem_names(text_path: Path) -> List[str]:
    """Extract unique *.wem tokens from a text file (basename only)."""
    text = text_path.read_text(encoding="utf-8", errors="ignore")
    names = {Path(m).name for m in re.findall(r'([^\s"\'<>|:*?]+\.wem)', text, flags=re.IGNORECASE)}
    return list(names)


def safe_mkdir(path: Path) -> None:
    """Create a directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def choose_device_and_compute_type() -> Tuple[str, str]:
    """Prefer CUDA if available; otherwise CPU int8."""
    try:
        import torch  # noqa
        if torch.cuda.is_available():
            return "cuda", "int8_float16"
    except Exception:
        pass
    return "cpu", "int8"


def list_files(root: Path) -> Iterable[Path]:
    """Yield files recursively under root."""
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            yield Path(dirpath) / f


# ----------------------------- pipeline steps -----------------------------

def stage_collect_wem(wem_names: List[str], search_dir: Path, wem_collection: Path, ui_lang: str) -> int:
    """Collect *.wem listed in TXT into wem-collection."""
    print(tr(ui_lang, "copying"))
    safe_mkdir(wem_collection)
    targets_lower = {n.lower() for n in wem_names}
    copied = 0
    for p in list_files(search_dir):
        if p.suffix.lower() == ".wem" and p.name.lower() in targets_lower:
            shutil.copy2(p, wem_collection / p.name)
            copied += 1
    print(tr(ui_lang, "copied_n", n=copied))
    return copied


def stage_ww2ogg(wem_collection: Path, tools_dir: Path, ui_lang: str) -> int:
    """Run ww2ogg for all .wem in wem-collection."""
    ww2ogg = tools_dir / "ww2ogg.exe"
    codebooks = tools_dir / "packed_codebooks_aoTuV_603.bin"
    if not ww2ogg.exists():
        raise FileNotFoundError(tr(ui_lang, "tools_missing", name=ww2ogg.name, dir=str(tools_dir)))
    if not codebooks.exists():
        raise FileNotFoundError(tr(ui_lang, "tools_missing", name=codebooks.name, dir=str(tools_dir)))
    print(tr(ui_lang, "convert_step"))
    errors = 0
    for wem in tqdm(sorted(wem_collection.glob("*.wem")), desc="ww2ogg", unit="file"):
        rc, out = run_cmd([str(ww2ogg), str(wem), "--pcb", str(codebooks)], cwd=wem_collection)
        if rc != 0:
            errors += 1
            print(tr(ui_lang, "ww2ogg_err", name=wem.name, out=out))
    return errors


def stage_revorb(wem_collection: Path, tools_dir: Path, ui_lang: str) -> int:
    """Run revorb for all .ogg in wem-collection."""
    revorb = tools_dir / "revorb.exe"
    if not revorb.exists():
        raise FileNotFoundError(tr(ui_lang, "tools_missing", name=revorb.name, dir=str(tools_dir)))
    print(tr(ui_lang, "revorb_step"))
    errors = 0
    for ogg in tqdm(sorted(wem_collection.glob("*.ogg")), desc="revorb", unit="file"):
        rc, out = run_cmd([str(revorb), str(ogg)], cwd=wem_collection)
        if rc != 0:
            errors += 1
            print(tr(ui_lang, "revorb_err", name=ogg.name, out=out))
    return errors


def stage_move_ogg(wem_collection: Path, ogg_collection: Path, ui_lang: str) -> int:
    """Move all .ogg into ogg-collection."""
    print(tr(ui_lang, "move_step"))
    safe_mkdir(ogg_collection)
    moved = 0
    for ogg in sorted(wem_collection.glob("*.ogg")):
        dst = ogg_collection / ogg.name
        if dst.exists():
            dst.unlink()
        shutil.move(str(ogg), dst)
        moved += 1
    return moved


def stage_transcribe(
    ogg_collection: Path,
    out_csv: Path,
    model_name: str,
    audio_lang: str,
    transcript_lang: str,
    ui_lang: str,
) -> Tuple[int, int]:
    """Transcribe .ogg in ogg-collection; optional translation to English via Whisper."""
    oggs = sorted(ogg_collection.glob("*.ogg"))
    if not oggs:
        pd.DataFrame(columns=["filename", "voiceline"]).to_csv(out_csv, index=False, encoding="utf-8")
        print(tr(ui_lang, "csv_written", path=str(out_csv)))
        return 0, 0

    device, compute_type = choose_device_and_compute_type()
    print(tr(ui_lang, "transcribe_step"))
    print(tr(ui_lang, "transcribe_mode", device=device, ctype=compute_type))
    print(tr(ui_lang, "using_model", model=model_name))

    # Validate/normalize audio language
    lang = (audio_lang or "auto").lower()
    if lang not in (["auto"] + ALLOWED_LANGS):
        raise ValueError(tr(ui_lang, "invalid_audio_lang", val=audio_lang))

    task = None
    if transcript_lang and transcript_lang.lower() == "en" and lang != "en":
        task = "translate"
        print(tr(ui_lang, "translating_to_en"))
    elif transcript_lang and transcript_lang.lower() != "en":
        print(tr(ui_lang, "translate_limit"))

    if lang == "auto":
        print(tr(ui_lang, "whisper_auto_lang"))
        lang_hint = None
    else:
        print(tr(ui_lang, "whisper_lang_hint", lang=lang))
        lang_hint = lang

    model = WhisperModel(model_name, device=device, compute_type=compute_type)

    rows, failures = [], 0
    for ogg in tqdm(oggs, desc="whisper", unit="file"):
        try:
            segments, _ = model.transcribe(
                str(ogg),
                language=lang_hint,
                vad_filter=True,
                beam_size=5,
                best_of=5,
                condition_on_previous_text=False,
                task=task,
            )
            text = "".join(seg.text for seg in segments).strip()
        except Exception as e:
            failures += 1
            text = f"[ERROR: {e}]"
        rows.append({"filename": ogg.name, "voiceline": text})

    pd.DataFrame(rows, columns=["filename", "voiceline"]).to_csv(out_csv, index=False, encoding="utf-8")
    print(tr(ui_lang, "csv_written", path=str(out_csv)))
    return len(rows), failures


def cleanup_wem(wem_collection: Path, ui_lang: str) -> int:
    """Delete all .wem files in wem-collection."""
    print(tr(ui_lang, "cleanup"))
    deleted = 0
    for wem in sorted(wem_collection.glob("*.wem")):
        try:
            wem.unlink()
            deleted += 1
        except Exception:
            pass
    print(tr(ui_lang, "cleanup_done"))
    return deleted


# ----------------------------- main -----------------------------

def build_parser(ui_lang: str) -> argparse.ArgumentParser:
    """Build a localized argparse parser."""
    p = argparse.ArgumentParser(description=tr(ui_lang, "app_desc"))
    p.add_argument("-d", "--dir", required=True, help=tr(ui_lang, "arg_dir"))
    p.add_argument("-t", "--txt", required=True, help=tr(ui_lang, "arg_txt"))
    p.add_argument("--model", default="small", help=tr(ui_lang, "arg_model"))
    p.add_argument("--audio-lang", default="auto", help=tr(ui_lang, "arg_audio_lang"))
    p.add_argument("--ui-lang", default="system", help=tr(ui_lang, "arg_ui_lang"))
    p.add_argument("--transcript-lang", default="", help=tr(ui_lang, "arg_transcript_lang"))
    return p


def main():
    """
    Entry point:
      - Collect .wem (listed in TXT) from --dir into ./wem-collection
      - Convert to .ogg (ww2ogg + revorb) using ./tools
      - Move to ./ogg-collection
      - Transcribe with Whisper to CSV (filename, voiceline), optional EN translation
      - Clean up .wem on full success
      - CLI language defaults to system locale (fallback en); audio-lang defaults to auto
    """
    # Decide UI language from system (before parsing, to localize --help)
    system_lang = detect_system_lang()
    parser = build_parser(system_lang)
    args = parser.parse_args()

    # Final UI language: allow explicit override
    ui_lang = args.ui_lang.lower().strip()
    if ui_lang == "system":
        ui_lang = system_lang
    if ui_lang not in I18N:
        ui_lang = "en"

    # Use the project root (parent of the package directory) as the base directory
    base_dir = Path(__file__).resolve().parent.parent
    wem_dir = base_dir / "wem-collection"
    ogg_dir = base_dir / "ogg-collection"
    out_csv = base_dir / "voicelines.csv"

    tools_dir = base_dir / "tools"
    ww2ogg = tools_dir / "ww2ogg.exe"
    revorb = tools_dir / "revorb.exe"
    codebooks = tools_dir / "packed_codebooks_aoTuV_603.bin"

    search_dir = Path(args.dir).expanduser().resolve()
    textfile = Path(args.txt).expanduser().resolve()
    if not search_dir.exists():
        raise FileNotFoundError(tr(ui_lang, "dir_missing", path=str(search_dir)))
    if not textfile.exists():
        raise FileNotFoundError(tr(ui_lang, "txt_missing", path=str(textfile)))
    for exe in (ww2ogg, revorb, codebooks):
        if not exe.exists():
            raise FileNotFoundError(tr(ui_lang, "tools_missing", name=exe.name, dir=str(tools_dir)))

    wem_names = extract_wem_names(textfile)
    print(tr(ui_lang, "found_wem_entries", n=len(wem_names)))
    if not wem_names:
        print(tr(ui_lang, "none_found_abort"))
        return

    safe_mkdir(wem_dir)
    copied = stage_collect_wem(wem_names, search_dir, wem_dir, ui_lang)
    if copied == 0:
        print(tr(ui_lang, "none_found_abort"))
        return

    ww_errs = stage_ww2ogg(wem_dir, tools_dir, ui_lang)
    rv_errs = stage_revorb(wem_dir, tools_dir, ui_lang)
    moved = stage_move_ogg(wem_dir, ogg_dir, ui_lang)

    total, failures = stage_transcribe(
        ogg_dir, out_csv,
        model_name=args.model.strip(),
        audio_lang=(args.audio_lang or "auto").strip().lower(),
        transcript_lang=(args.transcript_lang or "").strip().lower(),
        ui_lang=ui_lang,
    )

    success = (ww_errs == 0) and (rv_errs == 0) and (moved > 0) and (failures == 0)
    if success:
        cleanup_wem(wem_dir, ui_lang)
    # else keep .wem for troubleshooting


if __name__ == "__main__":
    main()
