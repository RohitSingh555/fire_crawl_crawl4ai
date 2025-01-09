import pandas as pd
from sqlalchemy.orm import Session
from app.models import Website
from app.database import engine, get_db, Base

Base.metadata.create_all(bind=engine)

def insert_websites_from_excel(file_path: str, db: Session):
    try:
        df = pd.read_excel(file_path, sheet_name=2, engine="openpyxl")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print(f"Columns in the third sheet of the Excel file: {df.columns.tolist()}")

    expected_columns = ['Sr. No.', 'State', 'City', 'Town', 'Links']  
    missing_columns = [col for col in expected_columns if col not in df.columns]
    if missing_columns:
        print(f"Error: The following columns are missing from the Excel file: {', '.join(missing_columns)}")
        return

    for index, row in df.iterrows():
        try:
            print(f"Processing row {index + 1}: {row}")
            
            website = Website(
                id=int(row['Sr. No.']) if not pd.isna(row['Sr. No.']) else None, 
                state=row['State'] if not pd.isna(row['State']) else None,
                city=row['City'] if not pd.isna(row['City']) else None,
                town=row['Town'] if not pd.isna(row['Town']) else None,
                news_link=row['Links'] if not pd.isna(row['Links']) else None 
            )
            db.add(website)
        except ValueError as ve:
            print(f"Skipping row {index + 1} due to data error: {ve}")
        except Exception as e:
            print(f"Unexpected error while processing row {index + 1}: {e}")

    try:
        db.commit()
        print("Websites have been successfully added to the database!")
    except Exception as e:
        print(f"Error committing to the database: {e}")

if __name__ == "__main__":
    file_path = "attachments/Continental Adjusters - NEWS Portals.xlsx"
    
    db = next(get_db())
    insert_websites_from_excel(file_path, db)
