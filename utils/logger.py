"""
================================================================================
  Quantum Trade Oracle — Logger
================================================================================
  Logger structuré avec rotation automatique et support console coloré.
================================================================================
"""

import sys
import logging
from pathlib import Path
from datetime import datetime


def get_logger(name: str, log_dir: str = "./logs") -> logging.Logger:
    """
    Crée et retourne un logger configuré pour un module donné.

    Args:
        name:    Nom du module (affiché dans les logs)
        log_dir: Répertoire des fichiers de log

    Returns:
        Logger configuré avec handlers console + fichier
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger   # Éviter la duplication de handlers

    logger.setLevel(logging.DEBUG)

    # ── Format ────────────────────────────────────────────────────────────────
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Handler Console ───────────────────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    # ── Handler Fichier ───────────────────────────────────────────────────────
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(log_path / f"qto_{today}.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger


# Logger par défaut
log = get_logger("QTO")
