import sys, spacy, streamlit, pandas
print("python:", sys.executable)
print("spacy:", spacy.__version__)
print("streamlit:", streamlit.__version__)
print("pandas:", pandas.__version__)
import en_core_web_sm
en_core_web_sm.load()
print("model OK")
