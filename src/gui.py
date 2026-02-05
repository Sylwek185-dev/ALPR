# src/gui.py
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.app_service import ParkingService

os.environ["DISABLE_MODEL_SOURCE_CHECK"] = "True"

st.set_page_config(page_title="Parking ALPR", layout="wide")


def load_css():
    # plik: src/ui.css
    css_path = Path(__file__).parent / "ui.css"
    if css_path.exists():
        st.markdown(
            f"<style>{css_path.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Brak pliku CSS: {css_path}")


load_css()

st.title("System kontroli obsługi parkingu")

service = ParkingService(model_path="models/plate_detector.pt", yolo_conf=0.35)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Wejście: podaj ścieżkę do zdjęcia")
    img_path = st.text_input("Ścieżka do zdjęcia", value="data/images/1.jpg")

    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        do_entry = st.button(" Wjazd ")
    with btn2:
        do_exit = st.button(" Wyjazd ")
    with btn3:
        do_read = st.button(" Odczyt ")

    if do_read:
        res = service.read_plate(img_path)
        st.write(res)

    if do_entry:
        res = service.entry_from_image(img_path)
        if res["ok"]:
            st.success(f"Wjazd OK: {res['plate']} (id={res['event_id']})")
            st.json(res["read"])
        else:
            st.error(res["error"])
            st.json(res.get("read", {}))

    if do_exit:
        res = service.exit_from_image(img_path)
        if res["ok"]:
            ex = res["exit"]
            st.success(
                f"Wyjazd OK: {res['plate']} | fee={ex['fee_pln']} zł | "
                f"{ex['entry_time']} -> {ex['exit_time']}"
            )
            st.json(res["read"])
        else:
            st.error(res["error"])
            st.json(res.get("read", {}))

with col2:
    st.subheader("Stan parkingu")
    if st.button(" Pokaż auta na parkingu "):
        rows = service.open_cars()
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("Historia")
    limit = st.number_input("Limit", min_value=10, max_value=1000, value=50, step=10)
    if st.button(" Pokaż historię "):
        rows = service.history(int(limit))
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("Eksport CSV")
    out_csv = st.text_input("Plik CSV", value="data/parking_export.csv")
    if st.button(" Export CSV "):
        rows = service.export_all(out_csv)
        Path(out_csv).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        st.success(f"Zapisano: {out_csv} ({len(rows)} rekordów)")
