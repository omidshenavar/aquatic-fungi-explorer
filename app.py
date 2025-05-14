import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime
import base64
import io
import logging
import contextlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# App configuration
APP_NAME = "Aquatic Fungi Publication Browser"
VERSION = "1.0"
AUTHOR = "Omid Shenavar"
AUTHOR_WEBSITE = "https://omidshenavar.github.io"

# Set page configuration
st.set_page_config(
    page_title=APP_NAME,
    page_icon="app.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark theme colors
THEME = {
    "primary": "#8ECAE6",
    "secondary": "#219EBC",
    "accent": "#FFB703",
    "background": "#121212",
    "surface": "#252525",
    "text": "#E0E0E0",
    "secondary_text": "#B0B0B0"
}

# CSS styling
st.markdown(f"""
<style>
    .stApp {{
        background-color: {THEME['background']};
        color: {THEME['text']};
    }}
    h1, h2, h3 {{
        color: {THEME['primary']};
        font-weight: 600;
    }}
    .card {{
        background-color: {THEME['surface']};
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
    }}
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }}
    .metric-card {{
        background-color: {THEME['surface']};
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.05);
    }}
    .metric-value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {THEME['primary']};
    }}
    .metric-label {{
        font-size: 0.8rem;
        color: {THEME['secondary_text']};
        text-transform: uppercase;
    }}
    .stButton>button {{
        background-color: {THEME['primary']};
        color: {THEME['background']};
        border-radius: 4px;
        padding: 0.5rem 1rem;
        border: none;
    }}
    .stButton>button:hover {{
        background-color: {THEME['accent']};
    }}
    .download-button {{
        display: inline-block;
        padding: 0.5rem 1rem;
        background-color: {THEME['primary']};
        color: {THEME['background']} !important;
        border-radius: 4px;
        text-decoration: none !important;
        margin: 0.5rem 0;
    }}
    .download-button:hover {{
        background-color: {THEME['accent']};
    }}
    .footer {{
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(255,255,255,0.1);
        text-align: center;
        color: {THEME['secondary_text']};
        font-size: 0.9rem;
    }}
    .social-icons a {{
        color: {THEME['secondary_text']};
        margin: 0 0.5rem;
        font-size: 1.3rem;
        text-decoration: none;
    }}
    .social-icons a:hover {{
        color: {THEME['primary']};
    }}
    .publication-row:hover {{
        background-color: rgba(255, 255, 255, 0.05);
        cursor: pointer;
    }}
    .about-section {{
        background-color: rgba(142, 202, 230, 0.1);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1.5rem;
    }}
</style>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/academicons@1.9.2/css/academicons.min.css">
""", unsafe_allow_html=True)

# Database operations
def get_db_path():
    """Get the database path relative to the script directory"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'publications.db')

@contextlib.contextmanager
def get_connection():
    """Thread-safe database connection context manager"""
    connection = None
    try:
        connection = sqlite3.connect(get_db_path())
        connection.execute("PRAGMA encoding = 'UTF-8'")
        yield connection
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        logger.error(f"Database connection failed: {str(e)}")
        raise
    finally:
        if connection:
            connection.close()

def setup_database_indexes():
    """Create necessary indexes if they don't exist"""
    try:
        with get_connection() as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_title ON publications(Title)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON publications(Year)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_keywords ON publications(Keywords)")
            conn.commit()
    except Exception as e:
        logger.error(f"Failed to create database indexes: {str(e)}")

def validate_db_file(db_file):
    """Validate that the database has the expected structure"""
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='publications'")
            if not cursor.fetchone():
                return False, "No 'publications' table found."
            
            cursor.execute("PRAGMA table_info(publications)")
            columns = [info[1] for info in cursor.fetchall()]
            required_columns = ['Authors', 'Title', 'Keywords', 'Abstract', 'Citations', 'Year', 'DOI', 'Link']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                return False, f"Missing columns: {', '.join(missing_columns)}."
            return True, ""
    except Exception as e:
        return False, f"Invalid SQLite file: {str(e)}"

@st.cache_data(ttl=3600)
def load_data():
    """Load the entire dataset into a DataFrame"""
    logger.info(f"Loading data from {get_db_path()}")
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM publications", conn)

def fetch_paginated_data(search_term="", year_filter="All", min_citations=0, page=1, page_size=10):
    """Fetch paginated data based on filters"""
    offset = (page - 1) * page_size
    query = "SELECT * FROM publications WHERE 1=1"
    params = []
    
    if search_term:
        query += " AND (LOWER(Title) LIKE ? OR LOWER(Authors) LIKE ? OR LOWER(Keywords) LIKE ? OR LOWER(Abstract) LIKE ?)"
        search_term = f"%{search_term.lower()}%"
        params.extend([search_term] * 4)
    
    if year_filter != "All":
        query += " AND Year = ?"
        params.append(year_filter)
    
    if min_citations > 0:
        query += " AND Citations >= ?"
        params.append(min_citations)
    
    count_query = "SELECT COUNT(*) FROM publications WHERE 1=1" + query.split("WHERE 1=1")[1]
    
    query += f" LIMIT ? OFFSET ?"
    params_with_pagination = params.copy()
    params_with_pagination.extend([page_size, offset])
    
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params_with_pagination)
        total_count = pd.read_sql_query(count_query, conn, params=params).iloc[0, 0]
    
    return df, total_count

