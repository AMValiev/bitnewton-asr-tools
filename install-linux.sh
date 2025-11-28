#!/bin/bash

echo "========================================"
echo "Ustanovka BitNewton ASR Tools dlya Linux/WSL"
echo "========================================"
echo ""

# Poluchaem absolutniy put k tekuschey papke
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"

# Proverka prav root (sudo) - eto nuzhno dlya zapisi v /usr/local/bin
if [ "$EUID" -ne 0 ]; then 
  echo "[!] Oshibka: Dlya sozdaniya ssylok v /usr/local/bin nuzhmy prava sudo."
  echo "Pozhaluysta, zapustite skript tak: sudo ./install-linux.sh"
  exit 1
fi

echo "[1/2] Sozdanie simvolicheskih ssylok v /usr/local/bin..."

# Sozdaem obertki (wrappers) ili symlinki
# Zdes my ispolzuem pryamye symlinki na python-skripty.
# Chtoby eto rabotalo, v nachale python-faylov dolzhen byt 'shebang' (#!/usr/bin/env python3)
# i oni dolzhny byt ispolnyaemymi (+x).

# Delaem fayly ispolnyaemymi
chmod +x "$INSTALL_DIR/src/transcribe.py"
chmod +x "$INSTALL_DIR/src/summarize.py"

# Sozdaem ssylki. Flag -s (symbolic) -f (force/overwrite).
# Esli ssylka uzhe est, ona obnovitsya na noviy put.

ln -sf "$INSTALL_DIR/src/transcribe.py" /usr/local/bin/transcribe
echo "Sozdana ssylka: /usr/local/bin/transcribe -> $INSTALL_DIR/src/transcribe.py"

ln -sf "$INSTALL_DIR/src/summarize.py" /usr/local/bin/summarize
echo "Sozdana ssylka: /usr/local/bin/summarize -> $INSTALL_DIR/src/summarize.py"

echo "[2/2] Proverka ustanovki Python..."
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version)
    echo "Python nayden: $PY_VERSION"
else
    echo ""
    echo "[!] VNIMANIE: Python3 ne nayden!"
    echo "Ustanovite Python: sudo apt install python3 python3-pip"
fi

echo ""
echo "========================================"
echo "Ustanovka zavershena!"
echo "========================================"
echo "Komandy 'transcribe' i 'summarize' teper dostupny v sisteme."
echo "Perezagruzka terminala NE trebuetsya."