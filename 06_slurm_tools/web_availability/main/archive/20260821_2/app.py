"""
エントリポイント。ファイル名は ASCII のままにして
(streamlit run 時に日本語を打たずに済むように)、
st.Page(title=...) でサイドバーの表示名だけ日本語にしている。

  streamlit run app.py
"""
import streamlit as st

pg = st.navigation(
    [
        st.Page("views/home.py", title="稼働率", icon="📊", default=True),
        st.Page("views/monthly_yearly.py", title="月次・年間比較", icon="📈"),
    ]
)
pg.run()