def export_data(df, format_type):
    """Export data in various formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"aquatic_fungi_publications_{timestamp}"
    
    if format_type == "CSV":
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv" class="download-button">Download CSV</a>'
        logger.info(f"Exported {len(df)} records to CSV")
        return href
    
    elif format_type == "Excel":
        buffer = io.BytesIO()
        df.to_excel(buffer, index=False, engine='openpyxl')
        b64 = base64.b64encode(buffer.getvalue()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx" class="download-button">Download Excel</a>'
        logger.info(f"Exported {len(df)} records to Excel")
        return href
    
    elif format_type == "BibTeX":
        bibtex_entries = []
        for _, row in df.iterrows():
            authors = row['Authors'].split(';') if pd.notna(row['Authors']) else ['']
            last_name = authors[0].strip().split()[-1] if authors[0].strip() else 'unknown'
            bibtex_key = f"{last_name}{row['Year']}"
            authors_bibtex = " and ".join([a.strip() for a in authors if a.strip()])
            entry = f"""@article{{{bibtex_key},
  title = {{{row['Title']}}},
  author = {{{authors_bibtex}}},
  year = {{{row['Year']}}},
  doi = {{{row['DOI'] if pd.notna(row['DOI']) else ''}}},
  abstract = {{{row['Abstract'] if pd.notna(row['Abstract']) else ''}}},
}}
"""
            bibtex_entries.append(entry)
        bibtex_content = "\n".join(bibtex_entries)
        b64 = base64.b64encode(bibtex_content.encode()).decode()
        href = f'<a href="data:application/x-bibtex;base64,{b64}" download="{filename}.bib" class="download-button">Download BibTeX</a>'
        logger.info(f"Exported {len(df)} records to BibTeX")
        return href
    
    return ""

# Initialize database and validate it
db_path = get_db_path()
if not os.path.exists(db_path):
    st.error("No database found. Please ensure 'publications.db' is in the same directory.")
    st.stop()

is_valid, error_msg = validate_db_file(db_path)
if not is_valid:
    st.error(f"Invalid database: {error_msg}")
    st.stop()

# Set up database indexes
setup_database_indexes()

# Initialize session state for filters
if 'filters' not in st.session_state:
    st.session_state.filters = {
        'search_term': '',
        'year_filter': 'All',
        'min_citations': 0,
        'page': 1,
        'page_size': 10,
        'selected_row': None
    }

# Initialize state for selected publication
if 'selected_publication' not in st.session_state:
    st.session_state.selected_publication = None

# Header
col1, col2 = st.columns([1, 4])
with col1:
    st.image("app.png", width=60)
with col2:
    st.markdown(f"""
    <h1 style="margin-top: 0;">{APP_NAME}</h1>
    <p style="color: {THEME['secondary_text']};">A database explorer tool for "<b>Challenges and Opportunities in Defining Aquatic Fungi</b>" by Masigol et al. (2025)</p>
    """, unsafe_allow_html=True)
st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <h2 style="font-size: 1.5rem;">🔍 Filters</h2>
    """, unsafe_allow_html=True)
    
    # Load unique years from the database
    with get_connection() as conn:
        years_df = pd.read_sql_query("SELECT DISTINCT Year FROM publications WHERE Year IS NOT NULL ORDER BY Year DESC", conn)
        years = ['All'] + years_df['Year'].astype(str).tolist()
    
    # Define search term input with on_change callback
    def update_filters():
        st.session_state.filters.update({
            'search_term': st.session_state.search_term,
            'year_filter': st.session_state.year_filter,
            'min_citations': st.session_state.min_citations,
            'page': 1,
            'page_size': st.session_state.page_size,
            'selected_row': None
        })
    
    st.text_input(
        "Search", 
        placeholder="Title, authors, keywords...",
        key="search_term",
        on_change=update_filters
    )
    
    st.selectbox(
        "Publication Year", 
        years, 
        key="year_filter",
        on_change=update_filters
    )
    
    # Get max citations safely
    with get_connection() as conn:
        max_cit_df = pd.read_sql_query("SELECT MAX(Citations) FROM publications", conn)
        max_cit = int(max_cit_df.iloc[0, 0] if not pd.isna(max_cit_df.iloc[0, 0]) else 0)
    
    st.slider(
        "Minimum Citations", 
        0, 
        min(500, max_cit), 
        0, 
        key="min_citations",
        on_change=update_filters
    )
    
    st.selectbox(
        "Items per page", 
        [10, 20, 50], 
        index=0,
        key="page_size",
        on_change=update_filters
    )
    
    # Apply Filters button as an alternative (now optional)
    if st.button("Apply Filters", use_container_width=True):
        update_filters()
    
    # Improved About section in sidebar
    st.markdown("---")
    st.markdown("""
    <div class="about-section">
        <h3 style="margin-top: 0;">About</h3>
        <p><strong>Aquatic Fungi Publication Browser</strong> (v1.0) is a specialized tool for exploring publications studied in the following manuscript: <a href="#" style="color: #8ECAE6;">Challenges and Opportunities in Defining Aquatic Fungi</a> (Masigol et al., 2025).</p>
        <p>Created by <a href="https://omidshenavar.github.io" target="_blank" style="color: #8ECAE6;">Omid Shenavar</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Social icons in sidebar
    st.markdown("""
    <div class="social-icons" style="text-align: center; margin-top: 0.5rem;">
        <a href="https://orcid.org/0000-0003-2297-8352" target="_blank" title="ORCID"><i class="ai ai-orcid"></i></a>
        <a href="https://www.researchgate.net/profile/Omid-Shenavar" target="_blank" title="ResearchGate"><i class="ai ai-researchgate"></i></a>
        <a href="https://scholar.google.com/citations?user=Uvse3ykAAAAJ&hl=en&oi=ao" target="_blank" title="Google Scholar"><i class="ai ai-google-scholar"></i></a>
        <a href="https://ir.linkedin.com/in/omid-shenavar-46702496" target="_blank" title="LinkedIn"><i class="fab fa-linkedin-in"></i></a>
        <a href="https://github.com/omidshenavar" target="_blank" title="GitHub"><i class="fab fa-github"></i></a>
    </div>
    """, unsafe_allow_html=True)

# Tabs
tabs = st.tabs(["Publications", "Manuscript Info"])

with tabs[0]:
    # Fetch paginated data
    df, total_count = fetch_paginated_data(
        st.session_state.filters['search_term'],
        st.session_state.filters['year_filter'],
        st.session_state.filters['min_citations'],
        st.session_state.filters['page'],
        st.session_state.filters['page_size']
    )
    
    # Calculate metrics
    avg_citations = df['Citations'].fillna(0).mean() if not df.empty else 0
    unique_years = df['Year'].nunique() if not df.empty else 0
    
    # Metrics
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-value">{total_count}</div>
            <div class="metric-label">Publications</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{avg_citations:.1f}</div>
            <div class="metric-label">Avg. Citations</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{unique_years}</div>
            <div class="metric-label">Years</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Paginated table
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    if not df.empty:
        # Show table with interactive rows
        st.markdown("""
        <p style="font-size: 0.9rem; color: #B0B0B0;">Click on any publication to view details</p>
        """, unsafe_allow_html=True)
        
        # Display table with clickable rows
        st.dataframe(
            df[['Title', 'Authors', 'Year', 'Citations', 'DOI']].style.format({
                'Citations': '{:.0f}',
                'DOI': lambda x: x if pd.notna(x) and x != 'N/A' else ''
            }),
            use_container_width=True,
            height=300,
            hide_index=False,
            column_config={
                "index": st.column_config.Column(
                    "ID",
                    width="small",
                )
            }
        )
        
        # Alternative selection method using selectbox but styled to be more compact
        if len(df) > 0:
            # Create a function to format publication titles
            def format_publication(idx):
                row = df.loc[idx]
                year = row['Year'] if pd.notna(row['Year']) else 'N/A'
                title = row['Title'] if pd.notna(row['Title']) else 'Untitled'
                if len(title) > 60:
                    title = f"{title[:60]}..."
                return f"{year} - {title}"
            
            st.markdown("<div style='margin-top:10px;'><small>Select a publication to view details:</small></div>", unsafe_allow_html=True)
            selected_index = st.selectbox(
                "Select Publication",
                options=df.index,
                format_func=format_publication,
                key="publication_select",
                label_visibility="hidden"
            )
            
            st.session_state.selected_publication = df.loc[selected_index]
        
        # Pagination controls
        total_pages = max(1, (total_count + st.session_state.filters['page_size'] - 1) // st.session_state.filters['page_size'])
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.number_input(
                "Page",
                min_value=1,
                max_value=total_pages,
                value=st.session_state.filters['page'],
                step=1,
                key="page_input"
            )
            if page != st.session_state.filters['page']:
                st.session_state.filters['page'] = page
                st.session_state.selected_row = None
        
        # Publication details
        if st.session_state.selected_publication is not None:
            st.markdown("<h3>Publication Details</h3>", unsafe_allow_html=True)
            row = st.session_state.selected_publication
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"""
                <h3>{row['Title'] if pd.notna(row['Title']) else 'Untitled'}</h3>
                <p><strong>Authors:</strong> {row['Authors'] if pd.notna(row['Authors']) else 'Not available'}</p>
                <p><strong>Abstract:</strong> {row['Abstract'] if pd.notna(row['Abstract']) else 'Not available'}</p>
                <p><strong>Keywords:</strong> {row['Keywords'] if pd.notna(row['Keywords']) else 'Not available'}</p>
                """, unsafe_allow_html=True)
            
            with col2:
                # Fix to properly display DOI link and add WOS link
                doi_display = "Not available"
                if pd.notna(row['DOI']) and row['DOI'] != 'N/A':
                    doi_display = f'<a href="https://doi.org/{row["DOI"]}" target="_blank">{row["DOI"]}</a>'
                
                wos_display = "Not available"
                if pd.notna(row.get('Link')) and row['Link'] != 'N/A':
                    wos_display = f'<a href="{row["Link"]}" target="_blank">Visit Web of Science</a>'
                
                st.markdown(f"""
                <div style="background-color: rgba(142, 202, 230, 0.1); padding: 1rem; border-radius: 8px;">
                    <p><strong>Year:</strong> {row['Year'] if pd.notna(row['Year']) else 'N/A'}</p>
                    <p><strong>Citations:</strong> {int(row['Citations']) if pd.notna(row['Citations']) else 'N/A'}</p>
                    <p><strong>DOI:</strong> {doi_display}</p>
                    <p><strong>WOS link:</strong> {wos_display}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No publications found. Try adjusting your filters.")
    
    # Export section
    st.markdown("<h3>Export Data</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        export_format = st.selectbox("Format", ["CSV", "Excel", "BibTeX"])
    with col2:
        if st.button("Export", use_container_width=True) and not df.empty:
            with st.spinner(f"Preparing {export_format} export..."):
                href = export_data(df, export_format)
                st.markdown(href, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

with tabs[1]:
    st.markdown(f"""
    <h2>Manuscript Information</h2>
    """, unsafe_allow_html=True)
    
    # Improved manuscript info display
    st.markdown(f"""
    <div class="card" style="background: linear-gradient(to right, {THEME["surface"]}, rgba(33, 158, 188, 0.1));">
        <h3 style="color: {THEME["primary"]}; margin-top: 0; font-size: 1.5rem;">Challenges and Opportunities in Defining Aquatic Fungi</h3>
        <div style="display: flex; gap: 2rem; flex-wrap: wrap;">
            <div style="flex: 2; min-width: 300px;">
                <p><strong>Authors:</strong> Hossein Masigol et al.</p>
                <p><strong>Status:</strong> In preparation</p>
                <p><strong>Expected Publication:</strong> 2025</p>
                <p><strong>Abstract:</strong> This manuscript provides a comprehensive review and analysis of current research on aquatic fungi, highlighting taxonomic challenges, methodological approaches, and future research directions. The database accessible through this application supports the findings and analyses presented in the manuscript.</p>
            </div>
            <div style="flex: 1; min-width: 200px;">
                <div style="border-left: 3px solid {THEME["accent"]}; padding-left: 1rem;">
                    <h4 style="color: {THEME["accent"]}; margin-top: 0;">Acknowledgements</h4>
                    <p style="font-size: 0.9rem;"><strong>Alice Retter</strong><br>Initial database and literature collection</p>
                    <p style="font-size: 0.9rem;"><strong>Hossein Masigol</strong><br>Research coordination and manuscript preparation</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Citation information
    st.markdown("""
    <h3>How to Cite</h3>

    <p><strong>Manuscript:</strong></p>
    <div style="background-color: rgba(255,255,255,0.05); padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 0.9rem; margin-bottom: 1rem;">
        Masigol, H., et al. (2025). <i>Challenges and Opportunities in Defining Aquatic Fungi.</i> [Journal pending]. DOI: TBA
    </div>

    <p><strong>Database & Application:</strong></p>
    <div style="background-color: rgba(255,255,255,0.05); padding: 1rem; border-radius: 4px; font-family: monospace; font-size: 0.9rem;">
        Shenavar, O. (2025). <i>Aquatic Fungi Publication Explorer</i> [WebApp]. Zenodo. DOI: <a href='https://doi.org/10.5281/zenodo.15406080' target='_blank'>10.5281/zenodo.15406080</a>
    </div>
    """, unsafe_allow_html=True)



# Footer - simplified since About is now in sidebar
st.markdown(f"""
<div class="footer">
    <p>{APP_NAME} v{VERSION} | © {datetime.now().year} | MIT License</p>
</div>
""", unsafe_allow_html=True)