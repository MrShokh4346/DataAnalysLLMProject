# README.md

## Bank Data Analyst Assistant Prototype

Bu loyiha bank tizimi uchun lokal LLM asosidagi Data Analyst Assistant prototipidir. Foydalanuvchi tabiiy til (Uzbek) so'rov yuborsa, SQL generatsiya qilinadi, bajariladi va natija Excel faylga eksport qilinadi (grafiklar bilan).

### O'rnatish

1. **Docker orqali:**
   - Dockerfile va boshqa fayllarni papkaga joylashtiring.
   - `docker build -t bank-analyst .`
   - `docker run -p 8501:8501 bank-analyst`
   - Brauzerda `http://localhost:8501` ga o'ting.

2. **Lokal o'rnatish:**
   - Python 3.10+ o'rnating.
   - Ollama o'rnating: https://ollama.com va `ollama pull llama3` bajaring.
   - `pip install -r requirements.txt`
   - `python bank_analyst_assistant.py` - birinchi ishga tushirishda DB generatsiya qilinadi.

### Ishlatish

- Web UI: Brauzerda ochilgan sahifada Uzbek tilida so'rov kiriting, masalan:  
  "2024 yil iyun oyida Toshkent viloyati bo'yicha jami tranzaksiyalar summasini ko'rsat"
- Natija: SQL ko'rsatiladi, jadval, va yuklab olish uchun Excel fayl (bar chart bilan).

### Demo

1. So'rov: "2024 yil iyun oyida Toshkent viloyati bo‘yicha jami tranzaksiyalar summasini ko‘rsat"
2. Generatsiya SQL: `SELECT SUM(amount) FROM transactions t JOIN accounts a ON t.account_id = a.id JOIN clients c ON a.client_id = c.id WHERE strftime('%Y-%m', t.date) = '2024-06' AND c.region = 'Toshkent viloyati';`
3. Natija: Jadval va Excel fayl (jami summa bilan bar chart).

### Texnik tafsilotlar

- **DB**: SQLite, 100K clients, 200K accounts, 1M transactions (mock data).
- **LLM**: Llama3 (ollama orqali lokal).
- **SQL**: pd.read_sql_query.
- **Excel**: xlsxwriter bilan bar/pie chart.
- **UI**: Streamlit (web).
- **Bonus**: Docker container.

### Baholash

- SQL: LLM prompt orqali to'g'ri generatsiya (schemaga asoslangan).
- Kod: Modulli, toza.
- Excel: Grafiklar qo'shilgan.
- Lokal: Ollama + Docker tayyor.
- Qo'shimcha: Web UI.

Muammolar bo'lsa, loglarni tekshiring.