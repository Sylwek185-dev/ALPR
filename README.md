## Parking ALPR (YOLO + OCR + SQLite)

Aplikacja webowa do automatycznej kontroli wjazdu i wyjazdu pojazdów
na parking na podstawie rozpoznawania tablic rejestracyjnych (ANPR).

Interfejs graficzny został wykonany w Streamlit.

### Pobranie projektu z GitHub

```
git clone https://github.com/Sylwek185-dev/ALPR.git
cd ALPR
```

### 1) Instalacja

#### macOS / Linux

```
python -m venv .venv
source .venv/bin/activate
```

#### lub:

#### Windows

```
.venv\Scripts\activate # Windows
pip install -r requirements.txt
```

### 2) Struktura plików

- zdjęcia testowe: `data/images/`
- baza danych SQLite: `data/parking.db`
- model YOLO: `models/plate_detector.pt`
- interfejs graficzny: `src/gui.py`
- logika aplikacji: `src/app_service.py`

### 3) Uruchomienie aplikacji (GUI)

#### w macOS/Linux

```
./.venv/bin/python -m streamlit run src/gui.py
```

#### w Windows

```
.\.venv\Scripts\python.exe -m streamlit run src\gui.py
```

Po uruchomieniu aplikacja będzie dostępna w przeglądarce pod adresem:

http://localhost:8501

### 4) Sposób użycia

1. Podaj ścieżkę do zdjęcia pojazdu od nr 1 do 20 (np. `data/images/1.jpg`)
2. Wybierz jedną z akcji:
   - **Wjazd** – rejestruje pojazd na parkingu
   - **Wyjazd** – nalicza opłatę i zamyka wjazd
   - **Odczyt** – tylko rozpoznanie tablicy (bez zapisu do bazy)
3. Stan parkingu i historia zapisywane są w bazie SQLite
4. Dane można wyeksportować do pliku CSV

---

## Najczęstsze problemy

### Jeśli pojawi się błąd:

`ModuleNotFoundError: No module named 'src'  `

uruchom aplikację z katalogu głównego projektu poleceniem:

<br>

w macOS/Linux

```
PYTHONPATH=. python -m streamlit run src/gui.py
```

<br>

w Windows

```set PYTHONPATH=.
python -m streamlit run src/gui.py
```

---

### Jeśli pojawi się błąd:

```
streamlit: command not found
```

uruchom Streamlit przez Pythona:

```
python -m streamlit run src/gui.py
```

---

### Jeśli aplikacja długo sprawdza połączenie z serwerami modeli:

```
Checking connectivity to the model hosters

```

ustaw zmienną środowiskową:

```
export DISABLE_MODEL_SOURCE_CHECK=True
```

a następnie uruchom ponownie aplikację:

```
python -m streamlit run src/gui.py
```
