# GUI

Streamlit web interface for PintMe. Single page with two search modes: text description and image upload. Results are displayed as a 3-column image grid with captions on demand.

## Run

```bash
pip install -r requirements.txt

streamlit run app.py
# or with a custom search API URL:
SEARCH_API=http://localhost:8200 streamlit run app.py
```

Opens at `http://localhost:8501` by default.

## Dependencies

- Search API running on `http://localhost:8200`
- Images are served by the search API (`GET /image/{hash}`)
