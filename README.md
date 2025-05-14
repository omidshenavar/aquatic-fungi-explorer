# 🌊 Aquatic Fungi Publication Explorer

Welcome to the **Aquatic Fungi Publication Explorer** — a lightweight, user-friendly web application that helps readers access the database and literature studied in the Masigol et al. manuscript (yet to be published). This is a specialized tool created specifically to support the findings and analysis presented in that publication.

This companion application allows researchers to explore the dataset referenced in the paper and gain deeper insights into the aquatic fungi literature compilation that forms the basis of the study.

🔗 **Live App**: [https://aquatic-fungi-explorer.streamlit.app/](https://aquatic-fungi-explorer.streamlit.app/)

**Note for Iranian Researchers**: Due to regional restrictions, researchers from Iran may need to use a VPN to access the live version. Alternatively, you can run the application locally by following the instructions below.

---

## 📌 Purpose

This web application provides a searchable interface to the specific database of aquatic fungal research publications compiled for the Masigol et al. (2025) study. It allows:

- Filtering by year, author, keyword, and more  
- Downloading filtered results as Excel or CSV  
- Logging your search parameters (anonymously) for reproducibility  
- Helping fellow researchers verify and build upon the findings presented in the manuscript

⚠️ **Important Note:**  
This application and its underlying dataset are intended as supplementary materials for the *Masigol et al. (2025)* manuscript. Please cite both the application and the original manuscript in any work that builds upon or references this database.

---

## 🚀 How to Run Locally

You can run this app on your local machine, which is especially useful for users in regions with access restrictions.

### For Linux Users:

### 1. Clone the Repository
```bash
git clone https://github.com/omidshenavar/aquatic-fungi-explorer.git
cd aquatic-fungi-explorer
```

### 2. Set Up a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Launch the App
```bash
streamlit run app.py
```

### For Windows Users:

### 1. Clone the Repository
```bash
git clone https://github.com/omidshenavar/aquatic-fungi-explorer.git
cd aquatic-fungi-explorer
```

### 2. Set Up a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Launch the App
```bash
streamlit run app.py
```

## 📦 Requirements

The app uses the following Python packages:
```
streamlit>=1.30.0
pandas>=2.0.0
openpyxl>=3.1.0
```

And the following standard Python libraries:
- sqlite3
- os
- datetime
- base64
- io
- logging
- contextlib

## 📄 License

This project is licensed under the BSD 3-Clause License with Citation Requirement.
See the [LICENSE](./LICENSE) file for full terms and conditions, including mandatory citation instructions.


Copyright (c) 2025 Omid Shenavar
All rights reserved.

## 📚 Citation

If you use or reference this tool in any academic or professional context, please cite it as follows:

Shenavar, O. (2025). Aquatic Fungi Publication Explorer [WebApp]. Zenodo. https://doi.org/10.5281/zenodo.15406080

Masigol, H., et al. (2025). *Challenges and Opportunities in Defining Aquatic Fungi.* [Journal pending]. DOI: TBA

## 🙋 Feedback & Contribution

Contributions are welcome! Feel free to fork this repository, open issues, or submit pull requests.

Thank you for exploring aquatic fungal biodiversity with us 🌱