import pandas as pd
import sqlite3
import os
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database(excel_files, db_path='publications.db'):
    """
    Convert Excel files to a SQLite database with a 'publications' table.
    
    Args:
        excel_files (list): List of paths to Excel files.
        db_path (str): Path to output SQLite database.
    """
    try:
        # Initialize database
        if os.path.exists(db_path):
            os.remove(db_path)
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA encoding = 'UTF-8'")
        cursor = conn.cursor()
        
        # Create table with renamed columns
        cursor.execute('''
            CREATE TABLE publications (
                "Authors" TEXT,
                "Title" TEXT,
                "Keywords" TEXT,
                "Abstract" TEXT,
                "Citations" INTEGER,
                "Year" TEXT,
                "DOI" TEXT,
                "WOS_ID" TEXT,
                "Link" TEXT
            )
        ''')
        
        # Read and combine Excel files
        dfs = []
        input_columns = [
            'Authors', 'Article Title', 'Author Keywords', 'Keywords Plus',
            'Abstract', 'Times Cited, All Databases', 'Publication Year', 'DOI', 'UT (Unique WOS ID)'
        ]
        output_columns = [
            'Authors', 'Title', 'Keywords', 'Abstract', 'Citations', 'Year', 'DOI', 'WOS_ID', 'Link'
        ]
        
        for file in excel_files:
            logger.info(f"Reading Excel file: {file}")
            df = pd.read_excel(file, dtype=str)
            # Standardize column names
            df.columns = [col.strip() for col in df.columns]
            # Check if required columns exist
            missing_cols = [col for col in input_columns if col not in df.columns]
            if missing_cols:
                logger.warning(f"Missing columns in {file}: {missing_cols}")
            # Select input columns, fill missing with NaN
            df = df.reindex(columns=input_columns).fillna('N/A')
            # Combine Author Keywords and Keywords Plus
            df['Keywords'] = df.apply(
                lambda x: '; '.join(filter(lambda y: y != 'N/A', [x['Author Keywords'], x['Keywords Plus']])),
                axis=1
            )
            # Rename columns
            df = df.rename({
                'Article Title': 'Title',
                'Times Cited, All Databases': 'Citations',
                'Publication Year': 'Year',
                'UT (Unique WOS ID)': 'WOS_ID'
            }, axis=1)
            # Compute Link
            df['Link'] = df['WOS_ID'].apply(
                lambda x: f"https://www.webofscience.com/wos/woscc/full-record/{x}" if x != 'N/A' else 'N/A'
            )
            # Select output columns
            df = df[output_columns]
            dfs.append(df)
        
        # Combine dataframes
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined {len(combined_df)} records from {len(dfs)} files")
        
        # Clean data
        combined_df = combined_df.fillna('N/A')
        combined_df['Citations'] = pd.to_numeric(
            combined_df['Citations'], errors='coerce'
        ).fillna(0).astype(int)
        
        # Insert into database
        combined_df.to_sql('publications', conn, if_exists='append', index=False)
        conn.commit()
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM publications")
        count = cursor.fetchone()[0]
        logger.info(f"Inserted {count} records into 'publications' table")
        
        # Verify fungi search
        cursor.execute("SELECT COUNT(*) FROM publications WHERE Title LIKE '%fungi%'")
        fungi_count = cursor.fetchone()[0]
        logger.info(f"Found {fungi_count} records with 'fungi' in Title")
        
        conn.close()
        return True, f"Database created with {count} records"
    
    except Exception as e:
        logger.error(f"Failed to create database: {str(e)}")
        return False, f"Failed to create database: {str(e)}"

if __name__ == "__main__":
    # Log current directory
    current_dir = os.getcwd()
    logger.info(f"Current working directory: {current_dir}")
    
    # Find all Excel files (case-insensitive)
    excel_files = (
        glob.glob("*.xlsx") + 
        glob.glob("*.XLSX") + 
        glob.glob("*.xls") + 
        glob.glob("*.XLS")
    )
    logger.info(f"Found Excel files: {excel_files}")
    
    if not excel_files:
        logger.error("No Excel files found in the current directory")
        print("Error: No Excel files found in the current directory")
        exit(1)
    
    success, message = create_database(excel_files)
    print(message)